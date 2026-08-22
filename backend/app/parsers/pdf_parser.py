"""PDF parser built on pymupdf."""

import re
from pathlib import Path

import pymupdf

from app.parsers.base import BaseParser, ParsedDocument, Paragraph

# Lines starting with these characters are treated as list items rather
# than wrapped prose to be merged.
_BULLET_PREFIX_RE = re.compile(r"^[\u2022\u25cf\u25aa\u25e6\u2023\u00b7]\s*|\s*-\s+")


class PdfParser(BaseParser):
    """Extracts text from PDFs block by block, preserving reading order.

    MVP behavior per Implementation Guide 8.3: all text is Normal style.
    Bullet-looking lines are emitted as separate paragraphs so downstream
    classification can detect them.
    """

    def parse(self, file_path: str) -> ParsedDocument:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")

        with pymupdf.open(str(path)) as document:
            paragraphs: list[Paragraph] = []
            for page in document:
                for block in page.get_text("blocks"):
                    block_text = block[4].replace("\u200b", "")
                    paragraphs.extend(self._block_to_paragraphs(block_text))

        return ParsedDocument(
            filename=path.name,
            file_type="pdf",
            paragraphs=paragraphs,
        )

    def supported_types(self) -> list[str]:
        return ["pdf"]

    @staticmethod
    def _is_bullet_line(line: str) -> bool:
        stripped = line.strip()
        if re.match(r"^[\u2022\u25cf\u25aa\u25e6\u2023\u00b7]", stripped):
            return True
        return bool(re.match(r"-\s+\S", stripped))

    def _block_to_paragraphs(self, block_text: str) -> list[Paragraph]:
        """Group block lines into paragraphs.

        Bullet-marked lines start a new bullet paragraph; every other line
        continues the current paragraph (so wrapped prose and multi-line
        bullets merge correctly).
        """
        paragraphs: list[Paragraph] = []
        current_lines: list[str] = []
        current_is_bullet = False

        def flush() -> None:
            nonlocal current_lines, current_is_bullet
            merged = " ".join(part.strip() for part in current_lines)
            if merged:
                paragraphs.append(
                    Paragraph(
                        text=merged,
                        style="Normal",
                        is_bullet=current_is_bullet,
                    )
                )
            current_lines = []
            current_is_bullet = False

        for line in block_text.splitlines():
            stripped = line.strip()
            if not stripped:
                flush()
                continue
            if self._is_bullet_line(stripped):
                flush()
                cleaned = _BULLET_PREFIX_RE.sub("", stripped, count=1).strip()
                current_lines = [cleaned]
                current_is_bullet = True
            else:
                current_lines.append(stripped)

        flush()
        return paragraphs
