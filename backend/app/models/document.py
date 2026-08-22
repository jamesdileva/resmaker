"""Pydantic schemas for import requests and responses."""

from typing import Optional

from pydantic import BaseModel


class ImportResponse(BaseModel):
    """Response for a submitted import job."""

    job_id: str
    status: str  # "processing" | "completed" | "failed"
    source_doc_id: Optional[str] = None
    items_created: int = 0
    items_skipped: int = 0
    error: Optional[str] = None


class ImportStatusResponse(BaseModel):
    """Status of an import job."""

    job_id: str
    status: str
    source_doc_id: Optional[str] = None
    items_created: int = 0
    items_skipped: int = 0
    error: Optional[str] = None
