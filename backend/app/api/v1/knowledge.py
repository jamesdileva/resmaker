"""Knowledge item CRUD and search endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlmodel import Session

from app.db.connection import get_session
from app.db.models import KnowledgeItem
from app.repositories.knowledge_item import KnowledgeItemRepository, MatchResult

router = APIRouter(prefix="/knowledge-items", tags=["knowledge-items"])


class KnowledgeItemCreate(BaseModel):
    """Payload for creating a knowledge item."""

    type: str = Field(..., examples=["resume_bullet", "soq_paragraph"])
    title: Optional[str] = None
    content: str
    category: Optional[str] = None
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    source_doc_id: Optional[str] = None


class KnowledgeItemUpdate(BaseModel):
    """Payload for partially updating a knowledge item."""

    type: Optional[str] = None
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class KnowledgeItemListResponse(BaseModel):
    """Paginated knowledge item list with total count."""

    items: list[KnowledgeItem]
    total: int


@router.get("/", response_model=KnowledgeItemListResponse)
def list_knowledge_items(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    type: Optional[str] = None,
    category: Optional[str] = None,
    session: Session = Depends(get_session),
) -> KnowledgeItemListResponse:
    """List knowledge items with pagination and optional filters."""
    repo = KnowledgeItemRepository(session)
    items = repo.get_multi(skip=skip, limit=limit, type=type, category=category)
    return KnowledgeItemListResponse(
        items=items, total=repo.count(type=type, category=category)
    )


@router.get("/search", response_model=list[MatchResult])
def search_knowledge_items(
    q: str,
    min_score: float = Query(0.3, ge=0.0, le=1.0),
    session: Session = Depends(get_session),
) -> list[MatchResult]:
    """Full-text search across the knowledge base."""
    return KnowledgeItemRepository(session).search(q, min_score=min_score)


@router.post(
    "/", response_model=KnowledgeItem, status_code=status.HTTP_201_CREATED
)
def create_knowledge_item(
    payload: KnowledgeItemCreate, session: Session = Depends(get_session)
) -> KnowledgeItem:
    """Create a knowledge item."""
    return KnowledgeItemRepository(session).create(KnowledgeItem(**payload.model_dump()))


@router.get("/{item_id}", response_model=KnowledgeItem)
def get_knowledge_item(
    item_id: str, session: Session = Depends(get_session)
) -> KnowledgeItem:
    """Fetch a single knowledge item."""
    item = KnowledgeItemRepository(session).get(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Knowledge item not found")
    return item


@router.get("/{item_id}/provenance")
def get_item_provenance(
    item_id: str, session: Session = Depends(get_session)
) -> dict:
    """Full trace info: source document, linked evidence, usage history."""
    from app.services.matching_service import MatchingService

    provenance = MatchingService(session).get_provenance(item_id)
    if provenance is None:
        raise HTTPException(status_code=404, detail="Knowledge item not found")
    item = provenance["knowledge_item"]
    provenance["knowledge_item"] = KnowledgeItem.model_validate(
        item, from_attributes=True
    )
    return provenance


@router.put("/{item_id}", response_model=KnowledgeItem)
def update_knowledge_item(
    item_id: str,
    payload: KnowledgeItemUpdate,
    session: Session = Depends(get_session),
) -> KnowledgeItem:
    """Update mutable fields of a knowledge item."""
    data = payload.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(status_code=400, detail="No fields to update")
    updated = KnowledgeItemRepository(session).update(item_id, data)
    if updated is None:
        raise HTTPException(status_code=404, detail="Knowledge item not found")
    return updated


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_knowledge_item(
    item_id: str, session: Session = Depends(get_session)
) -> None:
    """Delete a knowledge item."""
    if not KnowledgeItemRepository(session).delete(item_id):
        raise HTTPException(status_code=404, detail="Knowledge item not found")
