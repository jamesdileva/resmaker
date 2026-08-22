"""Pydantic schemas for SOQ building."""

from typing import Optional

from pydantic import BaseModel, Field


class BuildSoqRequest(BaseModel):
    """Payload for answering an SOQ question."""

    question: str = Field(..., min_length=3)
    selected_item_ids: list[str] = []
    max_words: int = Field(default=250, ge=25, le=2000)


class SOQAnalysis(BaseModel):
    """Result of analyzing an SOQ question."""

    category: str
    keywords: list[str]
    matched_patterns: Optional[list[str]] = None
