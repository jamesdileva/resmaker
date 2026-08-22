"""Versioned API routers."""

from app.api.v1.applications import router as applications_router
from app.api.v1.evidence import router as evidence_router
from app.api.v1.knowledge import router as knowledge_router

__all__ = ["applications_router", "evidence_router", "knowledge_router"]
