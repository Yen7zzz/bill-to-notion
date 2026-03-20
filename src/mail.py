import imaplib
import email
import email.header
import logging
from dataclasses import dataclass
from typing import Iterator

log = logging.getLogger(__name__)

IMAP_HOST = "imap.gmail.com"


def _decode_filename(raw: str | None) -> str | None:
    if raw is None:
        return None
    parts = email.header.decode_header(raw)
    decoded = []
    for part, charset in parts:
        if isinstance(part, bytes):
            decoded.append(part.decode(charset or "utf-8", errors="replace"))
        else:
            decoded.append(part)
    return "".join(decoded)

@dataclass
class MailAttachment:
    uid: bytes
    sender: str
    filename: str
    data: bytes

class GmailClient:
    def __init__(self, user: str, password: str):
        self._user = user
        self._password = password
        self._conn: imaplib.IMAP4_SSL | None = None

    def __enter__(self):
        self._conn = imaplib.IMAP4_SSL(IMAP_HOST)
        self._conn.login(self._user, self._password)
        status, detail = self._conn.select(b'[Gmail]/&UWiQ6JD1TvY-')
        if status != "OK":
            raise RuntimeError(f"IMAP SELECT failed: {detail}")
        return self

    def __exit__(self, *args):
        if self._conn:
            try:
                self._conn.close()
            except Exception:
                pass
            self._conn.logout()

    def fetch_unseen_pdfs(self, sender_email: str, subject_filter: str | None = None) -> Iterator[MailAttachment]:
        criteria = f'(UNSEEN FROM "{sender_email}")'
        if subject_filter:
            criteria = f'(UNSEEN FROM "{sender_email}" SUBJECT "{subject_filter}")'
        _, uids = self._conn.uid("search", None, criteria.encode("utf-8"))
        log.info(f"[{sender_email}] IMAP search returned UIDs: {uids[0]}")
        if not uids[0]:
            return

        for uid in uids[0].split():
            _, data = self._conn.uid("fetch", uid, "(RFC822)")
            msg = email.message_from_bytes(data[0][1])

            log.info(f"[{sender_email}] UID {uid} subject: {msg.get('Subject')}")
            for part in msg.walk():
                ct = part.get_content_type()
                filename = _decode_filename(part.get_filename())
                log.info(f"  part content-type={ct!r} filename={filename!r}")
                if ct == "application/pdf" or (
                    ct == "application/octet-stream"
                    and filename
                    and filename.lower().endswith(".pdf")
                ):
                    yield MailAttachment(
                        uid=uid,
                        sender=sender_email,
                        filename=filename or "statement.pdf",
                        data=part.get_payload(decode=True),
                    )

    def mark_seen(self, uid: bytes) -> None:
        self._conn.uid("store", uid, "+FLAGS", r"(\Seen)")