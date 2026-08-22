"""Pydantic schemas for the build pipeline."""

from typing import Any, Optional

from pydantic import BaseModel, Field

from app.db.models import KnowledgeItem
from app.models.resume import RenderedSection


class Suggestion(BaseModel):
    """A ranked evidence suggestion for a query."""

    knowledge_item: KnowledgeItem
    score: float
    evidence_id: Optional[str] = None


class BuiltDocument(BaseModel):
    """A deterministically assembled document ready for export."""

    document_id: str
    template_name: str
    sections: list[RenderedSection]
    traceability: dict[str, str] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)


class BuildResumeRequest(BaseModel):
    """Payload for assembling a resume."""

    item_ids: list[str]
    user_profile: dict[str, Any] = Field(default_factory=dict)
    template: str = "standard"


class SuggestRequest(BaseModel):
    """Payload for requesting evidence suggestions."""

    query: str
    item_types: list[str] = []
    min_score: float = Field(default=0.3, ge=0.0, le=1.0)
    top_k: int = Field(default=10, ge=1, le=100)
