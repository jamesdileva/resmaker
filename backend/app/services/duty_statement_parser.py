"""Duty statement parser: extracts structured requirements from job postings."""

import re

from app.models.duty import DutyRequirement
from app.services.extraction_service import ExtractionService

NUMBERED_PREFIX_RE = re.compile(r"^\s*(\d{1,2})\s*[.)]\s+")
BULLET_PREFIX_RE = re.compile(r"^\s*[\u2022\u25cf\u25aa\u25e6\u2023\u00b7\-\*]\s+")


class DutyStatementParser:
    """Parses a job posting's duty statement into individual requirements."""

    def __init__(self, extraction: ExtractionService | None = None) -> None:
        self.extraction = extraction or ExtractionService()

    def parse(self, text: str) -> list[DutyRequirement]:
        """Extract duties from raw posting text.

        Strategy:
          1. Numbered and bulleted lines become one duty each.
          2. If no structured lines exist, flowing paragraphs are split
             on sentence boundaries.
        """
        lines = [line.strip() for line in text.splitlines() if line.strip()]

        requirements = self._parse_structured_lines(lines)
        if not requirements:
            requirements = self._parse_prose(" ".join(lines))

        for index, requirement in enumerate(requirements):
            requirement.order_index = index
            requirement.category = self.classify_requirement(requirement.text)
            requirement.keywords = self.extraction.extract_keywords(
                requirement.text
            )[:10]
        return requirements

    def classify_requirement(self, text: str) -> str:
        """Assign a topic category to a duty statement."""
        from app.models.knowledge import ParagraphType

        return self.extraction.assign_category(text, ParagraphType.NORMAL_TEXT)

    def extract_keywords(self, requirements: list[DutyRequirement]) -> list[str]:
        """Aggregate deduplicated keywords across all requirements."""
        keywords: list[str] = []
        for requirement in requirements:
            for keyword in requirement.keywords:
                if keyword not in keywords:
                    keywords.append(keyword)
        return keywords

    # --- internals ---

    @staticmethod
    def _strip_numbered(line: str) -> tuple[bool, str]:
        match = NUMBERED_PREFIX_RE.match(line)
        if match is None:
            return False, line
        return True, NUMBERED_PREFIX_RE.sub("", line, count=1).strip()

    @staticmethod
    def _strip_bullet(line: str) -> tuple[bool, str]:
        if BULLET_PREFIX_RE.match(line) is None:
            return False, line
        cleaned = re.sub(r"^[\s\u2022\u25cf\u25aa\u25e6\u2023\u00b7\-*]+", "", line)
        return True, cleaned.strip()

    def _parse_structured_lines(self, lines: list[str]) -> list[DutyRequirement]:
        duties: list[DutyRequirement] = []
        for line in lines:
            is_numbered, cleaned = self._strip_numbered(line)
            if not is_numbered:
                is_bulleted, cleaned = self._strip_bullet(line)
                if not is_bulleted:
                    continue
            if len(cleaned.split()) < 3:
                continue
            duties.append(DutyRequirement(text=cleaned))
        return duties

    def _parse_prose(self, text: str) -> list[DutyRequirement]:
        sentences = re.split(r"(?<=[.!?])\s+", text)
        duties: list[DutyRequirement] = []
        for sentence in sentences:
            cleaned = sentence.strip()
            # Keep substantive sentences only; skip fragments and headers.
            if len(cleaned.split()) < 6 or cleaned.lower().endswith(":"):
                continue
            duties.append(DutyRequirement(text=cleaned))
        return duties
