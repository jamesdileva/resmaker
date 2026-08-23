"""Pydantic schemas for SOQ building."""

from typing import Optional

from pydantic import BaseModel, Field


class BuildSoqRequest(BaseModel):
    """Payload for answering an SOQ question."""

    question: str = Field(..., min_length=3)
    selected_item_ids: list[str] = []
    max_words: int = Field(default=250, ge=25, le=2000)


class BuildSoqBatchRequest(BaseModel):
    """Payload for a full multi-question SOQ document (CalCareers style).

    Each question gets its own evidence: explicit ``selections`` win when
    provided (keyed by question text); otherwise the top ``items_per_question``
    suggestions are used. Header fields follow the CalCareers requirement
    to include name, position title, and the SOQ heading.
    """

    questions: list[str] = Field(min_length=1, max_length=20)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    position_title: str = Field(min_length=1, max_length=200)
    max_words: int = Field(default=250, ge=25, le=2000)
    items_per_question: int = Field(default=5, ge=1, le=10)
    selections: Optional[dict[str, list[str]]] = None


class SOQAnalysis(BaseModel):
    """Result of analyzing an SOQ question."""

    category: str
    keywords: list[str]
    matched_patterns: Optional[list[str]] = None
