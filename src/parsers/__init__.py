from .base import BaseParser
from .esun import ESunParser
from .sinopac import SinoPacParser
from .cathay import CathayParser

# Values are (parser_class, subject_filter).
# subject_filter is passed as an IMAP SUBJECT criterion; None means no filter.
SENDER_MAP: dict[str, tuple[type[BaseParser], str | None]] = {
    "estatement@esunbank.com":                  (ESunParser,   None),
    "ebillservice@newebill.banksinopac.com.tw": (SinoPacParser, None),
    "service@pxbillrc01.cathaybk.com.tw":       (CathayParser, "電子帳單"),
}

def get_parser(sender: str) -> BaseParser | None:
    entry = SENDER_MAP.get(sender)
    return entry[0]() if entry else None