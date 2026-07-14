from __future__ import annotations

from dataclasses import dataclass
import io
import re
from typing import Any

import fitz
from PIL import Image

from app.settings.config import settings


@dataclass
class OCRResult:
    markdown: str
    text: str
    engine: str


class OCRPipeline:
    def __init__(self, preferred_engine: str = "auto"):
        self.preferred_engine = preferred_engine
        self._paddle_reader: Any | None = None
        self._documentai_client: Any | None = None

    def extract_pdf(self, file_path: str) -> tuple[list[str], str]:
        pdf = fitz.open(file_path)
        pages: list[str] = []
        for index in range(pdf.page_count):
            pages.append(self.extract_page(pdf[index]).markdown)
        pdf.close()
        return pages, "\n\n".join(filter(None, pages)).strip()

    def extract_page(self, page: fitz.Page) -> OCRResult:
        image = self._render_page(page, dpi=300)
        processed = self._preprocess_image(image)

        engines = self._ordered_engines()
        last_error: Exception | None = None
        for engine in engines:
            try:
                if engine == "paddleocr":
                    result = self._run_paddleocr(processed)
                else:
                    result = self._run_documentai(processed)
                if result.text.strip():
                    return result
            except Exception as exc:
                last_error = exc
                continue

        if last_error:
            raise RuntimeError(f"OCR pipeline failed: {last_error}") from last_error
        return OCRResult(markdown="", text="", engine="none")

    def _ordered_engines(self) -> list[str]:
        if self.preferred_engine == "documentai":
            return ["documentai", "paddleocr"]
        return ["paddleocr", "documentai"]

    def _render_page(self, page: fitz.Page, dpi: int = 300) -> Image.Image:
        pix = page.get_pixmap(dpi=dpi, alpha=False)
        return Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")

    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        try:
            import cv2
            import numpy as np
        except ImportError:
            return image

        array = np.array(image)
        gray = cv2.cvtColor(array, cv2.COLOR_RGB2GRAY)
        denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
        binary = cv2.adaptiveThreshold(
            denoised,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            31,
            11,
        )
        kernel = np.ones((1, 1), np.uint8)
        opened = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
        return Image.fromarray(opened).convert("RGB")

    def _run_paddleocr(self, image: Image.Image) -> OCRResult:
        try:
            from paddleocr import PaddleOCR
            import numpy as np
        except ImportError as exc:
            raise RuntimeError("paddleocr is not installed") from exc

        if self._paddle_reader is None:
            self._paddle_reader = PaddleOCR(use_angle_cls=True, lang="en", show_log=False)

        raw = self._paddle_reader.ocr(np.array(image), cls=True)
        lines = self._flatten_paddle_result(raw)
        markdown = self._build_structured_markdown(lines)
        return OCRResult(markdown=markdown, text=self._strip_markdown(markdown), engine="paddleocr")

    def _flatten_paddle_result(self, raw: Any) -> list[dict[str, Any]]:
        items = raw[0] if isinstance(raw, list) and raw and isinstance(raw[0], list) else raw
        lines: list[dict[str, Any]] = []
        for item in items or []:
            if not isinstance(item, (list, tuple)) or len(item) < 2:
                continue
            box = item[0]
            payload = item[1]
            if not isinstance(payload, (list, tuple)) or not payload:
                continue
            text = str(payload[0]).strip()
            if not text:
                continue
            coords = [(float(pt[0]), float(pt[1])) for pt in box]
            ys = [pt[1] for pt in coords]
            xs = [pt[0] for pt in coords]
            lines.append(
                {
                    "text": self._clean_text(text),
                    "y": sum(ys) / len(ys),
                    "x": min(xs),
                    "height": max(ys) - min(ys),
                }
            )
        return lines

    def _build_structured_markdown(self, lines: list[dict[str, Any]]) -> str:
        if not lines:
            return ""

        sorted_lines = sorted(lines, key=lambda item: (item["y"], item["x"]))
        heights = [line["height"] for line in sorted_lines if line["height"] > 0]
        median_height = sorted(heights)[len(heights) // 2] if heights else 0.0

        rows: list[list[dict[str, Any]]] = []
        for line in sorted_lines:
            if not rows or abs(line["y"] - rows[-1][0]["y"]) > max(12.0, median_height * 0.6):
                rows.append([line])
            else:
                rows[-1].append(line)

        blocks: list[str] = []
        paragraph_buffer: list[str] = []

        def flush_paragraph() -> None:
            if paragraph_buffer:
                blocks.append(" ".join(paragraph_buffer).strip())
                paragraph_buffer.clear()

        for row in rows:
            row = sorted(row, key=lambda item: item["x"])
            texts = [item["text"] for item in row if item["text"]]
            if not texts:
                continue
            avg_height = sum(item["height"] for item in row) / max(1, len(row))
            joined = " ".join(texts).strip()

            if len(texts) >= 3:
                flush_paragraph()
                blocks.append("| " + " | ".join(texts) + " |")
                continue

            if median_height and avg_height > median_height * 1.35 and len(joined) <= 120:
                flush_paragraph()
                blocks.append(f"## {joined}")
                continue

            paragraph_buffer.append(joined)

        flush_paragraph()
        return "\n\n".join(blocks).strip()

    def _run_documentai(self, image: Image.Image) -> OCRResult:
        project_id = settings.GOOGLE_DOCUMENT_AI_PROJECT_ID
        processor_id = settings.GOOGLE_DOCUMENT_AI_PROCESSOR_ID
        location = settings.GOOGLE_DOCUMENT_AI_LOCATION
        if not project_id or not processor_id:
            raise RuntimeError("Google Document AI not configured")

        try:
            from google.cloud import documentai
        except ImportError as exc:
            raise RuntimeError("google-cloud-documentai is not installed") from exc

        if self._documentai_client is None:
            client_options = {"api_endpoint": f"{location}-documentai.googleapis.com"} if location else {}
            self._documentai_client = documentai.DocumentProcessorServiceClient(client_options=client_options)

        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        raw_document = documentai.RawDocument(content=buffer.getvalue(), mime_type="image/png")
        name = self._documentai_client.processor_path(project_id, location or "us", processor_id)
        request = documentai.ProcessRequest(name=name, raw_document=raw_document)
        result = self._documentai_client.process_document(request=request)
        doc = result.document

        markdown = self._documentai_to_markdown(doc)
        text = self._strip_markdown(markdown) or self._clean_text(doc.text or "")
        return OCRResult(markdown=markdown or text, text=text, engine="documentai")

    def _documentai_to_markdown(self, doc: Any) -> str:
        pages = getattr(doc, "pages", None) or []
        if not pages:
            return self._clean_text(getattr(doc, "text", "") or "")

        blocks: list[str] = []
        for page in pages:
            page_blocks: list[str] = []
            for paragraph in getattr(page, "paragraphs", []) or []:
                text = self._text_from_anchor(doc.text or "", getattr(paragraph.layout, "text_anchor", None))
                text = self._clean_text(text)
                if text:
                    page_blocks.append(text)
            for table in getattr(page, "tables", []) or []:
                rows = []
                for row in list(getattr(table, "header_rows", []) or []) + list(getattr(table, "body_rows", []) or []):
                    cells = []
                    for cell in getattr(row, "cells", []) or []:
                        cell_text = self._text_from_anchor(doc.text or "", getattr(cell.layout, "text_anchor", None))
                        cell_text = self._clean_text(cell_text)
                        if cell_text:
                            cells.append(cell_text)
                    if cells:
                        rows.append("| " + " | ".join(cells) + " |")
                page_blocks.extend(rows)
            if not page_blocks:
                fallback = self._clean_text(getattr(doc, "text", "") or "")
                if fallback:
                    page_blocks.append(fallback)
            blocks.append("\n\n".join(page_blocks).strip())
        return "\n\n".join(filter(None, blocks)).strip()

    def _text_from_anchor(self, full_text: str, anchor: Any) -> str:
        if not anchor or not getattr(anchor, "text_segments", None):
            return ""
        parts: list[str] = []
        for segment in anchor.text_segments:
            start = int(getattr(segment, "start_index", 0) or 0)
            end = int(getattr(segment, "end_index", 0) or 0)
            parts.append(full_text[start:end])
        return "".join(parts)

    def _strip_markdown(self, text: str) -> str:
        stripped = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)
        stripped = re.sub(r"^\|\s*", "", stripped, flags=re.MULTILINE)
        stripped = re.sub(r"\s*\|\s*", " ", stripped)
        return self._clean_text(stripped)

    def _clean_text(self, text: str) -> str:
        text = re.sub(r"[—–•·]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()
