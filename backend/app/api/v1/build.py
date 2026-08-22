"""Build endpoints: evidence suggestions and document assembly."""

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.core.exceptions import NotFoundError, ValidationAppError
from app.db.connection import get_session
from app.models.build import (
    BuildResumeRequest,
    BuiltDocument,
    SuggestRequest,
    Suggestion,
)
from app.services.resume_builder import ResumeBuilderService

router = APIRouter(prefix="/build", tags=["build"])


@router.post("/suggest", response_model=list[Suggestion])
def suggest_evidence(
    payload: SuggestRequest, session: Session = Depends(get_session)
) -> list[Suggestion]:
    """Return ranked knowledge-item suggestions for a query."""
    service = ResumeBuilderService(session)
    return service.suggest_items(
        payload.query,
        item_types=payload.item_types or None,
        min_score=payload.min_score,
        top_k=payload.top_k,
    )


@router.post("/resume", response_model=BuiltDocument)
def build_resume(
    payload: BuildResumeRequest, session: Session = Depends(get_session)
) -> BuiltDocument:
    """Assemble a resume from the selected knowledge items."""
    service = ResumeBuilderService(session)
    try:
        return service.build_resume(
            payload.item_ids,
            user_profile=payload.user_profile,
            template=payload.template,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/auto-resume", response_model=BuiltDocument)
def auto_build_resume(
    job_posting_id: str, session: Session = Depends(get_session)
) -> BuiltDocument:
    """Auto-select best-matching evidence for a posting and build a resume."""
    service = ResumeBuilderService(session)
    try:
        return service.auto_build_resume(job_posting_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
