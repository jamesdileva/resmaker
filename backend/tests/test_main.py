"""Tests for the FastAPI health check endpoints."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_returns_ok() -> None:
    """GET / returns the ok status payload."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_returns_healthy() -> None:
    """GET /health returns the healthy status payload."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
