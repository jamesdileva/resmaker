"""Evidence CRUD and linking endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlmodel import Session

from app.db.connection import get_session
from app.db.models import Evidence
from app.repositories.evidence import EvidenceRepository, EvidenceWithItems

router = APIRouter(prefix="/evidence", tags=["evidence"])


class EvidenceCreate(BaseModel):
    """Payload for creating an evidence record."""

    type: str = Field(..., examples=["experience", "project", "education"])
    title: str
    content: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    company: Optional[str] = None
    role: Optional[str] = None
    source_doc_id: Optional[str] = None


class EvidenceLinkRequest(BaseModel):
    """Payload for linking a knowledge item to evidence."""

    evidence_id: str
    knowledge_item_id: str
    strength: int = Field(default=3, ge=1, le=5)


@router.get("/", response_model=list[Evidence])
def list_evidence(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    session: Session = Depends(get_session),
) -> list[Evidence]:
    """List evidence records with pagination."""
    return EvidenceRepository(session).get_multi(skip=skip, limit=limit)


@router.post(
    "/", response_model=Evidence, status_code=status.HTTP_201_CREATED
)
def create_evidence(
    payload: EvidenceCreate, session: Session = Depends(get_session)
) -> Evidence:
    """Create an evidence record."""
    return EvidenceRepository(session).create(Evidence(**payload.model_dump()))


@router.get("/{evidence_id}", response_model=EvidenceWithItems)
def get_evidence(
    evidence_id: str, session: Session = Depends(get_session)
) -> EvidenceWithItems:
    """Fetch evidence together with its linked knowledge items."""
    evidence = EvidenceRepository(session).get(evidence_id)
    if evidence is None:
        raise HTTPException(status_code=404, detail="Evidence not found")
    return evidence


@router.post("/link", status_code=status.HTTP_200_OK)
def link_evidence_to_item(
    payload: EvidenceLinkRequest, session: Session = Depends(get_session)
) -> dict:
    """Link a knowledge item to an evidence record (upsert)."""
    repo = EvidenceRepository(session)
    if repo.get(payload.evidence_id) is None:
        raise HTTPException(status_code=404, detail="Evidence not found")
    from app.repositories.knowledge_item import KnowledgeItemRepository

    if KnowledgeItemRepository(session).get(payload.knowledge_item_id) is None:
        raise HTTPException(status_code=404, detail="Knowledge item not found")
    repo.link_to_item(
        payload.evidence_id,
        payload.knowledge_item_id,
        strength=payload.strength,
    )
    return {"status": "linked"}
