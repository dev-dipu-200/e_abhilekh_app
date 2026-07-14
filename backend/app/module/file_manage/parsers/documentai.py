import os

import fitz

from app.settings.config import settings

from .ocr_pipeline import OCRPipeline


class DocumentAIParser:
    def __init__(self):
        self.ocr_pipeline = OCRPipeline(preferred_engine="documentai")

    def parse(self, file_path: str) -> dict:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        project_id = settings.GOOGLE_DOCUMENT_AI_PROJECT_ID
        processor_id = settings.GOOGLE_DOCUMENT_AI_PROCESSOR_ID
        if not project_id or not processor_id:
            raise RuntimeError(
                "Google Document AI not configured. "
                "Set GOOGLE_DOCUMENT_AI_PROJECT_ID and GOOGLE_DOCUMENT_AI_PROCESSOR_ID"
            )

        pdf = fitz.open(file_path)
        page_count = pdf.page_count
        pdf.close()

        pages, full_text = self.ocr_pipeline.extract_pdf(file_path)
        subject = next((line.strip()[:500] for line in full_text.splitlines() if line.strip()), None)

        return {
            "page_count": page_count,
            "subject": subject,
            "raw_text": full_text,
            "pages": pages,
        }
