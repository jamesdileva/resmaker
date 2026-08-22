"""Versioned API routers."""

from app.api.v1.applications import router as applications_router
from app.api.v1.build import router as build_router
from app.api.v1.evidence import router as evidence_router
from app.api.v1.import_ import router as import_router
from app.api.v1.knowledge import router as knowledge_router

__all__ = [
    "applications_router",
    "build_router",
    "evidence_router",
    "import_router",
    "knowledge_router",
]
