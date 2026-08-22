"""Application tracking endpoints."""

from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlmodel import Session, select

from app.db.connection import get_session
from app.db.models import Application, JobPosting
from app.models.application import ApplicationResultRequest
from app.repositories.application import ApplicationRepository

router = APIRouter(prefix="/applications", tags=["applications"])


class ApplicationCreate(BaseModel):
    """Payload for creating an application."""

    job_posting_id: str


@router.get("/", response_model=list[Application])
def list_applications(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    session: Session = Depends(get_session),
) -> list[Application]:
    """List applications with pagination."""
    stmt = select(Application).offset(skip).limit(limit).order_by(Application.applied_at)
    return list(session.exec(stmt))


@router.post(
    "/", response_model=Application, status_code=status.HTTP_201_CREATED
)
def create_application(
    payload: ApplicationCreate, session: Session = Depends(get_session)
) -> Application:
    """Create an application for an existing job posting."""
    posting = session.get(JobPosting, payload.job_posting_id)
    if posting is None:
        raise HTTPException(status_code=404, detail="Job posting not found")
    return ApplicationRepository(session).create(
        Application(job_posting_id=payload.job_posting_id)
    )


@router.get("/{application_id}", response_model=Application)
def get_application(
    application_id: str, session: Session = Depends(get_session)
) -> Application:
    """Fetch a single application."""
    app = ApplicationRepository(session).get(application_id)
    if app is None:
        raise HTTPException(status_code=404, detail="Application not found")
    return app


@router.post("/{application_id}/result", response_model=Application)
def update_application_result(
    application_id: str,
    payload: ApplicationResultRequest,
    session: Session = Depends(get_session),
) -> Application:
    """Update an application's outcome and record evidence usage."""
    repo = ApplicationRepository(session)
    updated = repo.update_result(application_id, payload.status)
    if updated is None:
        raise HTTPException(status_code=404, detail="Application not found")

    for usage in payload.evidence_usage:
        repo.record_evidence_usage(
            application_id,
            usage.knowledge_item_id,
            used_in_resume=usage.used_in_resume,
            used_in_soq=usage.used_in_soq,
            used_in_duty=usage.used_in_duty,
            result=payload.status if payload.status != "applied" else None,
        )
    return updated
