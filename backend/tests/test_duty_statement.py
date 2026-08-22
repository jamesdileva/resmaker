"""Tests for the duty statement builder service and endpoint (Sprint 20)."""

import pytest
from sqlmodel import Session

from app.core.exceptions import NotFoundError, ValidationAppError
from app.db.models import Evidence, JobPosting, KnowledgeItem, KnowledgeItemEvidenceLink
from app.services.duty_statement_builder import DutyStatementBuilderService


def _seed(session: Session):
    """Two distinct evidence records with matching bullets."""
    retail = Evidence(
        type="experience",
        title="Boost Mobile",
        content="retail",
        role="Sales Associate",
        company="Boost Mobile",
    )
    office = Evidence(
        type="experience",
        title="County Office",
        content="clerical",
        role="Data Entry Clerk",
        company="County Office",
    )
    session.add_all([retail, office])
    session.flush()

    items = [
        KnowledgeItem(
            type="resume_bullet",
            content=(
                "Resolved an average of 20+ customer complaints and "
                "disputes daily while maintaining satisfaction ratings"
            ),
        ),
        KnowledgeItem(
            type="resume_bullet",
            content=(
                "Maintained organized confidential records and filing "
                "systems ensuring documents were retrievable"
            ),
        ),
    ]
    links = []
    for item, evidence in zip(items, [retail, office]):
        session.add(item)
        session.flush()
        link = KnowledgeItemEvidenceLink(
            knowledge_item_id=item.id, evidence_id=evidence.id
        )
        session.add(link)
        links.append(link)
    session.commit()
    return items


def _posting(session: Session, raw_text: str) -> JobPosting:
    posting = JobPosting(title="Test Role", raw_text=raw_text)
    session.add(posting)
    session.commit()
    return posting


NUMBERED_DUTIES = """Duties:
1. Resolve customer complaints and disputes in a fast-paced environment.
2. Maintain confidential records and filing systems with accuracy.
"""


@pytest.fixture()
def seeded(session: Session):
    return _seed(session)


# --- suggest_items ---


def test_suggest_items_ranks_for_duty_text(session: Session, seeded) -> None:
    service = DutyStatementBuilderService(session)
    suggestions = service.suggest_items("Resolve customer complaints daily")
    assert len(suggestions) >= 1
    assert "complaints" in suggestions[0].knowledge_item.content.lower()


def test_suggest_respects_min_score_floor(session: Session, seeded) -> None:
    service = DutyStatementBuilderService(session)
    unrelated = service.suggest_items("quantum chromodynamics particle physics")
    assert all(s.score >= service.MIN_DUTY_MATCH_SCORE for s in unrelated)


# --- generate_response ---


def test_generate_response_one_group_per_duty(session: Session, seeded) -> None:
    items = seeded
    posting = _posting(session, NUMBERED_DUTIES)

    document = DutyStatementBuilderService(session).generate_response(
        posting.id, [item.id for item in items]
    )

    assert document.document_id
    assert document.template_name == "duty_standard"
    section = document.sections[0]
    assert section.section_type == "duty_response"
    assert len(section.groups) == 2

    first, second = section.groups
    assert first.title.startswith("Duty 1:")
    assert "complaints" in first.bullets[0].lower()
    assert "records" in second.bullets[0].lower() or "filing" in second.bullets[0].lower()

    # Distinct evidence per duty where available.
    assert first.evidence_id != second.evidence_id

    # Traceability covers every cited item.
    assert len(document.traceability) == len(section.groups)
    assert set(document.traceability.values()) == {
        first.evidence_id,
        second.evidence_id,
    }


def test_generate_response_warns_for_unmatched_duty(session: Session, seeded) -> None:
    items = seeded
    posting = _posting(
        session,
        """Duties:
1. Resolve customer complaints and disputes in a fast-paced environment.
2. Perform advanced aerospace engineering analysis of propulsion systems.
""",
    )
    document = DutyStatementBuilderService(session).generate_response(
        posting.id, [items[0].id]
    )
    assert any("duty 2" in w.lower() for w in document.warnings)
    # Only the matched duty produced a group.
    assert len(document.sections[0].groups) == 1


def test_missing_posting_raises(session: Session, seeded) -> None:
    with pytest.raises(NotFoundError):
        DutyStatementBuilderService(session).generate_response("missing", [])


def test_no_duties_in_posting_raises(session: Session, seeded) -> None:
    posting = _posting(session, "A short blurb.")
    with pytest.raises(ValidationAppError):
        DutyStatementBuilderService(session).generate_response(
            posting.id, [seeded[0].id]
        )


def test_invalid_items_raise(session: Session, seeded) -> None:
    posting = _posting(session, NUMBERED_DUTIES)
    with pytest.raises(ValidationAppError):
        DutyStatementBuilderService(session).generate_response(posting.id, ["nope"])


# --- API ---


def test_duty_endpoint_happy_path(client, api_session: Session) -> None:
    items = _seed(api_session)
    posting = _posting(api_session, NUMBERED_DUTIES)

    response = client.post(
        "/api/v1/build/duty-statement",
        json={"job_posting_id": posting.id, "selected_item_ids": [i.id for i in items]},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["template_name"] == "duty_standard"
    groups = body["sections"][0]["groups"]
    assert len(groups) == 2
    assert all(g["bullets"] for g in groups)


def test_duty_endpoint_unknown_posting_404(client) -> None:
    response = client.post(
        "/api/v1/build/duty-statement",
        json={"job_posting_id": "missing", "selected_item_ids": ["x"]},
    )
    assert response.status_code == 404


def test_duty_endpoint_validation_error(client, api_session: Session) -> None:
    posting = _posting(api_session, "No duties here.")
    response = client.post(
        "/api/v1/build/duty-statement",
        json={"job_posting_id": posting.id, "selected_item_ids": []},
    )
    assert response.status_code == 400


# --- Sprint 21 additions: raw_text path + duty preview ---


def test_generate_response_from_raw_text(session: Session, seeded) -> None:
    """Pasted posting text works without a pre-created JobPosting."""
    from sqlmodel import select

    items = seeded
    document = DutyStatementBuilderService(session).generate_response(
        raw_text=NUMBERED_DUTIES,
        selected_item_ids=[item.id for item in items],
    )
    assert len(document.sections[0].groups) == 2

    # The pasted text is persisted for provenance.
    postings = list(session.exec(select(JobPosting)).all())
    assert any(p.raw_text == NUMBERED_DUTIES for p in postings)


def test_generate_response_requires_source(session: Session, seeded) -> None:
    with pytest.raises(ValidationAppError):
        DutyStatementBuilderService(session).generate_response(
            selected_item_ids=[seeded[0].id]
        )


def test_duty_preview_endpoint(client) -> None:
    response = client.post(
        "/api/v1/build/duty-preview",
        json={"raw_text": NUMBERED_DUTIES},
    )
    assert response.status_code == 200
    requirements = response.json()["requirements"]
    assert len(requirements) == 2
    assert requirements[0]["category"]
    assert requirements[0]["keywords"]


def test_duty_preview_empty_text(client) -> None:
    response = client.post("/api/v1/build/duty-preview", json={"raw_text": ""})
    assert response.status_code == 200
    assert response.json()["requirements"] == []


def test_duty_endpoint_raw_text_happy_path(client, api_session: Session) -> None:
    items = _seed(api_session)
    response = client.post(
        "/api/v1/build/duty-statement",
        json={
            "raw_text": NUMBERED_DUTIES,
            "selected_item_ids": [i.id for i in items],
        },
    )
    assert response.status_code == 200
    assert len(response.json()["sections"][0]["groups"]) == 2


def test_duty_endpoint_missing_source_400(client) -> None:
    response = client.post(
        "/api/v1/build/duty-statement",
        json={"selected_item_ids": ["x"]},
    )
    assert response.status_code == 400
