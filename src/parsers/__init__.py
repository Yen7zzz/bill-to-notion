from .base import BaseParser
from .esun import ESunParser
from .sinopac import SinoPacParser

SENDER_MAP: dict[str, type[BaseParser]] = {
    "estatement@esunbank.com":                  ESunParser,
    "ebillservice@newebill.banksinopac.com.tw": SinoPacParser,
}

def get_parser(sender: str) -> BaseParser | None:
    cls = SENDER_MAP.get(sender)
    return cls() if cls else None