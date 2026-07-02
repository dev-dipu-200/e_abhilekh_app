from .pymupdf import PyMuPDFParser
from .docling import DoclingParser
from .documentai import DocumentAIParser

PARSERS = {
    "pymupdf": PyMuPDFParser,
    "docling": DoclingParser,
    "documentai": DocumentAIParser,
}


def get_parser(parser_type: str | None):
    cls = PARSERS.get(parser_type or "pymupdf")
    if not cls:
        cls = PyMuPDFParser
    return cls()


def parse_document(file_path: str, parser_type: str | None) -> dict:
    parser = get_parser(parser_type)
    return parser.parse(file_path)
