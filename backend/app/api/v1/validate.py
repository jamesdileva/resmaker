"""Validation endpoint for built documents."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.export_service import registry
from app.services.validation_service import (
    SOQ_DEFAULT_MAX_WORDS,
    DOC_TYPES,
    ValidationService,
)

router = APIRouter(prefix="/validate", tags=["validate"])


class ValidateRequest(BaseModel):
    """Payload for validating a built document."""

    document_id: str
    doc_type: str = "resume"
    keywords: list[str] = Field(default_factory=list)
    soq_max_words: int = Field(default=SOQ_DEFAULT_MAX_WORDS, ge=25, le=2000)


@router.post("/")
def validate_document(payload: ValidateRequest) -> dict:
    """Run the validation engine over a built document."""
    if payload.doc_type.lower() not in DOC_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown doc_type '{payload.doc_type}'. "
            f"Expected one of {sorted(DOC_TYPES)}",
        )

    document = registry.get(payload.document_id)
    if document is None:
        raise HTTPException(
            status_code=404, detail=f"Unknown document: {payload.document_id}"
        )

    result = ValidationService().validate(
        document,
        doc_type=payload.doc_type,
        keywords=payload.keywords or None,
        soq_max_words=payload.soq_max_words,
    )
    return result.model_dump()
