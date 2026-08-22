"""Export endpoints for built documents."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

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
    download: bool = False  # stream the file instead of returning a path


class ExportResponse(BaseModel):
    """Export result metadata."""

    file_path: str
    file_size: int


def _render(payload: ExportRequest):
    """Resolve, validate, and render an export request to bytes."""
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
        return export_format, DocxExporter().export(
            document, payload.include_traceability
        )
    return export_format, TxtExporter().export(
        document, payload.include_traceability
    )


@router.post("/", response_model=ExportResponse)
def export_document(payload: ExportRequest) -> ExportResponse:
    """Render a built document to the requested file format."""
    export_format, content = _render(payload)
    return ExportResponse(**save_exported(content, export_format))


@router.post("/download")
def download_exported_document(payload: ExportRequest) -> Response:
    """Stream the rendered file for direct browser/Electron download."""
    from fastapi.responses import FileResponse

    export_format, content = _render(payload)
    saved = save_exported(content, export_format)

    media_types = {
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "txt": "text/plain",
    }
    filename = f"career-os-export.{export_format}"
    return FileResponse(
        path=saved["file_path"],
        media_type=media_types[export_format],
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        background=None,
    )
