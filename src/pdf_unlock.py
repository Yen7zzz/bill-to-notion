import pikepdf
import pdfplumber
from io import BytesIO

def unlock_pdf(encrypted_bytes: bytes, password: str) -> pdfplumber.PDF:
    encrypted_buf = BytesIO(encrypted_bytes)
    decrypted_buf = BytesIO()

    with pikepdf.open(encrypted_buf, password=password) as pdf:
        pdf.save(decrypted_buf)

    decrypted_buf.seek(0)
    return pdfplumber.open(decrypted_buf)