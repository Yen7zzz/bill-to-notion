from .base import BaseParser
from .esun import ESunParser
from .sinopac import SinoPacParser
from .cathay import CathayParser

SENDER_MAP: dict[str, type[BaseParser]] = {
    "estatement@esunbank.com":                  ESunParser,
    "ebillservice@newebill.banksinopac.com.tw": SinoPacParser,
    "service@pxbillrc01.cathaybk.com.tw":       CathayParser,
}

def get_parser(sender: str) -> BaseParser | None:
    cls = SENDER_MAP.get(sender)
    return cls() if cls else None