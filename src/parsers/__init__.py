from dataclasses import dataclass
from .esun import ESunParser
from .sinopac import SinoPacParser
from .cathay import CathayParser
from .union_bank import UnionBankCreditParser, UnionBankBalanceParser
from .sinopac_balance import SinoPacBalanceParser


@dataclass
class DispatchRule:
    sender: str
    filename_contains: str | None  # None = no filter
    parser_cls: type
    target: str  # "credit_card" or "balance"


DISPATCH: list[DispatchRule] = [
    # --- Credit card parsers ---
    DispatchRule("estatement@esunbank.com",                  None,                   ESunParser,            "credit_card"),
    DispatchRule("ebillservice@newebill.banksinopac.com.tw", "信用卡帳單",            SinoPacParser,         "credit_card"),
    DispatchRule("service@pxbillrc01.cathaybk.com.tw",       "信用卡電子帳單消費明細", CathayParser,          "credit_card"),
    DispatchRule("stmnt@ubot.com.tw",                        None,                   UnionBankCreditParser, "credit_card"),
    # --- Balance parsers ---
    DispatchRule("ebillservice@newebill.banksinopac.com.tw", "電子綜合對帳單",        SinoPacBalanceParser,  "balance"),
    DispatchRule("stmnt@ubot.com.tw",                        None,                   UnionBankBalanceParser, "balance"),
]