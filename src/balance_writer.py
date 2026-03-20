import os
from notion_client import Client
from .parsers.balance_base import BalanceEntry


class NotionBalanceWriter:
    def __init__(self):
        self._client = Client(auth=os.environ["NOTION_TOKEN"])
        self._db_id = os.environ["NOTION_BALANCE_DB_ID"]

    def write(self, entry: BalanceEntry) -> None:
        self._client.pages.create(
            parent={"database_id": self._db_id},
            properties={
                "名稱":     {"title": [{"text": {"content": entry.account_name}}]},
                "帳單月份": {"date":  {"start": entry.date.isoformat()}},
                "餘額":     {"number": float(entry.amount)},
                "幣別":     {"select": {"name": entry.currency}},
            },
        )

    def write_batch(self, entries: list[BalanceEntry]) -> tuple[int, int]:
        ok = fail = 0
        for entry in entries:
            try:
                self.write(entry)
                ok += 1
            except Exception as e:
                print(f"[Balance] Write failed: {entry} — {e}")
                fail += 1
        return ok, fail