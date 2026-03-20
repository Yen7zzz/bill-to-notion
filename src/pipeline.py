import os
import logging
from collections import defaultdict
from .mail import GmailClient
from .pdf_unlock import unlock_pdf
from .parsers import DISPATCH, DispatchRule
from .notion_writer import NotionWriter
from .balance_writer import NotionBalanceWriter

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


def run():
    log.info("Pipeline started")
    notion = NotionWriter()

    balance_db = os.environ.get("NOTION_BALANCE_DB_ID")
    balance_writer = NotionBalanceWriter() if balance_db else None
    if not balance_db:
        log.warning("NOTION_BALANCE_DB_ID not set — balance writes disabled")

    # Group rules by (sender, filename_filter) so we fetch each combination once
    groups: dict[tuple[str, str | None], list[DispatchRule]] = defaultdict(list)
    for rule in DISPATCH:
        groups[(rule.sender, rule.filename_contains)].append(rule)

    with GmailClient(os.environ["EMAIL_USER"], os.environ["EMAIL_PASS"]) as gmail:
        for (sender, fn_filter), rules in groups.items():
            for attachment in gmail.fetch_unseen_pdfs(sender, filename_contains=fn_filter):
                log.info(f"[{sender}] Found: {attachment.filename}")
                try:
                    pdf = unlock_pdf(attachment.data, os.environ["ID_NUMBER"])
                    total_ok = total_fail = 0

                    for rule in rules:
                        parser = rule.parser_cls()
                        parsed = parser.parse(pdf)
                        log.info(f"  [{rule.parser_cls.__name__}] Parsed {len(parsed)} entries")

                        if rule.target == "credit_card":
                            ok, fail = notion.write_batch(parsed)
                        elif rule.target == "balance" and balance_writer:
                            ok, fail = balance_writer.write_batch(parsed)
                        else:
                            log.warning(f"  Skipping {rule.target} (writer unavailable)")
                            ok, fail = len(parsed), 0

                        total_ok += ok
                        total_fail += fail

                    log.info(f"  Total: {total_ok} ok / {total_fail} failed")
                    if total_fail == 0:
                        gmail.mark_seen(attachment.uid)
                    else:
                        log.warning("  Partial failure — keeping email unseen for retry")

                except Exception as e:
                    log.error(f"  Pipeline failed for {attachment.filename}: {e}", exc_info=True)


if __name__ == "__main__":
    run()