import pikepdf
import pdfplumber
from io import BytesIO
from src.parsers.sinopac import SinoPacParser

def test_sinopac():
    password = "E125353141"
    with open(r"C:\Users\2993\bill-to-notion\pythonProject\永豐銀行信用卡帳單 (1).pdf", "rb") as f:
        encrypted = f.read()

    buf = BytesIO()
    with pikepdf.open(BytesIO(encrypted), password=password) as p:
        p.save(buf)
    buf.seek(0)

    pdf = pdfplumber.open(buf)
    txns = SinoPacParser().parse(pdf)

    for t in txns:
        print(t)
    print(f"Total: {len(txns)}")

test_sinopac()