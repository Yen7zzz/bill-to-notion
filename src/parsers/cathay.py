import re
from datetime import date
from decimal import Decimal
import pdfplumber
from .base import BaseParser, Transaction

# TODO: 拿到 Notion page ID 後填入
CARD_MAP = {
    "4102": "2c640bb7-4433-804a-9eb3-f6b618cb4bf0",  # CUBE 卡
}


class CathayParser(BaseParser):
    bank_name = "國泰世華"

    _HEADER_YEAR = re.compile(r"(\d{2,3})年(\d{1,2})月")  # 民國年
    _TXN = re.compile(
        r"^(\d{2}/\d{2})\s+\d{2}/\d{2}\s+"   # 消費日 入帳日
        r"(.+?)\s+"                             # 交易說明
        r"(-?[\d,]+)\s+"                        # 金額
        r"(\d{4})\s+\d{4}\s+"                   # 卡號後四碼 行動卡號後四碼
        r"\w+\s+TWD\s*$",                       # 國家 幣別
        re.MULTILINE,
    )
    _SKIP = re.compile(
        r"上期帳單總額|繳款小計|正卡本期消費|本期應繳總額"
        r"|ＣＵＢＥＡｐｐ轉帳繳款|轉帳繳款|自動扣繳"
    )

    def parse(self, pdf: pdfplumber.PDF) -> list[Transaction]:
        full_text = "\n".join(page.extract_text() or "" for page in pdf.pages)
        year = self._get_year(full_text)
        bill_month = self._get_bill_month(full_text)
        results = []

        for m in self._TXN.finditer(full_text):
            spend_date_str, desc, amount_str, card_last4 = m.groups()
            desc = desc.strip()
            amount = Decimal(amount_str.replace(",", ""))

            if self._SKIP.search(desc) or amount <= 0:
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
        if not m:
            return date.today().year
        roc_year = int(m.group(1))
        return roc_year + 1911 if roc_year < 1000 else roc_year

    def _get_bill_month(self, text: str) -> int:
        m = self._HEADER_YEAR.search(text)
        return int(m.group(2)) if m else date.today().month