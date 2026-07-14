PARSER_REGISTRY = {}


def _check_import(module: str, name: str) -> bool:
    try:
        __import__(module)
        return True
    except ImportError:
        return False

def _register_parsers():
    from .pymupdf import PyMuPDFParser
    PARSER_REGISTRY["pymupdf"] = PyMuPDFParser

    if _check_import("docling", "DoclingParser"):
        from .docling import DoclingParser
        PARSER_REGISTRY["docling"] = DoclingParser
    else:
        PARSER_REGISTRY["docling"] = None

    if _check_import("google.cloud.documentai", "DocumentAIParser"):
        from .documentai import DocumentAIParser
        PARSER_REGISTRY["documentai"] = DocumentAIParser
    else:
        PARSER_REGISTRY["documentai"] = None


_register_parsers()


def get_parser(parser_type: str | None):
    key = parser_type or "pymupdf"
    cls = PARSER_REGISTRY.get(key) or PARSER_REGISTRY.get("pymupdf")
    return cls()


def parse_document(file_path: str, parser_type: str | None) -> dict:
    parser = get_parser(parser_type)
    return parser.parse(file_path)
