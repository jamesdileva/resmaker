"""Knowledge-related pydantic schemas for the extraction pipeline."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel


class ParagraphType(str, Enum):
    """Classification of a parsed paragraph."""

    HEADING = "heading"
    RESUME_BULLET = "resume_bullet"
    SOQ_QUESTION = "soq_question"
    SOQ_ANSWER = "soq_answer"
    NORMAL_TEXT = "normal_text"


class ExperienceHeading(BaseModel):
    """A job heading like 'Role - Company (2019-2022)'."""

    role: str
    company: str
    dates: Optional[str] = None


class BulletData(BaseModel):
    """Resume bullets grouped under their job heading."""

    role: str
    company: str
    dates: Optional[str] = None
    bullets: list[str]


class SOQData(BaseModel):
    """An SOQ question paired with its answer text."""

    question: str
    answer: str


class MetricData(BaseModel):
    """A quantitative achievement found in text."""

    value: str
    kind: str  # "percent" | "dollar" | "count"
    context: str
