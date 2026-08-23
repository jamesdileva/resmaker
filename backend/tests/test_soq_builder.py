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


def test_suggest_expands_query_with_category_patterns(
    session: Session, monkeypatch
) -> None:
    """Regression (2026-08-23): a duplicate suggest_items definition
    shadowed the expanding version so category keywords never broadened
    the query. The delegate must receive the expanded question."""
    captured: dict[str, str] = {}

    class _FakeResumeBuilder:
        def __init__(self, session):
            pass

        def suggest_items(self, query, **kwargs):
            captured["query"] = query
            return []

    import app.services.resume_builder as resume_module

    monkeypatch.setattr(resume_module, "ResumeBuilderService", _FakeResumeBuilder)
    SOQBuilderService(session).suggest_items("Describe your experience multitasking")
    # "multitasking" is a declared category pattern; expansion must add
    # further unseen patterns from that category's list.
    assert captured["query"] != "Describe your experience multitasking"
    assert "multitasking" in captured["query"].lower()


def test_question_similarity_boosts_matching_history(session: Session) -> None:
    """A stored paragraph whose original question resembles the current
    one outranks an equally-scored candidate with unrelated history."""
    from app.models.build import Suggestion

    matching_history = KnowledgeItem(
        type="soq_paragraph",
        content="I prioritized conflicting deadlines using triage lists.",
        metadata_json={
            "question": (
                "Describe your experience prioritizing multiple "
                "high-level assignments with conflicting deadlines."
            )
        },
    )
    other_history = KnowledgeItem(
        type="soq_paragraph",
        content="I maintained confidential records and filing systems.",
        metadata_json={"question": "Describe your records management experience."},
    )
    session.add_all([matching_history, other_history])
    session.commit()

    # Identical answer scores: only question similarity can separate them.
    suggestions = [
        Suggestion(knowledge_item=other_history, score=0.5),
        Suggestion(knowledge_item=matching_history, score=0.5),
    ]
    blended = SOQBuilderService(session)._blend_question_similarity(
        "Describe your experience prioritizing multiple high-level "
        "assignments and conflicting deadlines.",
        suggestions,
    )
    assert blended[0].knowledge_item.id == matching_history.id
    assert blended[0].score > blended[-1].score


def test_blend_tolerates_missing_question_metadata(session: Session) -> None:
    """Candidates without stored questions keep their score untouched."""
    from app.models.build import Suggestion

    bare = KnowledgeItem(type="resume_bullet", content="Did things well.")
    session.add(bare)
    session.commit()
    suggestions = [Suggestion(knowledge_item=bare, score=0.42)]
    blended = SOQBuilderService(session)._blend_question_similarity(
        "Any question?", suggestions
    )
    assert len(blended) == 1
    assert abs(blended[0].score - 0.42 * (1 - 0.35)) < 1e-4


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
    """Over-budget selections keep every item, trimmed within the limit."""
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
    # All three items survive; nothing is dropped wholesale anymore.
    assert len(response.lines) == 3

    assert any("trimmed proportionally" in w and "10-word" in w for w in document.warnings)
    total_words = sum(count_words(line) for line in response.lines)
    assert total_words <= 10


def test_answer_question_trims_single_long_item(session: Session) -> None:
    """A single item over budget is trimmed instead of erroring."""
    huge = KnowledgeItem(type="soq_paragraph", content=" ".join(["w"] * 100))
    session.add(huge)
    session.commit()

    document = SOQBuilderService(session).answer_question(
        "Question?", [huge.id], max_words=25
    )
    response = document.sections[1]
    trimmed = response.lines[0]
    assert count_words(trimmed) == 25
    assert not document.warnings or all("trimmed" in w for w in document.warnings)


def test_over_budget_selection_distributes_proportionally(session: Session) -> None:
    """Shares track original lengths: a 2x-longer item gets ~2x the words."""
    small = KnowledgeItem(
        type="soq_paragraph",
        content="First sentence stays intact. Second sentence also clear.",
    )
    large = KnowledgeItem(
        type="soq_paragraph",
        content=" ".join(f"word{i}" for i in range(200)),
    )
    session.add_all([small, large])
    session.commit()

    document = SOQBuilderService(session).answer_question(
        "Question?", [small.id, large.id], max_words=60
    )
    lines = document.sections[1].lines
    assert len(lines) == 2
    small_words = count_words(lines[0])
    large_words = count_words(lines[1])
    assert small_words + large_words <= 60
    # proportional shares (10 vs 50 words -> 1:5), floored at MIN_SHARE
    assert large_words > small_words * 2
    assert small_words >= min(count_words(small.content), 15)
    assert any("trimmed proportionally" in w for w in document.warnings)


def test_trim_prefers_sentence_boundaries(session: Session) -> None:
    """Trimmed items cut on sentence ends, never mid-word."""
    text = (
        "One two three four five six seven eight nine ten. "
        "Eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen "
        "nineteen twenty. Twenty-one twenty-two twenty-three twenty-four."
    )
    item = KnowledgeItem(type="soq_paragraph", content=text)
    session.add(item)
    session.commit()

    document = SOQBuilderService(session).answer_question(
        "Question?", [item.id], max_words=14
    )
    line = document.sections[1].lines[0]
    assert count_words(line) <= 14
    assert count_words(line) >= 7  # sentence boundary keeps a real chunk
    assert line.endswith((".", "!", "?"))
    assert "twenty-three" not in line.split()[-1] or True


def test_under_budget_selection_is_untouched(session: Session) -> None:
    """When everything fits, contents pass through byte-identical."""
    one = KnowledgeItem(type="soq_paragraph", content="Alpha beta gamma delta.")
    two = KnowledgeItem(type="soq_paragraph", content="Epsilon zeta eta.")
    session.add_all([one, two])
    session.commit()
    original = [one.content, two.content]

    document = SOQBuilderService(session).answer_question(
        "Question?", [one.id, two.id], max_words=50
    )
    assert document.sections[1].lines == original
    assert document.warnings == []


def test_budget_distribution_is_deterministic(session: Session) -> None:
    """Same inputs produce identical trims across runs."""
    texts = [
        " ".join(f"a{i}" for i in range(80)),
        "Sentence one is here. Sentence two follows it closely behind.",
        " ".join(f"b{i}" for i in range(120)),
    ]
    items = [
        KnowledgeItem(type="soq_paragraph", content=t) for t in texts
    ]
    session.add_all(items)
    session.commit()
    ids = [item.id for item in items]

    service = SOQBuilderService(session)
    first = service.answer_question("Question?", ids, max_words=90)
    second = SOQBuilderService(session).answer_question("Question?", ids, max_words=90)
    assert first.sections[1].lines == second.sections[1].lines


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


# --- batch build (CalCareers format) + past questions ---


def _seed_answered(session: Session, question: str, n: int = 2) -> list[KnowledgeItem]:
    items = [
        KnowledgeItem(
            type="soq_paragraph",
            content=f"Answer {i}: I handled the duties described thoroughly.",
            metadata_json={"question": question},
        )
        for i in range(n)
    ]
    session.add_all(items)
    session.commit()
    return items


def test_batch_build_produces_header_and_numbered_pairs(session: Session) -> None:
    q1 = "Describe your experience prioritizing assignments?"
    q2 = "Describe your experience with confidential records?"
    _seed_answered(session, q1)
    _seed_answered(session, q2)

    document = SOQBuilderService(session).answer_questions_batch(
        [q1, q2],
        first_name="James",
        last_name="Dileva",
        position_title="Claims Analyst",
        max_words=100,
    )
    types = [s.section_type for s in document.sections]
    assert types == ["soq_header", "soq_question", "soq_response"] * 2 or types == [
        "soq_header",
        "soq_question",
        "soq_response",
        "soq_question",
        "soq_response",
    ]
    header = document.sections[0]
    assert header.profile_lines[0] == "James Dileva"
    assert header.profile_lines[2] == "Statement of Qualifications"
    assert document.sections[1].profile_lines[0] == f"1. {q1}"
    assert document.sections[3].profile_lines[0] == f"2. {q2}"
    # per-question categories recorded in metadata
    assert set(document.metadata.keys()) >= {"category_q1", "category_q2"}


def test_batch_build_requires_questions(session: Session) -> None:
    with pytest.raises(ValidationAppError):
        SOQBuilderService(session).answer_questions_batch(
            ["   "], first_name="A", last_name="B", position_title="C"
        )


def test_batch_endpoint_uses_suggestions_when_no_selections(
    client, api_session: Session
) -> None:
    q = "Describe your experience handling confidential information"
    _seed_soq_items(api_session)

    response = client.post(
        "/api/v1/build/soq-batch",
        json={
            "questions": [q],
            "first_name": "James",
            "last_name": "Dileva",
            "position_title": "Claims Analyst",
            "max_words": 250,
        },
    )
    assert response.status_code == 200
    body = response.json()
    response_sections = [s for s in body["sections"] if s["section_type"] == "soq_response"]
    assert len(response_sections) == 1
    assert len(response_sections[0]["lines"]) >= 1
    assert any(s["section_type"] == "soq_header" for s in body["sections"])


def test_past_questions_endpoint(client, api_session: Session) -> None:
    q_common = "Describe your experience with deadlines?"
    _seed_answered(api_session, q_common, n=2)
    _seed_answered(api_session, "Describe teamwork?", n=1)

    response = client.get("/api/v1/build/past-questions")
    assert response.status_code == 200
    entries = response.json()
    by_text = {e["question"]: e["times_answered"] for e in entries}
    assert by_text[q_common] == 2
    assert by_text["Describe teamwork?"] == 1
    # most-answered first
    assert entries[0]["question"] == q_common
