"""Plain text parser: one paragraph per non-empty line."""

from pathlib import Path

from app.parsers.base import BaseParser, ParsedDocument, Paragraph


class TxtParser(BaseParser):
    """Reads plain text files line by line as Normal-style paragraphs."""

    def parse(self, file_path: str) -> ParsedDocument:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"TXT file not found: {file_path}")
        content = path.read_text(encoding="utf-8")

        paragraphs = [
            Paragraph(text=line.strip(), style="Normal")
            for line in content.splitlines()
            if line.strip()
        ]
        return ParsedDocument(
            filename=path.name,
            file_type="txt",
            paragraphs=paragraphs,
        )

    def supported_types(self) -> list[str]:
        return ["txt"]
