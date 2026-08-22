"""Tests for the SOQ builder service and endpoint (Sprint 16)."""

import pytest
from sqlmodel import Session

from app.core.exceptions import ValidationAppError
from app.db.models import Evidence, KnowledgeItem, KnowledgeItemEvidenceLink
from app.services.soq_builder import SOQBuilderService, count_words


def _seed_soq_items(session: Session):
    evidence = Evidence(
        type="experience",
        title="Boost Mobile",
        content="retail",
        role="Sales Associate",
        company="Boost Mobile",
    )
    session.add(evidence)
    session.flush()

    items = [
        KnowledgeItem(
            type="soq_paragraph",
            title="Confidential question",
            content=(
                "Throughout my five years at Boost Mobile I managed "
                "confidential customer records and verified identities."
            ),
            category="Confidential Information",
        ),
        KnowledgeItem(
            type="soq_paragraph",
            content=(
                "I performed weekly data analysis on intake reports and "
                "presented findings to management using Excel dashboards."
            ),
            category="Analysis",
        ),
        # Long item that will not fit small word budgets.
        KnowledgeItem(
            type="soq_paragraph",
            content=" ".join(["filler"] * 120),
        ),
    ]
    for item in items:
        session.add(item)
        session.flush()
        if item.category:
            session.add(
                KnowledgeItemEvidenceLink(
                    knowledge_item_id=item.id,
                    evidence_id=evidence.id,
                )
            )
    session.commit()
    return items


@pytest.fixture()
def seeded(session: Session):
    return _seed_soq_items(session)


# --- count_words ---


def test_count_words() -> None:
    assert count_words("one two three") == 3
    assert count_words("") == 0
    assert count_words("  spaced   out  ") == 2


# --- suggest_items ---


def test_suggest_returns_relevant_evidence(session: Session, seeded) -> None:
    service = SOQBuilderService(session)
    suggestions = service.suggest_items(
        "Describe your experience handling confidential information"
    )
    assert len(suggestions) >= 1
    top = suggestions[0]
    assert "confidential" in top.knowledge_item.content.lower()
    assert top.evidence_id is not None


def test_suggest_filters_by_type(session: Session, seeded) -> None:
    service = SOQBuilderService(session)
    suggestions = service.suggest_items(
        "confidential analysis", item_types=["soq_paragraph"]
    )
    assert all(s.knowledge_item.type == "soq_paragraph" for s in suggestions)


# --- answer_question ---


def test_answer_question_builds_response_with_traceability(
    session: Session, seeded
) -> None:
    first = seeded[0]
    document = SOQBuilderService(session).answer_question(
        "Describe your experience handling confidential information",
        [first.id],
    )

    assert document.document_id
    section_types = [s.section_type for s in document.sections]
    assert section_types == ["soq_question", "soq_response"]

    question_section = document.sections[0]
    assert question_section.profile_lines[0].startswith("Describe your")

    response_section = document.sections[1]
    assert len(response_section.lines) == 1

    assert document.traceability == {first.id: document.traceability[first.id]}
    assert list(document.traceability.values())[0]


def test_answer_question_skips_missing_and_duplicate_ids(
    session: Session, seeded
) -> None:
    first = seeded[0]
    document = SOQBuilderService(session).answer_question(
        "Question?", [first.id, "missing-id", first.id, "missing-2"]
    )
    response = document.sections[1]
    assert len(response.lines) == 1


def test_answer_question_enforces_word_budget(session: Session) -> None:
    """Items that would overflow the budget are dropped with a warning."""
    short_one = KnowledgeItem(type="soq_paragraph", content="one two three")
    short_two = KnowledgeItem(type="soq_paragraph", content="four five six seven")
    huge = KnowledgeItem(
        type="soq_paragraph", content=" ".join(["word"] * 500)
    )
    session.add_all([short_one, short_two, huge])
    session.commit()

    document = SOQBuilderService(session).answer_question(
        "Question?",
        [short_one.id, short_two.id, huge.id],
        max_words=10,
    )
    response = document.sections[1]
    assert response.lines == ["one two three", "four five six seven"]

    assert any("omitted" in w and "10-word" in w for w in document.warnings)
    total_words = sum(count_words(line) for line in response.lines)
    assert total_words <= 10


def test_answer_question_raises_when_nothing_fits(session: Session) -> None:
    huge = KnowledgeItem(type="soq_paragraph", content=" ".join(["w"] * 100))
    session.add(huge)
    session.commit()

    with pytest.raises(ValidationAppError):
        SOQBuilderService(session).answer_question("Question?", [huge.id], max_words=25)


def test_answer_question_requires_question(session: Session, seeded) -> None:
    with pytest.raises(ValidationAppError):
        SOQBuilderService(session).answer_question("   ", [seeded[0].id])


def test_answer_question_requires_valid_items(session: Session, seeded) -> None:
    with pytest.raises(ValidationAppError):
        SOQBuilderService(session).answer_question("Question?", ["nope"])


# --- API ---


def test_build_soq_endpoint(client, api_session: Session, seeded=None) -> None:
    items = _seed_soq_items(api_session)

    response = client.post(
        "/api/v1/build/soq",
        json={
            "question": "Describe your experience handling confidential information",
            "selected_item_ids": [items[0].id],
            "max_words": 250,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["template_name"] == "soq_standard"
    types = [s["section_type"] for s in body["sections"]]
    assert types == ["soq_question", "soq_response"]


def test_build_soq_endpoint_validation(client, api_session: Session) -> None:
    response = client.post(
        "/api/v1/build/soq",
        json={"question": "What?", "selected_item_ids": ["missing"]},
    )
    assert response.status_code == 400


def test_build_soq_endpoint_request_validation(client) -> None:
    response = client.post("/api/v1/build/soq", json={"question": ""})
    assert response.status_code == 400
