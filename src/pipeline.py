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

    # Group rules by sender so each email is fetched exactly once per sender
    sender_rules: dict[str, list[DispatchRule]] = defaultdict(list)
    for rule in DISPATCH:
        sender_rules[rule.sender].append(rule)

    with GmailClient(os.environ["EMAIL_USER"], os.environ["EMAIL_PASS"]) as gmail:
        for sender, rules in sender_rules.items():
            # Collect all PDF attachments grouped by email UID
            emails: dict[bytes, list] = defaultdict(list)
            for attachment in gmail.fetch_unseen_pdfs(sender):
                emails[attachment.uid].append(attachment)

            for uid, attachments in emails.items():
                total_ok = total_fail = 0
                for attachment in attachments:
                    log.info(f"[{sender}] Processing: {attachment.filename}")
                    # Find rules whose filename_contains matches this attachment
                    matching = [
                        r for r in rules
                        if r.filename_contains is None
                        or (attachment.filename and r.filename_contains in attachment.filename)
                    ]
                    if not matching:
                        log.info(f"  No matching rules — skipping")
                        continue
                    try:
                        pdf = unlock_pdf(attachment.data, os.environ["ID_NUMBER"])
                        for rule in matching:
                            parsed = rule.parser_cls().parse(pdf)
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
                    except Exception as e:
                        log.error(f"  Pipeline failed for {attachment.filename}: {e}", exc_info=True)
                        total_fail += 1

                log.info(f"  Email UID {uid}: {total_ok} ok / {total_fail} failed")
                if total_fail == 0:
                    gmail.mark_seen(uid)
                else:
                    log.warning("  Partial failure — keeping email unseen for retry")


if __name__ == "__main__":
    run()