"""Tests for the FastAPI health check endpoints and app startup."""

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


def test_root_returns_ok() -> None:
    """GET / returns the ok status payload."""
    with TestClient(app) as client:
        response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_returns_healthy() -> None:
    """GET /health returns the healthy status payload."""
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_startup_initializes_database(tmp_path: Path, monkeypatch) -> None:
    """App startup runs init_db against the configured database path."""
    db_file = tmp_path / "startup_test.db"
    monkeypatch.setenv("CAREER_OS_DB_PATH", str(db_file))
    from sqlalchemy import inspect

    from app.db.connection import get_engine

    with TestClient(app):
        pass
    assert db_file.exists()
    tables = set(inspect(get_engine(str(db_file))).get_table_names())
    assert "knowledge_items" in tables
    assert "knowledge_items_fts" in tables
