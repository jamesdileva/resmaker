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
from app.models.soq import BuildSoqRequest
from app.services.resume_builder import ResumeBuilderService
from app.services.soq_builder import SOQBuilderService

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


@router.post("/analyze-question")
def analyze_soq_question(payload: dict, session: Session = Depends(get_session)) -> dict:
    """Classify an SOQ question and extract its keywords."""
    from app.services.soq_analyzer import SOQAnalyzer

    question = str(payload.get("question", ""))
    if not question.strip():
        raise ValidationAppError("Question is required")
    analysis = SOQAnalyzer().analyze(question)
    return analysis.model_dump()


@router.post("/soq", response_model=BuiltDocument)
def build_soq(
    payload: BuildSoqRequest, session: Session = Depends(get_session)
) -> BuiltDocument:
    """Assemble an SOQ response from selected items within a word limit."""
    service = SOQBuilderService(session)
    return service.answer_question(
        payload.question,
        payload.selected_item_ids,
        max_words=payload.max_words,
    )


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
