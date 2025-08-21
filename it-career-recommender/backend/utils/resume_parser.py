# utils/resume_parser.py
from PyPDF2 import PdfReader
import docx

def extract_text(filename: str, contents: bytes) -> str:
    text = ""
    if filename.endswith(".pdf"):
        import io
        pdf = PdfReader(io.BytesIO(contents))
        for page in pdf.pages:
            text += page.extract_text() or ""
    elif filename.endswith(".docx"):
        import io
        with open("temp.docx", "wb") as f:
            f.write(contents)
        doc = docx.Document("temp.docx")
        text = "\n".join([p.text for p in doc.paragraphs])
    else:  # fallback for .txt
        text = contents.decode("utf-8", errors="ignore")
    return text
