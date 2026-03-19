import re
from datetime import date
from decimal import Decimal
import pdfplumber
from .base import BaseParser, Transaction

UNICARD_PAGE_ID = "2c640bb7-4433-80c0-8e80-fefd474eee46"

class ESunParser(BaseParser):
    bank_name = "玉山銀行"

    _HEADER_YEAR = re.compile(r"(\d{3})年(\d{2})月")
    _TXN = re.compile(
        r"^(\d{2}/\d{2})\s+(\d{2}/\d{2})\s+(.+?)\s+TWD\s+([\d,]+)\s*$",
        re.MULTILINE,
    )
    _SKIP = re.compile(r"感謝您|本期合計|本期應繳|最低應繳")

    def parse(self, pdf: pdfplumber.PDF) -> list[Transaction]:
        full_text = "\n".join(page.extract_text() or "" for page in pdf.pages)
        year = self._get_year(full_text)
        bill_month = self._get_bill_month(full_text)
        results = []

        for m in self._TXN.finditer(full_text):
            spend_date_str, _, desc, amount_str = m.groups()
            desc = desc.strip()

            if self._SKIP.search(desc):
                continue

            month, day = (int(x) for x in spend_date_str.split("/"))
            if month > bill_month + 1:
                txn_year = year - 1
            elif bill_month == 12 and month == 1:
                txn_year = year + 1
            else:
                txn_year = year
            results.append(Transaction(
                date=date(txn_year, month, day),
                description=desc,
                amount=Decimal(amount_str.replace(",", "")),
                bank=self.bank_name,
                payment_page_id=UNICARD_PAGE_ID,
            ))

        return results

    def _get_year(self, text: str) -> int:
        m = self._HEADER_YEAR.search(text)
        return int(m.group(1)) + 1911 if m else date.today().year

    def _get_bill_month(self, text: str) -> int:
        m = self._HEADER_YEAR.search(text)
        return int(m.group(2)) if m else date.today().month