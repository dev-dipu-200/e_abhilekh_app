from __future__ import annotations

import os
import re
from typing import Any

import fitz

from .ocr_pipeline import OCRPipeline


class PyMuPDFParser:
    def __init__(self):
        self.ocr_pipeline = OCRPipeline(preferred_engine="auto")

    def parse(self, file_path: str) -> dict:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        pdf = fitz.open(file_path)
        page_count = pdf.page_count

        searchable_pages = self._extract_with_pymupdf4llm(file_path)
        merged_pages: list[str] = []

        for index in range(page_count):
            page = pdf[index]
            direct_text = searchable_pages[index] if index < len(searchable_pages) else ""
            has_images = bool(page.get_images(full=True))

            if self._page_needs_ocr(direct_text):
                ocr_result = self.ocr_pipeline.extract_page(page)
                merged_pages.append(ocr_result.markdown)
                continue

            if has_images:
                ocr_result = self.ocr_pipeline.extract_page(page)
                merged_pages.append(self._merge_page_content(direct_text, ocr_result.markdown))
                continue

            merged_pages.append(self._clean_text(direct_text))

        pdf.close()

        full_text = "\n\n".join(filter(None, merged_pages)).strip()
        subject = self._extract_subject(full_text)

        return {
            "page_count": page_count,
            "subject": subject,
            "raw_text": full_text,
            "pages": merged_pages,
        }

    def _extract_with_pymupdf4llm(self, file_path: str) -> list[str]:
        try:
            import pymupdf4llm
        except ImportError as exc:
            raise RuntimeError("pymupdf4llm is not installed. Run: pip install pymupdf4llm") from exc

        try:
            page_chunks = pymupdf4llm.to_markdown(file_path, page_chunks=True)
            pages = self._normalize_page_chunks(page_chunks)
            if pages:
                return pages
        except TypeError:
            pass
        except Exception as exc:
            raise RuntimeError(f"PyMuPDF4LLM parsing failed: {exc}") from exc

        try:
            markdown = pymupdf4llm.to_markdown(file_path)
        except Exception as exc:
            raise RuntimeError(f"PyMuPDF4LLM parsing failed: {exc}") from exc

        cleaned = self._clean_text(markdown)
        return [cleaned] if cleaned else []

    def _normalize_page_chunks(self, page_chunks: Any) -> list[str]:
        if not isinstance(page_chunks, list):
            return []

        pages_text: list[str] = []
        for chunk in page_chunks:
            if isinstance(chunk, str):
                pages_text.append(self._clean_text(chunk))
                continue
            if isinstance(chunk, dict):
                text = chunk.get("text") or chunk.get("md") or chunk.get("content") or ""
                pages_text.append(self._clean_text(text))
                continue
            pages_text.append(self._clean_text(str(chunk)))
        return pages_text

    def _page_needs_ocr(self, text: str) -> bool:
        if not text.strip():
            return True
        if len(text.strip()) < 40:
            return True
        return self._is_corrupted(text)

    def _merge_page_content(self, direct_text: str, ocr_markdown: str) -> str:
        direct_clean = self._clean_text(direct_text)
        ocr_clean = self._clean_text(ocr_markdown)
        if not direct_clean:
            return ocr_clean
        if not ocr_clean:
            return direct_clean

        direct_index = self._normalized_line_index(direct_clean)
        additions: list[str] = []
        for line in [self._clean_text(part) for part in ocr_clean.splitlines()]:
            if len(line) < 8:
                continue
            normalized = self._normalize_for_match(line)
            if not normalized:
                continue
            if normalized in direct_index:
                continue
            additions.append(line)

        if not additions:
            return direct_clean

        merged = direct_clean + "\n\n" + "\n".join(additions)
        return self._clean_text(merged)

    def _normalized_line_index(self, text: str) -> set[str]:
        index: set[str] = set()
        for line in text.splitlines():
            normalized = self._normalize_for_match(line)
            if normalized:
                index.add(normalized)
        return index

    def _normalize_for_match(self, text: str) -> str:
        text = text.lower()
        text = re.sub(r"[^0-9a-z\u0900-\u097f]+", "", text)
        return text.strip()

    def _is_corrupted(self, text: str) -> bool:
        devanagari = sum(1 for c in text if 0x0900 <= ord(c) <= 0x097F)
        if devanagari < 10:
            return False
        latin_ext = sum(1 for c in text if 0x0100 <= ord(c) <= 0x024F)
        return latin_ext > devanagari * 0.05

    def _extract_subject(self, text: str) -> str | None:
        for line in text.splitlines():
            clean = self._clean_text(line)
            if clean:
                return clean[:500]
        return None

    def _clean_text(self, text: str) -> str:
        text = re.sub(r"[—–•·]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()
