"""Rule-based content classification for the import pipeline."""

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Optional

from app.models.knowledge import (
    BulletData,
    ExperienceHeading,
    MetricData,
    ParagraphType,
    SOQData,
)
from app.parsers.base import Paragraph

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

QUESTION_PREFIX_RE = re.compile(r"^\s*question\s*\d*\s*[:.)]?", re.IGNORECASE)
NUMBERED_QUESTION_RE = re.compile(r"^\s*\d{1,2}\s*[.)]\s+")
LETTERED_ITEM_RE = re.compile(r"^\s*[a-z]\.\s+", re.IGNORECASE)
QUESTION_CUE_WORDS = ("what", "how", "why", "describe", "tell", "please")
JOB_HEADING_RE = re.compile(
    r"^(?P<role>[^-()]+?)\s*[-\u2013\u2014]\s*(?P<company>.+?)"
    r"(?:\s*\((?P<dates>[^)]+)\))?\s*$"
)
TEXT_BULLET_PREFIX_RE = re.compile(r"^[\s\u200b]*[\u2022\u25cf\u25aa\u25e6\u2023\u00b7]\s*|\s*-\s+\S")
ALL_CAPS_HEADING_RE = re.compile(r"^[A-Z][A-Z &/'\-]+$")
FIRST_PERSON_CUES = re.compile(
    r"\b(i|my|me)\b.*\b(managed|handled|performed|processed|resolved|"
    r"trained|maintained|built|presented|reviewed|prepared)\b",
    re.IGNORECASE,
)
SKILL_CUE_RE = re.compile(
    r"\b(?:proficient in|skilled in|experience with|knowledge of|"
    r"familiar with)\s+(?P<skills>[^.;]+)",
    re.IGNORECASE,
)
PERCENT_RE = re.compile(r"\d+(?:\.\d+)?%")
DOLLAR_RE = re.compile(r"\$\d[\d,]*(?:\.\d+)?")
COUNT_RE = re.compile(
    r"\b(?:over|more than\s+)?(\d[\d,]*)\s+([a-z][a-z -]{2,30})", re.IGNORECASE
)

SKILL_LEXICON = {
    "excel",
    "sql",
    "crm",
    "python",
    "java",
    "microsoft office",
    "data analysis",
    "dashboards",
    "spreadsheets",
    "point-of-sale",
    "customer service",
    "communication",
    "filing systems",
}

STOPWORDS = frozenset(
    """a an and are as at be by for from has have i in is it its of on or
    our that the their them they this to was were will with""".split()
)


@lru_cache(maxsize=1)
def _load_categories() -> dict[str, list[str]]:
    with open(DATA_DIR / "categories.json", encoding="utf-8") as handle:
        return json.load(handle)


class ExtractionService:
    """Turns parsed paragraphs into structured knowledge item drafts."""

    def classify_paragraph(
        self,
        text: str,
        paragraph_info: Optional[Paragraph] = None,
    ) -> ParagraphType:
        """Classify a single paragraph using structural and textual rules."""
        stripped = text.strip()
        if not stripped:
            return ParagraphType.NORMAL_TEXT

        if paragraph_info is not None:
            if paragraph_info.is_heading:
                return (
                    ParagraphType.SOQ_QUESTION
                    if "question" in stripped.lower()
                    else ParagraphType.HEADING
                )
            if paragraph_info.is_bullet:
                # Strong interrogative text beats bullet styling (real
                # SOQs sometimes style questions as list items).
                lowered_now = stripped.lower()
                if QUESTION_PREFIX_RE.match(stripped) or re.match(
                    r"^(describe|tell us|explain|please describe)\b",
                    lowered_now,
                ):
                    return ParagraphType.SOQ_QUESTION
                return ParagraphType.RESUME_BULLET

        lowered = stripped.lower()
        if QUESTION_PREFIX_RE.match(stripped) or re.match(
            r"^(describe|tell us|explain|please describe)\b", lowered
        ):
            return ParagraphType.SOQ_QUESTION

        if self._looks_like_numbered_question(stripped):
            return ParagraphType.SOQ_QUESTION

        if TEXT_BULLET_PREFIX_RE.match(stripped):
            return ParagraphType.RESUME_BULLET

        if self._looks_like_all_caps_heading(stripped):
            return ParagraphType.HEADING

        if FIRST_PERSON_CUES.search(stripped):
            return ParagraphType.SOQ_ANSWER

        if paragraph_info is not None and not paragraph_info.is_heading:
            return ParagraphType.NORMAL_TEXT
        return ParagraphType.NORMAL_TEXT

    def extract_resume_bullets(self, paragraphs: list[Paragraph]) -> list[BulletData]:
        """Group consecutive resume bullets under their job headings."""
        groups: list[BulletData] = []
        current: Optional[BulletData] = None

        for paragraph in paragraphs:
            kind = self.classify_paragraph(paragraph.text, paragraph)
            heading_candidate = (
                kind == ParagraphType.HEADING
                or ("|" in paragraph.text and not paragraph.is_bullet)
            )
            if heading_candidate:
                heading = self.parse_job_heading(paragraph.text)
                if heading is not None:
                    current = BulletData(
                        role=heading.role,
                        company=heading.company,
                        dates=heading.dates,
                        bullets=[],
                    )
                    groups.append(current)
                continue
            if kind == ParagraphType.RESUME_BULLET:
                if current is not None:
                    cleaned = TEXT_BULLET_PREFIX_RE.sub(
                        "", paragraph.text.strip(), count=1
                    )
                    current.bullets.append(cleaned.strip() or paragraph.text.strip())

        return [group for group in groups if group.bullets]

    def parse_job_heading(self, text: str) -> Optional[ExperienceHeading]:
        """Parse job headings in several real-world formats.

        Supported shapes:
          - 'Role - Company (Dates)'
          - 'Role - Company'
          - 'Anything  |  Date range' (PDF resumes)
        """
        cleaned = text.strip()
        if "|" in cleaned:
            left, _, right = cleaned.partition("|")
            dates = right.strip() or None
            heading = self._parse_role_company(left.strip())
            if heading is not None:
                return ExperienceHeading(
                    role=heading.role,
                    company=heading.company,
                    dates=heading.dates or dates,
                )
            if left.strip():
                return ExperienceHeading(role=left.strip(), company="", dates=dates)
            return None

        return self._parse_role_company(cleaned)

    @staticmethod
    def _looks_like_all_caps_heading(text: str) -> bool:
        stripped = text.strip()
        if len(stripped) < 3 or len(stripped) > 60:
            return False
        return bool(ALL_CAPS_HEADING_RE.match(stripped))

    @staticmethod
    def _looks_like_numbered_question(text: str) -> bool:
        """Detect numbered SOQ questions like '1. Considering the attached...'."""
        if not NUMBERED_QUESTION_RE.match(text):
            return False
        if text.rstrip().endswith("?"):
            return True
        lowered = text.lower()
        return any(word in lowered for word in QUESTION_CUE_WORDS)

    @staticmethod
    def _parse_role_company(text: str) -> Optional[ExperienceHeading]:
        match = JOB_HEADING_RE.match(text)
        if match is None:
            return None
        return ExperienceHeading(
            role=match.group("role").strip(),
            company=match.group("company").strip(),
            dates=match.group("dates"),
        )

    @staticmethod
    def _is_name_heading(text: str) -> bool:
        """A bare name (no separator) is not a job heading."""
        return bool(text.strip()) and not any(
            sep in text for sep in ("-", "\u2013", "\u2014")
        )

    def extract_soq_paragraphs(self, paragraphs: list[Paragraph]) -> list[SOQData]:
        """Pair SOQ questions with their answer paragraphs.

        Runs only on documents that look like SOQs (explicit question
        paragraphs or a Statement-of-Qualifications marker), so resume
        and duty-statement imports never produce phantom Q&A pairs.
        Within an SOQ, any heading that is not a job heading — and any
        numbered line that is not a full sentence — starts a new
        answer block.
        """
        if not self._looks_like_soq_document(paragraphs):
            return []

        pairs: list[SOQData] = []
        current_question: Optional[str] = None
        answer_parts: list[str] = []

        def flush() -> None:
            nonlocal current_question, answer_parts
            if current_question is not None:
                if answer_parts:
                    pairs.append(
                        SOQData(
                            question=current_question,
                            answer=" ".join(answer_parts),
                        )
                    )
                elif len(current_question.split()) >= 25:
                    # Inline prompt+answer in one paragraph (common in
                    # finance-style SOQs): first sentence is the prompt,
                    # the remainder is the response.
                    sentences = re.split(r"(?<=[.!?])\s+", current_question)
                    if len(sentences) > 1:
                        pairs.append(
                            SOQData(
                                question=sentences[0],
                                answer=" ".join(sentences[1:]),
                            )
                        )
            current_question = None
            answer_parts = []

        for paragraph in paragraphs:
            kind = self.classify_paragraph(paragraph.text, paragraph)
            stripped = paragraph.text.strip()
            if self._starts_answer_block(stripped, kind):
                flush()
                current_question = stripped
            elif current_question is not None and kind in (
                ParagraphType.SOQ_ANSWER,
                ParagraphType.NORMAL_TEXT,
            ):
                answer_parts.append(stripped)

        flush()
        return pairs

    @staticmethod
    def _starts_answer_block(text: str, kind: ParagraphType) -> bool:
        """Decide whether a paragraph begins a new answer block."""
        if kind == ParagraphType.SOQ_QUESTION:
            return True
        if NUMBERED_QUESTION_RE.match(text) or LETTERED_ITEM_RE.match(text):
            # Any numbered/lettered line starts a block, sentence or not.
            return True
        if kind == ParagraphType.HEADING:
            # Topic headers ("High-Volume Communication and Customer
            # Service") start blocks; job headings and document titles
            # ("Statement of Qualifications") do not.
            lowered = text.strip().lower()
            if "statement of qualification" in lowered:
                return False
            return ExtractionService().parse_job_heading(text) is None
        return False

    @staticmethod
    def _looks_like_soq_document(paragraphs: list[Paragraph]) -> bool:
        markers = ("statement of qualification", "soq")
        head_text = " ".join(p.text.lower() for p in paragraphs[:6])
        if any(marker in head_text for marker in markers):
            return True
        if any(
            NUMBERED_QUESTION_RE.match(p.text.strip()) for p in paragraphs
        ):
            # Numbered-section SOQs. Duty statements also match this,
            # but their numbered lines run back-to-back with nothing to
            # capture, so pairing simply yields nothing for them.
            return True
        return any(
            ExtractionService().classify_paragraph(p.text, p)
            == ParagraphType.SOQ_QUESTION
            for p in paragraphs
        )

    def extract_skills(self, text: str) -> list[str]:
        """Extract standalone skill phrases from cue phrases and a lexicon."""
        found: list[str] = []

        for match in SKILL_CUE_RE.finditer(text):
            raw = match.group("skills")
            for phrase in re.split(r",|\band\b", raw):
                cleaned = phrase.strip().strip(".").lower()
                if cleaned:
                    found.append(cleaned)

        lowered = text.lower()
        for skill in sorted(SKILL_LEXICON, key=len, reverse=True):
            if skill in lowered and skill not in found:
                found.append(skill)

        # Deduplicate cue-captured phrases already covered by the lexicon.
        result: list[str] = []
        for candidate in found:
            if candidate not in result and len(candidate.split()) <= 4:
                result.append(candidate)
        return result

    def extract_metrics(self, text: str) -> list[MetricData]:
        """Find percentages, dollar amounts, and notable counts in text."""
        metrics: list[MetricData] = []
        seen: set[tuple[str, str]] = set()

        for pattern, kind in ((PERCENT_RE, "percent"), (DOLLAR_RE, "dollar")):
            for match in pattern.finditer(text):
                key = (match.group(0), kind)
                if key not in seen:
                    seen.add(key)
                    metrics.append(
                        MetricData(
                            value=match.group(0), kind=kind, context=self._context(text, match.start())
                        )
                    )

        for match in COUNT_RE.finditer(text):
            value, unit = match.group(1), match.group(2).strip()
            if any(stop in unit for stop in ("percent", "%")):
                continue
            key = (f"{value} {unit}", "count")
            if key in seen or int(value.replace(",", "")) < 2:
                continue
            seen.add(key)
            metrics.append(
                MetricData(
                    value=f"{value} {unit}",
                    kind="count",
                    context=self._context(text, match.start()),
                )
            )
        return metrics

    @staticmethod
    def _context(text: str, position: int, window: int = 40) -> str:
        start = max(position - window, 0)
        end = min(position + window, len(text))
        return text[start:end].strip()

    def assign_category(self, content: str, ptype: ParagraphType) -> str:
        """Assign the best-matching topic category by keyword score."""
        if ptype == ParagraphType.HEADING:
            return "General"

        lowered = content.lower()
        best_category, best_score = "General", 0
        for category, keywords in _load_categories().items():
            score = sum(lowered.count(keyword.lower()) for keyword in keywords)
            if score > best_score:
                best_category, best_score = category, score
        return best_category

    def extract_keywords(self, content: str) -> list[str]:
        """Tokenize content into lowercase keywords without stopwords."""
        tokens = re.findall(r"[a-z][a-z-]+", content.lower())
        keywords: list[str] = []
        for token in tokens:
            if token in STOPWORDS or token in keywords or len(token) < 3:
                continue
            keywords.append(token)
        return keywords
