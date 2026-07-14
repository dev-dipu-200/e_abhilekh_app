import unittest
from unittest.mock import MagicMock, patch

from app.module.file_manage.parsers.documentai import DocumentAIParser
from app.module.file_manage.parsers.ocr_pipeline import OCRPipeline, OCRResult
from app.module.file_manage.parsers.pymupdf import PyMuPDFParser


class FakePage:
    def __init__(self, has_images: bool):
        self._has_images = has_images

    def get_images(self, full: bool = True):
        return [object()] if self._has_images else []


class FakePDF:
    def __init__(self, pages):
        self._pages = pages
        self.page_count = len(pages)
        self.closed = False

    def __getitem__(self, index: int):
        return self._pages[index]

    def close(self):
        self.closed = True


class OCRPipelineTests(unittest.TestCase):
    def test_auto_prefers_paddleocr_before_documentai(self):
        pipeline = OCRPipeline(preferred_engine="auto")
        self.assertEqual(pipeline._ordered_engines(), ["paddleocr", "documentai"])

    def test_documentai_mode_prefers_documentai_before_paddleocr(self):
        pipeline = OCRPipeline(preferred_engine="documentai")
        self.assertEqual(pipeline._ordered_engines(), ["documentai", "paddleocr"])


class PyMuPDFParserTests(unittest.TestCase):
    def test_merge_page_content_only_appends_unique_ocr_lines(self):
        parser = PyMuPDFParser()

        merged = parser._merge_page_content(
            "Office Order\nReference 123",
            "Office Order\nScanned Annexure",
        )

        self.assertEqual(merged, "Office Order\nReference 123\n\nScanned Annexure")

    @patch("app.module.file_manage.parsers.pymupdf.os.path.exists", return_value=True)
    @patch("app.module.file_manage.parsers.pymupdf.fitz.open")
    def test_parse_merges_searchable_and_scanned_pages(self, mock_open, _mock_exists):
        parser = PyMuPDFParser()
        fake_pdf = FakePDF([FakePage(has_images=True), FakePage(has_images=False)])
        mock_open.return_value = fake_pdf

        direct_text = "Direct text from searchable PDF content that is long enough"
        parser._extract_with_pymupdf4llm = MagicMock(return_value=[direct_text, ""])
        parser.ocr_pipeline.extract_page = MagicMock(
            side_effect=[
                OCRResult(markdown=f"{direct_text}\nScanned note", text=f"{direct_text} Scanned note", engine="paddleocr"),
                OCRResult(markdown="Second page OCR", text="Second page OCR", engine="paddleocr"),
            ]
        )

        result = parser.parse("/tmp/sample.pdf")

        self.assertEqual(result["page_count"], 2)
        self.assertEqual(result["pages"], [f"{direct_text}\n\nScanned note", "Second page OCR"])
        self.assertEqual(result["raw_text"], f"{direct_text}\n\nScanned note\n\nSecond page OCR")
        self.assertEqual(result["subject"], direct_text)
        self.assertTrue(fake_pdf.closed)


class DocumentAIParserTests(unittest.TestCase):
    @patch("app.module.file_manage.parsers.documentai.os.path.exists", return_value=True)
    @patch("app.module.file_manage.parsers.documentai.fitz.open")
    def test_parse_returns_pages_for_chunking(self, mock_open, _mock_exists):
        parser = DocumentAIParser()
        fake_pdf = FakePDF([FakePage(has_images=False), FakePage(has_images=False)])
        mock_open.return_value = fake_pdf
        parser.ocr_pipeline.extract_pdf = MagicMock(
            return_value=(["First page", "Second page"], "First page\n\nSecond page")
        )

        with patch("app.module.file_manage.parsers.documentai.settings.GOOGLE_DOCUMENT_AI_PROJECT_ID", "demo-project"), \
             patch("app.module.file_manage.parsers.documentai.settings.GOOGLE_DOCUMENT_AI_PROCESSOR_ID", "demo-processor"):
            result = parser.parse("/tmp/sample.pdf")

        self.assertEqual(result["page_count"], 2)
        self.assertEqual(result["pages"], ["First page", "Second page"])
        self.assertEqual(result["raw_text"], "First page\n\nSecond page")
        self.assertEqual(result["subject"], "First page")
        self.assertTrue(fake_pdf.closed)


if __name__ == "__main__":
    unittest.main()
