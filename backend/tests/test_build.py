"""Tests for the resume builder service and build API (Sprint 14)."""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.exceptions import NotFoundError, ValidationAppError
from app.db.models import Evidence, JobPosting, KnowledgeItem, KnowledgeItemEvidenceLink
from app.services.resume_builder import ResumeBuilderService

PROFILE = {"name": "John Doe", "email": "john@example.com"}


def _seed_job(session: Session) -> tuple[Evidence, list[KnowledgeItem]]:
    evidence = Evidence(
        type="experience",
        title="Boost Mobile",
        content="retail work",
        role="Sales Associate",
        company="Boost Mobile",
    )
    items = [
        KnowledgeItem(
            type="resume_bullet",
            content="Handled confidential customer records daily",
            category="Confidential Information",
        ),
        KnowledgeItem(
            type="resume_bullet",
            content="Resolved customer complaints with a 95% satisfaction rating",
            category="Customer Service",
        ),
        KnowledgeItem(type="skill", content="Excel"),
    ]
    session.add(evidence)
    session.flush()
    for item in items:
        session.add(item)
        session.flush()
        if item.type == "resume_bullet":
            session.add(
                KnowledgeItemEvidenceLink(
                    knowledge_item_id=item.id,
                    evidence_id=evidence.id,
                )
            )
    session.commit()
    return evidence, items


@pytest.fixture()
def seeded(session: Session):
    return _seed_job(session)


# --- ResumeBuilderService ---


def test_build_resume_returns_sections_and_traceability(
    session: Session, seeded
) -> None:
    evidence, items = seeded
    bullet_ids = [i.id for i in items if i.type == "resume_bullet"]

    service = ResumeBuilderService(session)
    document = service.build_resume(bullet_ids, PROFILE)

    assert document.document_id
    assert document.template_name == "standard"
    section_types = [s.section_type for s in document.sections]
    assert "experience" in section_types
    assert "profile" in section_types

    experience = next(s for s in document.sections if s.section_type == "experience")
    assert experience.groups[0].title == "Sales Associate"
    total_bullets = sum(len(g.bullets) for g in experience.groups)
    assert total_bullets == 2

    assert set(document.traceability.keys()) == set(bullet_ids)
    assert all(v == evidence.id for v in document.traceability.values())


def test_build_resume_skips_unknown_items(session: Session, seeded) -> None:
    _, items = seeded
    service = ResumeBuilderService(session)
    document = service.build_resume([items[0].id, "missing-id"], {})
    experience = next(s for s in document.sections if s.section_type == "experience")
    assert sum(len(g.bullets) for g in experience.groups) == 1


def test_build_resume_no_valid_items_raises(session: Session, seeded) -> None:
    with pytest.raises(ValidationAppError):
        ResumeBuilderService(session).build_resume(["missing-1", "missing-2"], {})


def test_build_resume_unknown_template_raises(session: Session, seeded) -> None:
    _, items = seeded
    with pytest.raises(ValueError):
        ResumeBuilderService(session).build_resume(
            [items[0].id], {}, template="nope"
        )


def test_suggest_items_ranks_and_filters(session: Session, seeded) -> None:
    service = ResumeBuilderService(session)
    suggestions = service.suggest_items("confidential records")

    assert len(suggestions) >= 1
    scores = [s.score for s in suggestions]
    assert scores == sorted(scores, reverse=True)
    top = suggestions[0]
    assert "confidential" in top.knowledge_item.content.lower()

    typed = service.suggest_items("excel", item_types=["resume_bullet"])
    assert all(s.knowledge_item.type == "resume_bullet" for s in typed)


def test_auto_build_resume_from_posting(session: Session, seeded) -> None:
    posting = JobPosting(
        title="Customer Service Rep",
        raw_text="Handle confidential records and resolve customer complaints",
    )
    session.add(posting)
    session.commit()

    document = ResumeBuilderService(session).auto_build_resume(posting.id)
    experience = next(s for s in document.sections if s.section_type == "experience")
    assert sum(len(g.bullets) for g in experience.groups) >= 1
    assert document.traceability


def test_auto_build_missing_posting_raises(session: Session, seeded) -> None:
    with pytest.raises(NotFoundError):
        ResumeBuilderService(session).auto_build_resume("missing-posting")


# --- Build API ---


@pytest.fixture()
def api_seeded(client, api_session: Session):
    """Seed data into the same database the API client talks to."""
    return _seed_job(api_session)


def test_suggest_endpoint(client, api_seeded) -> None:
    response = client.post(
        "/api/v1/build/suggest",
        json={"query": "confidential", "top_k": 5},
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body) >= 1
    assert body[0]["knowledge_item"]["type"] == "resume_bullet"
    assert 0.0 <= body[0]["score"] <= 1.0


def test_build_resume_endpoint(client, api_seeded) -> None:
    _, items = api_seeded
    bullet_ids = [i.id for i in items if i.type == "resume_bullet"]

    response = client.post(
        "/api/v1/build/resume",
        json={"item_ids": bullet_ids, "user_profile": PROFILE},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["document_id"]
    assert body["template_name"] == "standard"
    types = [s["section_type"] for s in body["sections"]]
    assert "profile" in types and "experience" in types
    assert set(body["traceability"].keys()) == set(bullet_ids)


def test_build_resume_endpoint_validation_error(client) -> None:
    response = client.post("/api/v1/build/resume", json={"item_ids": ["missing"]})
    assert response.status_code == 400
    assert "error" in response.json() or "detail" in response.json()


def test_auto_resume_endpoint_404_for_unknown_posting(client) -> None:
    params = {"job_posting_id": "missing"}
    response = client.post("/api/v1/build/auto-resume", params=params)
    assert response.status_code == 404
