PARSER_REGISTRY = {}


def _register_parsers():
    from .pymupdf import PyMuPDFParser
    PARSER_REGISTRY["pymupdf"] = PyMuPDFParser
    from .tesseract_ocr import TesseractOCRParser
    PARSER_REGISTRY["tesseract"] = TesseractOCRParser
    try:
        from .docling import DoclingParser
        PARSER_REGISTRY["docling"] = DoclingParser
    except Exception:
        PARSER_REGISTRY["docling"] = None
    try:
        from .documentai import DocumentAIParser
        PARSER_REGISTRY["documentai"] = DocumentAIParser
    except Exception:
        PARSER_REGISTRY["documentai"] = None


_register_parsers()


def get_parser(parser_type: str | None):
    key = parser_type or "pymupdf"
    cls = PARSER_REGISTRY.get(key) or PARSER_REGISTRY.get("pymupdf")
    return cls()


def parse_document(file_path: str, parser_type: str | None) -> dict:
    parser = get_parser(parser_type)
    return parser.parse(file_path)
