import re
from datetime import date
from decimal import Decimal
import pdfplumber
from .base import BaseParser, Transaction

CARD_MAP = {
    "8409": "2c640bb7-4433-801c-a31e-fe0c3d251f46",  # sport
    "3205": "2c640bb7-4433-8076-b868-e027d89f1849",  # 現金回饋
}

class SinoPacParser(BaseParser):
    bank_name = "永豐銀行"

    _HEADER_YEAR = re.compile(r"(\d{4})年(\d{1,2})月")
    _TXN = re.compile(
        r"^(\d{2}/\d{2})\s+\d{2}/\d{2}\s+"
        r"(\d{4})\s+"
        r"(?:A-\s*|MA-\s*|SPORT\s*)?"
        r"(.+?)\s+"
        r"(-?[\d,]+)\s*$",
        re.MULTILINE,
    )
    _SKIP = re.compile(
        r"自扣已入帳"
        r"|豐點\s*-\s*折抵金"
        r"|折抵回饋金"
        r"|ＳＰＯＲＴ卡.*獎勵"
        r"|ＳＰＯＲＴ卡.*回饋"
        r"|ＳＰＯＲＴ卡.*通路"
    )

    def parse(self, pdf: pdfplumber.PDF) -> list[Transaction]:
        full_text = "\n".join(page.extract_text() or "" for page in pdf.pages)
        year = self._get_year(full_text)
        bill_month = self._get_bill_month(full_text)
        results = []

        for m in self._TXN.finditer(full_text):
            spend_date_str, card_last4, desc, amount_str = m.groups()
            desc = desc.strip()
            amount = Decimal(amount_str.replace(",", ""))

            if self._SKIP.search(desc) or amount == 0:
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
                amount=amount,
                bank=self.bank_name,
                payment_page_id=CARD_MAP.get(card_last4, ""),
            ))

        return results

    def _get_year(self, text: str) -> int:
        m = self._HEADER_YEAR.search(text)
        return int(m.group(1)) if m else date.today().year

    def _get_bill_month(self, text: str) -> int:
        m = self._HEADER_YEAR.search(text)
        return int(m.group(2)) if m else date.today().month