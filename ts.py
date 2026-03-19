import os
from notion_client import Client
from datetime import date
from decimal import Decimal
from src.parsers.base import Transaction
from src.notion_writer import NotionWriter

os.environ["NOTION_TOKEN"] = "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"
os.environ["NOTION_DATABASE_ID"] = "2c640bb744338073b553c65034bc755c"

writer = NotionWriter()
test_txn = Transaction(
    date=date(2026, 1, 19),
    description="測試寫入",
    amount=Decimal("100"),
    payment_page_id="2c640bb7-4433-801c-a31e-fe0c3d251f46",  # sport
)
writer.write(test_txn)
print("Done")