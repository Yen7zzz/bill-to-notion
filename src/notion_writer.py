import os
from notion_client import Client
from .parsers.base import Transaction

class NotionWriter:
    def __init__(self):
        self._client = Client(auth=os.environ["NOTION_TOKEN"])
        self._db_id = os.environ["NOTION_DATABASE_ID"]

    def write(self, txn: Transaction) -> None:
        props = {
            "名稱":     {"title": [{"text": {"content": txn.description}}]},
            "花費日期": {"date":  {"start": txn.date.isoformat()}},
            "金額":     {"number": float(txn.amount)},
        }
        if txn.payment_page_id:
            props["支付方式"] = {"relation": [{"id": txn.payment_page_id}]}

        self._client.pages.create(
            parent={"database_id": self._db_id},
            properties=props,
        )

    def write_batch(self, transactions: list[Transaction]) -> tuple[int, int]:
        ok = fail = 0
        for txn in transactions:
            try:
                self.write(txn)
                ok += 1
            except Exception as e:
                print(f"[Notion] Write failed: {txn} — {e}")
                fail += 1
        return ok, fail