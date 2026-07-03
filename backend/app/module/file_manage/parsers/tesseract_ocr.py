import os
import fitz
import pytesseract
from PIL import Image
import io
import re


class TesseractOCRParser:
    def parse(self, file_path: str) -> dict:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        pdf = fitz.open(file_path)
        page_count = pdf.page_count
        pages_text: list[str] = []
        subject = None

        for i in range(page_count):
            page = pdf[i]
            pix = page.get_pixmap(dpi=200)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            text = pytesseract.image_to_string(img, lang="hin+eng")
            text = self._clean_text(text)
            if text:
                if subject is None:
                    lines = [l.strip() for l in text.split("\n") if l.strip()]
                    if lines:
                        subject = lines[0][:500]
                pages_text.append(text)
            else:
                pages_text.append("")

        pdf.close()

        raw_text = "\n\n".join(filter(None, pages_text))

        return {
            "page_count": page_count,
            "subject": subject,
            "raw_text": raw_text,
            "pages": pages_text,
        }

    def _clean_text(self, text: str) -> str:
        text = re.sub(r"[—–•·]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()
