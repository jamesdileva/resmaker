"""Tests for the v1 API CRUD endpoints (Sprint 4)."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.db.models import JobPosting


@pytest.fixture()
def client(tmp_path: Path, monkeypatch):
    """TestClient over an app bound to a fresh temp database."""
    monkeypatch.setenv("CAREER_OS_DB_PATH", str(tmp_path / "api_test.db"))
    from app.main import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def job_posting(client) -> JobPosting:
    """Insert a job posting directly for application FK tests."""
    from app.db.connection import get_engine
    from sqlmodel import Session

    posting = JobPosting(title="Analyst", raw_text="duties")
    with Session(get_engine()) as session:
        session.add(posting)
        session.commit()
        session.refresh(posting)
    return posting


# --- Knowledge items ---


def test_create_and_get_knowledge_item(client) -> None:
    response = client.post(
        "/api/v1/knowledge-items/",
        json={"type": "resume_bullet", "content": "Led a team of five"},
    )
    assert response.status_code == 201
    created = response.json()
    assert created["id"]

    fetched = client.get(f"/api/v1/knowledge-items/{created['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["content"] == "Led a team of five"


def test_create_knowledge_item_validation_error(client) -> None:
    response = client.post("/api/v1/knowledge-items/", json={"type": "bullet"})
    assert response.status_code == 400
    body = response.json()
    assert body["error"] == "Validation error"


def test_get_missing_knowledge_item_returns_404(client) -> None:
    assert client.get("/api/v1/knowledge-items/nope").status_code == 404


def test_list_knowledge_items_with_filters(client) -> None:
    for i in range(3):
        client.post(
            "/api/v1/knowledge-items/",
            json={"type": "soq_paragraph", "content": f"answer {i}"},
        )
    client.post(
        "/api/v1/knowledge-items/",
        json={"type": "resume_bullet", "content": "a bullet"},
    )

    listed = client.get("/api/v1/knowledge-items/?limit=10")
    assert listed.status_code == 200
    body = listed.json()
    assert body["total"] == 4
    assert len(body["items"]) == 4

    filtered = client.get(
        "/api/v1/knowledge-items/", params={"type": "soq_paragraph"}
    )
    assert filtered.json()["total"] == 3


def test_update_knowledge_item(client) -> None:
    created = client.post(
        "/api/v1/knowledge-items/",
        json={"type": "skill", "content": "SQL"},
    ).json()

    updated = client.put(
        f"/api/v1/knowledge-items/{created['id']}",
        json={"title": "Database skills"},
    )
    assert updated.status_code == 200
    assert updated.json()["title"] == "Database skills"
    assert updated.json()["content"] == "SQL"

    missing = client.put(
        "/api/v1/knowledge-items/missing", json={"title": "x"}
    )
    assert missing.status_code == 404

    empty = client.put(f"/api/v1/knowledge-items/{created['id']}", json={})
    assert empty.status_code == 400


def test_delete_knowledge_item(client) -> None:
    created = client.post(
        "/api/v1/knowledge-items/",
        json={"type": "metric", "content": "20% growth"},
    ).json()

    deleted = client.delete(f"/api/v1/knowledge-items/{created['id']}")
    assert deleted.status_code == 204
    assert client.get(f"/api/v1/knowledge-items/{created['id']}").status_code == 404
    repeat = client.delete(f"/api/v1/knowledge-items/{created['id']}")
    assert repeat.status_code == 404


def test_search_endpoint(client) -> None:
    client.post(
        "/api/v1/knowledge-items/",
        json={
            "type": "soq_paragraph",
            "content": "Managed confidential records and privacy compliance",
        },
    )
    results = client.get(
        "/api/v1/knowledge-items/search", params={"q": "confidential"}
    )
    assert results.status_code == 200
    body = results.json()
    assert len(body) >= 1
    assert 0.0 < body[0]["score"] <= 1.0
    assert "knowledge_item" in body[0]


# --- Evidence ---


def _create_evidence(client) -> dict:
    response = client.post(
        "/api/v1/evidence/",
        json={"type": "experience", "title": "Boost Mobile", "content": "Retail"},
    )
    assert response.status_code == 201
    return response.json()


def test_evidence_crud_flow(client) -> None:
    evidence = _create_evidence(client)

    listed = client.get("/api/v1/evidence/")
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    fetched = client.get(f"/evidence/{evidence['id']}")
    if fetched.status_code == 404:
        fetched = client.get(f"/api/v1/evidence/{evidence['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["items"] == []
    assert client.get("/api/v1/evidence/missing").status_code == 404


def test_evidence_link_requires_both_records(client) -> None:
    evidence = _create_evidence(client)
    item = client.post(
        "/api/v1/knowledge-items/",
        json={"type": "resume_bullet", "content": "Sold plans"},
    ).json()

    linked = client.post(
        "/api/v1/evidence/link",
        json={
            "evidence_id": evidence["id"],
            "knowledge_item_id": item["id"],
            "strength": 4,
        },
    )
    assert linked.status_code == 200

    fetched = client.get(f"/api/v1/evidence/{evidence['id']}").json()
    assert [i["id"] for i in fetched["items"]] == [item["id"]]

    bad_link = client.post(
        "/api/v1/evidence/link",
        json={"evidence_id": evidence["id"], "knowledge_item_id": "missing"},
    )
    assert bad_link.status_code == 404


# --- Applications ---


def test_application_flow(client, job_posting) -> None:
    created = client.post(
        "/api/v1/applications/", json={"job_posting_id": job_posting.id}
    )
    assert created.status_code == 201
    app_id = created.json()["id"]
    assert created.json()["status"] == "applied"

    listed = client.get("/api/v1/applications/")
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    result = client.post(
        f"/api/v1/applications/{app_id}/result", json={"status": "interview"}
    )
    assert result.status_code == 200
    assert result.json()["status"] == "interview"
    assert client.get(f"/api/v1/applications/{app_id}").json()["status"] == (
        "interview"
    )


def test_application_invalid_job_posting_404(client) -> None:
    response = client.post(
        "/api/v1/applications/", json={"job_posting_id": "missing-posting"}
    )
    assert response.status_code == 404


def test_application_result_validation(client, job_posting) -> None:
    app_id = client.post(
        "/api/v1/applications/", json={"job_posting_id": job_posting.id}
    ).json()["id"]

    bad_status = client.post(
        f"/api/v1/applications/{app_id}/result", json={"status": "ghosted"}
    )
    assert bad_status.status_code == 400

    missing = client.post(
        "/api/v1/applications/missing/result", json={"status": "offer"}
    )
    assert missing.status_code == 404


def test_swagger_lists_all_endpoints(client) -> None:
    openapi = client.get("/openapi.json").json()
    paths = openapi["paths"]
    expected = [
        "/api/v1/knowledge-items/",
        "/api/v1/knowledge-items/search",
        "/api/v1/knowledge-items/{item_id}",
        "/api/v1/evidence/",
        "/api/v1/evidence/{evidence_id}",
        "/api/v1/evidence/link",
        "/api/v1/applications/",
        "/api/v1/applications/{application_id}",
        "/api/v1/applications/{application_id}/result",
    ]
    for path in expected:
        assert path in paths, f"missing {path}"
