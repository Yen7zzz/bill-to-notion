import imaplib
import email
from dataclasses import dataclass
from typing import Iterator

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
        self._conn.select("INBOX")
        return self

    def __exit__(self, *args):
        if self._conn:
            self._conn.close()
            self._conn.logout()

    def fetch_unseen_pdfs(self, sender_email: str) -> Iterator[MailAttachment]:
        _, uids = self._conn.uid("search", None, f'(UNSEEN FROM "{sender_email}")')
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