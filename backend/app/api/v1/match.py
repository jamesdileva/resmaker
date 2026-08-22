"""Job posting matching endpoint."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import Session

from app.core.exceptions import ValidationAppError
from app.db.connection import get_session
from app.db.models import JobPosting
from app.services.matching_service import SearchResult, MatchingService

router = APIRouter(prefix="/match", tags=["match"])


class MatchRequest(BaseModel):
    """Match a job posting (or free text) against the knowledge base."""

    job_posting_id: Optional[str] = None
    query: str = ""
    item_types: list[str] = []
    top_k: int = Field(default=10, ge=1, le=100)


@router.post("/")
def match(
    payload: MatchRequest,
    session: Session = Depends(get_session),
) -> dict:
    """Return the knowledge items that best address a job posting."""
    query_text = payload.query
    if payload.job_posting_id:
        posting = session.get(JobPosting, payload.job_posting_id)
        if posting is None:
            raise HTTPException(status_code=404, detail="Job posting not found")
        query_text = " ".join(
            part for part in (posting.title, posting.raw_text) if part
        )

    if not query_text.strip():
        raise ValidationAppError("Provide a query or job_posting_id")

    service = MatchingService(session)
    results = service.match_query(
        query=query_text, limit=payload.top_k, match_all=False
    )
    return {
        "query": query_text[:200],
        "matches": [
            result.model_dump() for result in results
        ],
    }
