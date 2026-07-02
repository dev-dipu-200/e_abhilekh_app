import os
import fitz


class PyMuPDFParser:
    def parse(self, file_path: str) -> dict:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        pdf = fitz.open(file_path)
        page_count = pdf.page_count
        text = ""
        for page in pdf:
            text += page.get_text()
        pdf.close()

        subject = text.strip().split("\n")[0][:500] if text.strip() else None

        return {
            "page_count": page_count,
            "subject": subject,
            "raw_text": text,
        }
