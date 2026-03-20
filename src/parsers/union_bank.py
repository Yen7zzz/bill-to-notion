import re
import calendar
from datetime import date
from decimal import Decimal
import pdfplumber
from .base import Transaction
from .balance_base import BalanceEntry

UNION_CC_PAGE_ID = "2c640bb7-4433-80f0-bd37-ee84787fd926"


class UnionBankCreditParser:
    """Extract credit card payment entries from 聯邦銀行 對帳單."""
    bank_name = "聯邦銀行"

    # 115/01/20 08:37:47 88850*9*9*8* 1234****2535**** 239.00 電子繳信用卡款
    _CC_PAYMENT = re.compile(
        r"^(\d{3})/(\d{2})/(\d{2})\s+\d{2}:\d{2}:\d{2}\s+\S+\s+\S+\s+([\d,]+\.\d{2})\s+.*繳信用卡款",
        re.MULTILINE,
    )

    def parse(self, pdf: pdfplumber.PDF) -> list[Transaction]:
        full_text = "\n".join(p.extract_text() or "" for p in pdf.pages)
        results = []

        for m in self._CC_PAYMENT.finditer(full_text):
            roc_year = int(m.group(1))
            month, day = int(m.group(2)), int(m.group(3))
            amount = Decimal(m.group(4).replace(",", ""))
            if amount <= 0:
                continue
            results.append(Transaction(
                date=date(roc_year + 1911, month, day),
                description="聯邦信用卡費",
                amount=amount,
                bank=self.bank_name,
                payment_page_id=UNION_CC_PAGE_ID,
            ))

        return results


class UnionBankBalanceParser:
    """Extract end-of-month balance from 聯邦銀行 對帳單."""
    bank_name = "聯邦銀行"

    # Format A (newer): 餘額基準日：115/2/28
    _DATE_A = re.compile(r"餘額基準日：(\d{3})/(\d{1,2})/(\d{1,2})")
    # Format B (older): 截至基準日115年01月底
    _DATE_B = re.compile(r"截至基準日(\d{3})年(\d{2})月底")
    # Both formats end with: 活期儲蓄存款 <amount>
    _BALANCE = re.compile(r"活期儲蓄存款\s+([\d,.]+)")

    def parse(self, pdf: pdfplumber.PDF) -> list[BalanceEntry]:
        full_text = "\n".join(p.extract_text() or "" for p in pdf.pages)

        bal_date = self._get_date(full_text)
        if not bal_date:
            return []

        m = self._BALANCE.search(full_text)
        if not m:
            return []

        return [BalanceEntry(
            date=bal_date,
            account_name="聯邦活儲",
            amount=Decimal(m.group(1).replace(",", "")),
        )]

    def _get_date(self, text: str) -> date | None:
        m = self._DATE_A.search(text)
        if m:
            return date(int(m.group(1)) + 1911, int(m.group(2)), int(m.group(3)))

        m = self._DATE_B.search(text)
        if m:
            year = int(m.group(1)) + 1911
            month = int(m.group(2))
            last_day = calendar.monthrange(year, month)[1]
            return date(year, month, last_day)

        return None