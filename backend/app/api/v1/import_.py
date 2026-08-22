"""Import endpoints: upload documents and track processing status."""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlmodel import Session

from app.core.exceptions import ImportFailedError
from app.db.connection import get_session
from app.models.document import ImportResponse, ImportStatusResponse
from app.services.import_service import (
    SUPPORTED_TYPES,
    ImportService,
    save_upload_to_temp,
)

router = APIRouter(prefix="/import", tags=["import"])

MAX_UPLOAD_BYTES = 50 * 1024 * 1024

# In-memory job registry; imports are synchronous in the MVP.
_jobs: dict[str, dict] = {}


@router.post("/", response_model=ImportResponse)
def import_document(
    file: UploadFile = File(...),
    file_type: Optional[str] = Form(default=None),
    session: Session = Depends(get_session),
) -> ImportResponse:
    """Upload and process a DOCX/PDF/TXT career document."""
    extension = (file_type or (file.filename or "").rsplit(".", 1)[-1]).lower()
    if extension not in SUPPORTED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{extension}'. "
            f"Allowed: {sorted(SUPPORTED_TYPES)}",
        )

    data = file.file.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail="File exceeds 50MB limit")
    if not data:
        raise HTTPException(status_code=400, detail="Empty upload")

    job_id = f"IMP-{uuid.uuid4().hex[:8]}"
    _jobs[job_id] = {"status": "processing", "source_doc_id": None}

    temp_path = save_upload_to_temp(data, f".{extension}")
    try:
        service = ImportService(session)
        source_doc = service.process_upload(
            temp_path,
            filename=file.filename,
            file_type=file_type or extension,
        )
        items_created = _count_items(session, source_doc.id)
        _jobs[job_id].update(
            {
                "status": "completed",
                "source_doc_id": source_doc.id,
                "items_created": items_created,
            }
        )
        return ImportResponse(
            job_id=job_id,
            status="completed",
            source_doc_id=source_doc.id,
            items_created=items_created,
        )
    except Exception as exc:  # noqa: BLE001 - report any processing failure
        _jobs[job_id].update({"status": "failed", "error": str(exc)})
        raise ImportFailedError(f"Import failed: {exc}") from exc
    finally:
        from pathlib import Path

        Path(temp_path).unlink(missing_ok=True)


@router.get("/status/{job_id}", response_model=ImportStatusResponse)
def import_status(job_id: str) -> ImportStatusResponse:
    """Return the current state of an import job."""
    record = _jobs.get(job_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Unknown import job")
    return ImportStatusResponse(
        job_id=job_id,
        status=record["status"],
        source_doc_id=record.get("source_doc_id"),
        items_created=record.get("items_created", 0),
        error=record.get("error"),
    )


def _count_items(session: Session, source_doc_id: str) -> int:
    from sqlalchemy import func, select

    from app.db.models import KnowledgeItem

    stmt = (
        select(func.count())
        .select_from(KnowledgeItem)
        .where(KnowledgeItem.source_doc_id == source_doc_id)
    )
    return session.execute(stmt).scalar_one()
