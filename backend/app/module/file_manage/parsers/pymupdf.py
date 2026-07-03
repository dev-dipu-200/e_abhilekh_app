import os
import fitz
import pytesseract
from PIL import Image
import io
import re


class PyMuPDFParser:
    def parse(self, file_path: str) -> dict:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        pdf = fitz.open(file_path)
        page_count = pdf.page_count
        pages_text: list[str] = []
        full_text = ""
        for page in pdf:
            pt = page.get_text()
            pages_text.append(pt)
            full_text += pt
        pdf.close()

        subject = full_text.strip().split("\n")[0][:500] if full_text.strip() else None

        # Fall back to OCR when the PDF is image-only or when the embedded
        # Unicode mapping is broken and extracted Hindi text is unreadable.
        if self._should_fallback_to_ocr(full_text, pages_text):
            pages_text, full_text = self._ocr_extract(file_path)
            subject = full_text.strip().split("\n")[0][:500] if full_text.strip() else subject

        return {
            "page_count": page_count,
            "subject": subject,
            "raw_text": full_text,
            "pages": pages_text,
        }

    def _should_fallback_to_ocr(self, text: str, pages: list[str]) -> bool:
        non_empty_pages = sum(1 for page in pages if page.strip())
        if non_empty_pages == 0:
            return True

        if len(text.strip()) < 50:
            return True

        return self._is_corrupted(text)

    def _is_corrupted(self, text: str) -> bool:
        devanagari = sum(1 for c in text if 0x0900 <= ord(c) <= 0x097F)
        if devanagari < 10:
            return False
        latin_ext = sum(1 for c in text if 0x0100 <= ord(c) <= 0x024F)
        return latin_ext > devanagari * 0.05

    def _ocr_extract(self, file_path: str) -> tuple[list[str], str]:
        pdf = fitz.open(file_path)
        pages: list[str] = []
        for i in range(pdf.page_count):
            page = pdf[i]
            pix = page.get_pixmap(dpi=200)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            text = pytesseract.image_to_string(img, lang="hin+eng")
            pages.append(self._clean_text(text))
        pdf.close()
        return pages, "\n\n".join(pages)

    def _clean_text(self, text: str) -> str:
        text = re.sub(r"[—–•·]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()
