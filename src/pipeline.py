import os
import logging
from .mail import GmailClient
from .pdf_unlock import unlock_pdf
from .parsers import SENDER_MAP, get_parser
from .notion_writer import NotionWriter

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

def run():
    print("Pipeline started", flush=True)
    log.info("Pipeline started")
    notion = NotionWriter()

    with GmailClient(os.environ["EMAIL_USER"], os.environ["EMAIL_PASS"]) as gmail:
        for sender, (parser_cls, subject_filter) in SENDER_MAP.items():
            parser = parser_cls()

            for attachment in gmail.fetch_unseen_pdfs(sender, subject_filter=subject_filter):
                log.info(f"[{sender}] Found: {attachment.filename}")
                try:
                    pdf = unlock_pdf(attachment.data, os.environ["ID_NUMBER"])
                    txns = parser.parse(pdf)
                    log.info(f"Parsed {len(txns)} transactions")

                    ok, fail = notion.write_batch(txns)
                    log.info(f"Notion: {ok} ok / {fail} failed")

                    if fail == 0:
                        gmail.mark_seen(attachment.uid)
                    else:
                        log.warning("Partial write failure — keeping email unseen for retry")

                except Exception as e:
                    log.error(f"Pipeline failed for {attachment.filename}: {e}", exc_info=True)

if __name__ == "__main__":
    run()