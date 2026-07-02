import os


class DoclingParser:
    def parse(self, file_path: str) -> dict:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        try:
            from docling.document_converter import DocumentConverter
            converter = DocumentConverter()
            result = converter.convert(file_path)
            doc = result.document
            text = doc.export_to_text() if hasattr(doc, "export_to_text") else ""
            page_count = len(doc.pages) if hasattr(doc, "pages") else 0
        except ImportError:
            raise RuntimeError("docling is not installed. Run: pip install docling")
        except Exception as e:
            raise RuntimeError(f"Docling parsing failed: {e}")

        subject = text.strip().split("\n")[0][:500] if text.strip() else None

        return {
            "page_count": page_count,
            "subject": subject,
            "raw_text": text,
        }
