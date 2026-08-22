"""FastAPI application entry point for Career OS."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import (
    applications_router,
    build_router,
    evidence_router,
    export_router,
    import_router,
    knowledge_router,
    match_router,
    search_router,
    validate_router,
)
from app.core.exceptions import AppError
from app.db.connection import get_engine, init_db


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Initialize the knowledge base schema on startup."""
    init_db(get_engine())
    yield


app = FastAPI(
    title="Career OS API",
    version="0.1.0",
    description="Deterministic career knowledge platform backend",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Return a structured JSON error for unhandled exceptions."""
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "path": str(request.url.path)},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Return a structured 400 for request validation failures."""
    return JSONResponse(
        status_code=400,
        content={
            "error": "Validation error",
            "details": exc.errors(),
        },
    )


app.include_router(knowledge_router, prefix="/api/v1")
app.include_router(evidence_router, prefix="/api/v1")
app.include_router(applications_router, prefix="/api/v1")
app.include_router(import_router, prefix="/api/v1")
app.include_router(build_router, prefix="/api/v1")
app.include_router(search_router, prefix="/api/v1")
app.include_router(match_router, prefix="/api/v1")
app.include_router(export_router, prefix="/api/v1")
app.include_router(validate_router, prefix="/api/v1")


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """Return structured errors for expected application failures."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.message},
    )


@app.get("/")
def root() -> dict:
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/health")
def health() -> dict:
    """Detailed health check endpoint."""
    return {"status": "healthy"}


def main() -> None:
    """Run the development server."""
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000)
