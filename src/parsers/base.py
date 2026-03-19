from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from datetime import date
import pdfplumber

@dataclass
class Transaction:
    date: date
    description: str
    amount: Decimal
    currency: str = "TWD"
    bank: str = ""
    payment_page_id: str = ""

class BaseParser(ABC):
    bank_name: str = ""

    @abstractmethod
    def parse(self, pdf: pdfplumber.PDF) -> list[Transaction]: ...