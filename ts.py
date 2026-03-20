# inspect_bank.py
import pikepdf
import pdfplumber
from io import BytesIO

PDF_PATH = r"C:\Users\2993\Downloads\永豐銀行2026年02月份-電子綜合對帳單.pdf"
PASSWORD = "E125353141"

buf = BytesIO()
with pikepdf.open(PDF_PATH, password=PASSWORD) as p:
    p.save(buf)
buf.seek(0)

pdf = pdfplumber.open(buf)
for i, page in enumerate(pdf.pages):
    print(f"=== PAGE {i} ===")
    text = page.extract_text()
    print(text)
    print()