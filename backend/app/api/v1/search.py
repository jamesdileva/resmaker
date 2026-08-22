"""Evidence Explorer search endpoint."""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlmodel import Session

from app.db.connection import get_session
from app.services.matching_service import MatchingService, SearchResult

router = APIRouter(prefix="/search", tags=["search"])


class SearchRequest(BaseModel):
    """Payload for the Evidence Explorer search."""

    query: str = ""
    item_types: list[str] = []
    categories: list[str] = []
    min_star_rating: int = Field(default=0, ge=0, le=5)
    sort_by: str = "relevance"  # "relevance" | "date"
    limit: int = Field(default=50, ge=1, le=200)


class SearchResponse(BaseModel):
    """Ranked results with provenance info."""

    items: list[SearchResult]
    total: int


@router.post("/", response_model=SearchResponse)
def search(
    payload: SearchRequest,
    session: Session = Depends(get_session),
) -> SearchResponse:
    """Search the knowledge base with filters and star ratings."""
    service = MatchingService(session)
    items = service.match_query(
        query=payload.query,
        item_types=payload.item_types or None,
        categories=payload.categories or None,
        min_star_rating=payload.min_star_rating,
        sort_by=payload.sort_by,
        limit=payload.limit,
    )
    return SearchResponse(items=items, total=len(items))
