"""FastAPI application entry point for Career OS."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

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
