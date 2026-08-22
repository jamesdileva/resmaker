"""Document parsers for the import pipeline."""

from app.parsers.base import BaseParser, ParsedDocument, Paragraph
from app.parsers.docx_parser import DocxParser
from app.parsers.pdf_parser import PdfParser
from app.parsers.txt_parser import TxtParser

_PARSERS: dict[str, type[BaseParser]] = {
    "docx": DocxParser,
    "pdf": PdfParser,
    "txt": TxtParser,
}


def get_parser(file_type: str) -> BaseParser:
    """Return the parser instance handling the given file extension."""
    key = file_type.lower().lstrip(".")
    parser_class = _PARSERS.get(key)
    if parser_class is None:
        raise ValueError(f"Unsupported file type: {file_type}")
    return parser_class()


__all__ = [
    "BaseParser",
    "ParsedDocument",
    "Paragraph",
    "DocxParser",
    "PdfParser",
    "TxtParser",
    "get_parser",
]
