"""Document parsing models and the parser interface."""

from abc import ABC, abstractmethod

from pydantic import BaseModel


class Paragraph(BaseModel):
    """A single parsed paragraph with structural hints."""

    text: str
    style: str = "Normal"
    is_bullet: bool = False
    bullet_level: int = 0
    is_heading: bool = False
    heading_level: int | None = None


class ParsedDocument(BaseModel):
    """The full result of parsing a document."""

    filename: str
    file_type: str
    paragraphs: list[Paragraph] = []


class BaseParser(ABC):
    """Interface all document parsers implement."""

    @abstractmethod
    def parse(self, file_path: str) -> ParsedDocument:
        """Parse a document file into structured paragraphs."""

    @abstractmethod
    def supported_types(self) -> list[str]:
        """Return the file extensions this parser handles."""
