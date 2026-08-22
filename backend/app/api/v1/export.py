"""Export endpoints for built documents."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import Session

from app.db.connection import get_session  # noqa: F401 - session kept for parity
from app.services.export_service import (
    DocxExporter,
    TxtExporter,
    registry,
    save_exported,
)

router = APIRouter(prefix="/export", tags=["export"])

SUPPORTED_FORMATS = {"docx", "txt"}


class ExportRequest(BaseModel):
    """Payload for exporting a built document."""

    document_id: str
    format: str = "docx"
    include_traceability: bool = True


class ExportResponse(BaseModel):
    """Export result metadata."""

    file_path: str
    file_size: int


@router.post("/", response_model=ExportResponse)
def export_document(payload: ExportRequest) -> ExportResponse:
    """Render a built document to the requested file format."""
    document = registry.get(payload.document_id)
    if document is None:
        raise HTTPException(
            status_code=404, detail=f"Unknown document: {payload.document_id}"
        )

    export_format = payload.format.lower()
    if export_format not in SUPPORTED_FORMATS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported format '{payload.format}'. "
                f"Supported formats: {sorted(SUPPORTED_FORMATS)}"
            ),
        )

    if export_format == "docx":
        content = DocxExporter().export(document, payload.include_traceability)
    else:
        content = TxtExporter().export(document, payload.include_traceability)

    return ExportResponse(**save_exported(content, export_format))
