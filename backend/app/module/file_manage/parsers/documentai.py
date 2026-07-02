import os
from app.settings.config import settings


class DocumentAIParser:
    def parse(self, file_path: str) -> dict:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        project_id = settings.GOOGLE_DOCUMENT_AI_PROJECT_ID
        processor_id = settings.GOOGLE_DOCUMENT_AI_PROCESSOR_ID
        location = settings.GOOGLE_DOCUMENT_AI_LOCATION

        if not project_id or not processor_id:
            raise RuntimeError(
                "Google Document AI not configured. "
                "Set GOOGLE_DOCUMENT_AI_PROJECT_ID and GOOGLE_DOCUMENT_AI_PROCESSOR_ID"
            )

        try:
            from google.cloud import documentai

            client_options = {"api_endpoint": f"{location}-documentai.googleapis.com"} if location else {}
            client = documentai.DocumentProcessorServiceClient(client_options=client_options)

            with open(file_path, "rb") as f:
                content = f.read()

            raw_document = documentai.RawDocument(content=content, mime_type="application/pdf")
            name = client.processor_path(project_id, location or "us", processor_id)
            request = documentai.ProcessRequest(name=name, raw_document=raw_document)
            result = client.process_document(request=request)
            doc = result.document

            text = doc.text or ""
            page_count = len(doc.pages) if hasattr(doc, "pages") else 0

        except ImportError:
            raise RuntimeError("google-cloud-documentai is not installed. Run: pip install google-cloud-documentai")
        except Exception as e:
            raise RuntimeError(f"Document AI parsing failed: {e}")

        subject = text.strip().split("\n")[0][:500] if text.strip() else None

        return {
            "page_count": page_count,
            "subject": subject,
            "raw_text": text,
        }
