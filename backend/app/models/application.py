"""Pydantic schemas for application tracking."""

from typing import Literal, Optional

from pydantic import BaseModel, Field


class EvidenceUsageEntry(BaseModel):
    """One knowledge item's usage within an application."""

    knowledge_item_id: str
    used_in_resume: bool = False
    used_in_soq: bool = False
    used_in_duty: bool = False


class ApplicationResultRequest(BaseModel):
    """Update an application outcome and optionally record evidence usage."""

    status: Literal["applied", "interview", "offer", "rejected"]
    evidence_usage: list[EvidenceUsageEntry] = Field(default_factory=list)
    notes: Optional[str] = None
