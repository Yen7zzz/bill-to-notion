from .base import BaseParser
from .esun import ESunParser
from .sinopac import SinoPacParser
from .cathay import CathayParser

# Values are (parser_class, filename_contains).
# filename_contains filters attachments by decoded filename substring; None accepts any PDF.
SENDER_MAP: dict[str, tuple[type[BaseParser], str | None]] = {
    "estatement@esunbank.com":                  (ESunParser,    None),
    "ebillservice@newebill.banksinopac.com.tw": (SinoPacParser, None),
    "service@pxbillrc01.cathaybk.com.tw":       (CathayParser,  "信用卡電子帳單消費明細"),
}

def get_parser(sender: str) -> BaseParser | None:
    entry = SENDER_MAP.get(sender)
    return entry[0]() if entry else None