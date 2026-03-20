from dataclasses import dataclass
from decimal import Decimal
from datetime import date


@dataclass
class BalanceEntry:
    date: date
    account_name: str
    amount: Decimal
    currency: str = "TWD"