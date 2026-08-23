"""Build endpoints: evidence suggestions and document assembly."""

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.core.exceptions import NotFoundError, ValidationAppError
from app.db.connection import get_session
from app.models.build import (
    BuildDutyRequest,
    BuildResumeRequest,
    BuiltDocument,
    DutyPreviewRequest,
    SuggestRequest,
    Suggestion,
)
from app.models.soq import BuildSoqBatchRequest, BuildSoqRequest
from app.services.duty_statement_builder import DutyStatementBuilderService
from app.services.resume_builder import ResumeBuilderService
from app.services.soq_builder import SOQBuilderService

router = APIRouter(prefix="/build", tags=["build"])


@router.get("/past-questions")
def past_questions(session: Session = Depends(get_session)) -> list[dict]:
    """Distinct questions previously answered by imported SOQ paragraphs.

    Sourced from soq_paragraph ``metadata.question``; sorted by how many
    stored items answered each question, then alphabetically.
    """
    from sqlalchemy import select

    from app.db.models import KnowledgeItem

    counts: dict[str, int] = {}
    rows = (
        session.execute(
            select(KnowledgeItem).where(KnowledgeItem.type == "soq_paragraph")  # type: ignore[attr-defined]
        )
        .scalars()
        .all()
    )
    for item in rows:
        question = str((item.metadata_json or {}).get("question") or "").strip()
        if question:
            counts[question] = counts.get(question, 0) + 1
    ordered = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return [
        {"question": question, "times_answered": count}
        for question, count in ordered
    ]


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


@router.post("/soq-batch", response_model=BuiltDocument)
def build_soq_batch(
    payload: BuildSoqBatchRequest, session: Session = Depends(get_session)
) -> BuiltDocument:
    """Assemble a full multi-question SOQ document with a CalCareers header."""
    service = SOQBuilderService(session)
    return service.answer_questions_batch(
        payload.questions,
        first_name=payload.first_name,
        last_name=payload.last_name,
        position_title=payload.position_title,
        max_words=payload.max_words,
        items_per_question=payload.items_per_question,
        selections=payload.selections,
    )


@router.post("/duty-preview")
def preview_duties(
    payload: DutyPreviewRequest, session: Session = Depends(get_session)
) -> dict:
    """Parse posting text into duty requirements without building."""
    from app.models.duty import DutyRequirement
    from app.services.duty_statement_parser import DutyStatementParser

    duties: list[DutyRequirement] = DutyStatementParser().parse(payload.raw_text)
    return {"requirements": [d.model_dump() for d in duties]}


@router.post("/duty-statement", response_model=BuiltDocument)
def build_duty_statement(
    payload: BuildDutyRequest, session: Session = Depends(get_session)
) -> BuiltDocument:
    """Generate an evidence-backed response for each duty in a posting."""
    if not payload.job_posting_id and not payload.raw_text:
        raise ValidationAppError("Provide job_posting_id or raw_text")
    service = DutyStatementBuilderService(session)
    return service.generate_response(
        job_posting_id=payload.job_posting_id,
        raw_text=payload.raw_text,
        selected_item_ids=payload.selected_item_ids,
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
