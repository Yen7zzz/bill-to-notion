import imaplib
import email
import logging
from dataclasses import dataclass
from typing import Iterator

log = logging.getLogger(__name__)

IMAP_HOST = "imap.gmail.com"

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

        _, folder_list = self._conn.list()
        log.info("Available IMAP folders:")
        for entry in folder_list:
            log.info(f"  {entry}")

        all_mail = self._find_all_mail_folder(folder_list)
        log.info(f"Selecting folder: {all_mail!r}")
        status, detail = self._conn.select(all_mail)
        if status != "OK":
            raise RuntimeError(f"IMAP SELECT failed ({all_mail!r}): {detail}")
        return self

    @staticmethod
    def _find_all_mail_folder(folder_list: list) -> bytes:
        """Return the raw folder name bytes for All Mail from the server's LIST response."""
        for entry in folder_list:
            if isinstance(entry, bytes) and b"\\All" in entry:
                # LIST entry format: (<flags>) "<delimiter>" <name>
                # The name is everything after the last space-delimited token following the delimiter
                parts = entry.split(b'"')
                if len(parts) >= 3:
                    return parts[-1].strip()
                # fallback: last space-separated token
                return entry.rsplit(b" ", 1)[-1].strip()
        raise RuntimeError("Could not find All Mail folder in IMAP LIST response")

    def __exit__(self, *args):
        if self._conn:
            try:
                self._conn.close()
            except Exception:
                pass
            self._conn.logout()

    def fetch_unseen_pdfs(self, sender_email: str) -> Iterator[MailAttachment]:
        _, uids = self._conn.uid("search", None, f'(UNSEEN FROM "{sender_email}")')
        log.info(f"[{sender_email}] IMAP search returned UIDs: {uids[0]}")
        if not uids[0]:
            return

        for uid in uids[0].split():
            _, data = self._conn.uid("fetch", uid, "(RFC822)")
            msg = email.message_from_bytes(data[0][1])

            for part in msg.walk():
                if part.get_content_type() == "application/pdf":
                    yield MailAttachment(
                        uid=uid,
                        sender=sender_email,
                        filename=part.get_filename() or "statement.pdf",
                        data=part.get_payload(decode=True),
                    )

    def mark_seen(self, uid: bytes) -> None:
        self._conn.uid("store", uid, "+FLAGS", r"(\Seen)")