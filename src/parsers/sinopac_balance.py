import re
from datetime import date
from decimal import Decimal
import pdfplumber
from .balance_base import BalanceEntry


class SinoPacBalanceParser:
    """Parse 永豐銀行 電子綜合對帳單 for TWD and foreign currency balances."""

    _PERIOD = re.compile(r"對帳單期間：\d{4}/\d{2}/\d{2}~(\d{4})/(\d{2})/(\d{2})")
    _TWD = re.compile(r"^臺幣\s+([\d,]+)", re.MULTILINE)
    _FX = re.compile(r"^外幣\s+([\d,]+)", re.MULTILINE)

    def parse(self, pdf: pdfplumber.PDF) -> list[BalanceEntry]:
        text = pdf.pages[0].extract_text() or ""

        m = self._PERIOD.search(text)
        if not m:
            return []
        bal_date = date(int(m.group(1)), int(m.group(2)), int(m.group(3)))

        results = []

        m_twd = self._TWD.search(text)
        if m_twd:
            results.append(BalanceEntry(
                date=bal_date,
                account_name="永豐活儲",
                amount=Decimal(m_twd.group(1).replace(",", "")),
            ))

        m_fx = self._FX.search(text)
        if m_fx:
            amt = Decimal(m_fx.group(1).replace(",", ""))
            if amt > 0:  # skip if no foreign currency
                results.append(BalanceEntry(
                    date=bal_date,
                    account_name="永豐外幣",
                    amount=amt,
                    currency="TWD",  # already converted to TWD equivalent in statement
                ))

        return results