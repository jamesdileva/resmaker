"""Evidence-related pydantic schemas."""

from typing import Optional

from pydantic import BaseModel


class EvidenceDraft(BaseModel):
    """Evidence record proposed by the extraction pipeline before storage."""

    title: str
    type: str = "experience"  # "experience" | "project" | "education"
    company: Optional[str] = None
    role: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    source_doc_id: Optional[str] = None
