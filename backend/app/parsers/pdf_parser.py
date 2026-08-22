"""PDF parser built on pymupdf."""

from pathlib import Path

import pymupdf

from app.parsers.base import BaseParser, ParsedDocument, Paragraph


class PdfParser(BaseParser):
    """Extracts text from PDFs block by block, preserving reading order.

    MVP behavior per Implementation Guide 8.3: all text is returned as
    Normal-style paragraphs; no heading or bullet inference.
    """

    def parse(self, file_path: str) -> ParsedDocument:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")

        with pymupdf.open(str(path)) as document:
            paragraphs: list[Paragraph] = []
            for page in document:
                # Blocks come back in document order; join wrapped lines
                # within a block into a single paragraph.
                for block in page.get_text("blocks"):
                    text = block[4].strip()
                    if not text:
                        continue
                    merged = " ".join(line.strip() for line in text.splitlines())
                    paragraphs.append(Paragraph(text=merged, style="Normal"))

        return ParsedDocument(
            filename=path.name,
            file_type="pdf",
            paragraphs=paragraphs,
        )

    def supported_types(self) -> list[str]:
        return ["pdf"]
