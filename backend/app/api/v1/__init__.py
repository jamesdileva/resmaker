"""Versioned API routers."""

from app.api.v1.applications import router as applications_router
from app.api.v1.build import router as build_router
from app.api.v1.evidence import router as evidence_router
from app.api.v1.export import router as export_router
from app.api.v1.import_ import router as import_router
from app.api.v1.knowledge import router as knowledge_router
from app.api.v1.llm import router as llm_router
from app.api.v1.match import router as match_router
from app.api.v1.search import router as search_router
from app.api.v1.validate import router as validate_router

__all__ = [
    "applications_router",
    "build_router",
    "evidence_router",
    "export_router",
    "import_router",
    "knowledge_router",
    "llm_router",
    "match_router",
    "search_router",
    "validate_router",
]
