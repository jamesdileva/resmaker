"""Tests for the core repository layer (Sprint 3)."""

from pathlib import Path

import pytest
from sqlmodel import Session, select

from app.db.connection import get_engine, init_db
from app.db.models import (
    Application,
    ApplicationEvidenceLink,
    Evidence,
    JobPosting,
    KnowledgeItem,
    KnowledgeItemEvidenceLink,
)
from app.repositories.application import ApplicationRepository
from app.repositories.evidence import EvidenceRepository
from app.repositories.knowledge_item import KnowledgeItemRepository


@pytest.fixture()
def session(tmp_path: Path):
    """Yield a session over a freshly initialized temp database."""
    db_file = tmp_path / "repo_test.db"
    engine = get_engine(str(db_file))
    init_db(engine)
    with Session(engine) as sess:
        yield sess


@pytest.fixture()
def knowledge_items(session: Session) -> list[KnowledgeItem]:
    items = [
        KnowledgeItem(
            type="resume_bullet",
            title="Confidential records",
            content="Handled confidential customer records daily",
            category="Confidential Information",
        ),
        KnowledgeItem(
            type="soq_paragraph",
            title="Analysis work",
            content="Performed data analysis and produced weekly reports",
            category="Analysis",
        ),
        KnowledgeItem(
            type="resume_bullet",
            title="Customer service",
            content="Resolved customer complaints with empathy",
            category="Customer Service",
        ),
    ]
    session.add_all(items)
    session.commit()
    for item in items:
        session.refresh(item)
    return items


# --- KnowledgeItemRepository ---


def test_knowledge_item_create_and_get(session: Session) -> None:
    repo = KnowledgeItemRepository(session)
    created = repo.create(
        KnowledgeItem(type="resume_bullet", content="Shipped a feature")
    )
    assert created.id
    fetched = repo.get(created.id)
    assert fetched is not None
    assert fetched.content == "Shipped a feature"


def test_knowledge_item_get_missing_returns_none(session: Session) -> None:
    repo = KnowledgeItemRepository(session)
    assert repo.get("no-such-id") is None


def test_knowledge_item_get_multi_filters(session: Session, knowledge_items) -> None:
    repo = KnowledgeItemRepository(session)
    all_items = repo.get_multi(skip=0, limit=10)
    assert len(all_items) == 3
    bullets = repo.get_multi(skip=0, limit=10, type="resume_bullet")
    assert len(bullets) == 2
    confidential = repo.get_multi(
        skip=0, limit=10, category="Confidential Information"
    )
    assert len(confidential) == 1


def test_knowledge_item_get_multi_pagination(session: Session, knowledge_items) -> None:
    repo = KnowledgeItemRepository(session)
    page = repo.get_multi(skip=1, limit=1)
    assert len(page) == 1
    empty = repo.get_multi(skip=10, limit=10)
    assert empty == []


def test_knowledge_item_update(session: Session, knowledge_items) -> None:
    repo = KnowledgeItemRepository(session)
    target = knowledge_items[0]
    updated = repo.update(target.id, {"title": "New title", "category": "Privacy"})
    assert updated.title == "New title"
    assert updated.category == "Privacy"
    assert repo.get(target.id).content == target.content


def test_knowledge_item_delete(session: Session, knowledge_items) -> None:
    repo = KnowledgeItemRepository(session)
    target = knowledge_items[0]
    assert repo.delete(target.id) is True
    assert repo.get(target.id) is None
    assert repo.delete("already-gone") is False


def test_knowledge_item_bulk_create(session: Session) -> None:
    repo = KnowledgeItemRepository(session)
    drafts = [
        KnowledgeItem(type="skill", content=f"Skill {i}") for i in range(5)
    ]
    created = repo.bulk_create(drafts)
    assert len(created) == 5
    assert all(item.id for item in created)
    assert len(repo.get_multi()) == 5


def test_knowledge_item_search_ranks_by_relevance(
    session: Session, knowledge_items
) -> None:
    repo = KnowledgeItemRepository(session)
    results = repo.search("confidential records")
    assert len(results) >= 1
    top = results[0]
    assert top.knowledge_item.id == knowledge_items[0].id
    assert 0.0 < top.score <= 1.0
    scores = [r.score for r in results]
    assert scores == sorted(scores, reverse=True)


def test_knowledge_item_search_min_score_filters(
    session: Session, knowledge_items
) -> None:
    repo = KnowledgeItemRepository(session)
    everything = repo.search("confidential", min_score=0.0)
    strict = repo.search("confidential", min_score=0.99)
    assert len(everything) >= 1
    assert all(r.score >= 0.99 for r in strict)


def test_get_with_evidence(session: Session, knowledge_items) -> None:
    evidence_repo = EvidenceRepository(session)
    item_repo = KnowledgeItemRepository(session)
    ev = evidence_repo.create(
        Evidence(type="experience", title="Boost Mobile", content="Retail role")
    )
    evidence_repo.link_to_item(ev.id, knowledge_items[0].id, strength=4)

    item, linked = item_repo.get_with_evidence(knowledge_items[0].id)
    assert item is not None
    assert [e.id for e in linked] == [ev.id]

    missing_item, no_evidence = item_repo.get_with_evidence("missing")
    assert missing_item is None
    assert no_evidence == []


# --- EvidenceRepository ---


def test_evidence_create_get_multi(session: Session) -> None:
    repo = EvidenceRepository(session)
    ev = repo.create(
        Evidence(type="project", title="Side project", content="Built an app")
    )
    fetched = repo.get(ev.id)
    assert fetched is not None
    assert fetched.evidence.title == "Side project"
    assert repo.get_multi(skip=0, limit=10)[0].id == ev.id
    assert repo.get("missing") is None


def test_evidence_link_to_item(session: Session, knowledge_items) -> None:
    repo = EvidenceRepository(session)
    ev = repo.create(Evidence(type="experience", title="Job", content="Work"))
    repo.link_to_item(ev.id, knowledge_items[1].id, strength=2)
    fetched = repo.get(ev.id)
    assert [i.id for i in fetched.items] == [knowledge_items[1].id]


def test_evidence_get_success_rate(session: Session, knowledge_items) -> None:
    posting = JobPosting(title="Analyst", raw_text="duties")
    session.add(posting)
    session.commit()
    app_ok = Application(job_posting_id=posting.id, status="offer")
    app_bad = Application(job_posting_id=posting.id, status="rejected")
    session.add_all([app_ok, app_bad])
    session.commit()

    repo = EvidenceRepository(session)
    ev = repo.create(Evidence(type="experience", title="Job", content="Work"))
    repo.link_to_item(ev.id, knowledge_items[0].id)

    item_repo = KnowledgeItemRepository(session)
    usage_repo = ApplicationRepository(session)
    item_id = knowledge_items[0].id
    usage_repo.record_evidence_usage(app_ok.id, item_id, result="offer")
    usage_repo.record_evidence_usage(app_bad.id, item_id, result="rejected")

    rate = repo.get_success_rate(ev.id)
    assert rate == pytest.approx(0.5)


def test_evidence_get_success_rate_no_history(session: Session) -> None:
    repo = EvidenceRepository(session)
    ev = repo.create(Evidence(type="education", title="Degree", content="BSc"))
    assert repo.get_success_rate(ev.id) == 0.0


# --- ApplicationRepository ---


def test_application_create_get_update_result(session: Session) -> None:
    posting = JobPosting(title="Role", raw_text="duties")
    session.add(posting)
    session.commit()

    repo = ApplicationRepository(session)
    app = repo.create(Application(job_posting_id=posting.id))
    assert app.status == "applied"

    fetched = repo.get(app.id)
    assert fetched is not None
    assert repo.get("missing") is None

    updated = repo.update_result(app.id, "interview")
    assert updated.status == "interview"
    assert repo.update_result("missing", "offer") is None


def test_base_generic_helpers_via_application_repo(session: Session) -> None:
    """The inherited BaseRepository CRUD helpers behave correctly."""
    posting = JobPosting(title="Role", raw_text="duties")
    session.add(posting)
    session.commit()
    repo = ApplicationRepository(session)

    listed = repo.get_multi(skip=0, limit=10)
    assert len(listed) == 0

    app = repo.create(Application(job_posting_id=posting.id))
    assert [a.id for a in repo.get_multi(skip=0, limit=10)] == [app.id]

    assert repo.delete(app.id) is True
    assert repo.delete(app.id) is False
    assert repo.get_multi(skip=0, limit=10) == []


def test_record_evidence_usage_upserts(session: Session, knowledge_items) -> None:
    posting = JobPosting(title="Role", raw_text="duties")
    session.add(posting)
    session.commit()
    repo = ApplicationRepository(session)
    app = repo.create(Application(job_posting_id=posting.id))

    repo.record_evidence_usage(
        app.id, knowledge_items[0].id, used_in_resume=True, result=None
    )
    repo.record_evidence_usage(
        app.id, knowledge_items[0].id, used_in_resume=True, result="interview"
    )

    links = list(
        session.exec(select(ApplicationEvidenceLink)).all()
    )
    assert len(links) == 1
    assert links[0].result == "interview"


def test_get_success_weight(session: Session, knowledge_items) -> None:
    posting = JobPosting(title="Role", raw_text="duties")
    session.add(posting)
    session.commit()
    repo = ApplicationRepository(session)
    app_offer = repo.create(Application(job_posting_id=posting.id))
    app_interview = repo.create(Application(job_posting_id=posting.id))
    app_reject = repo.create(Application(job_posting_id=posting.id))

    item_id = knowledge_items[0].id
    repo.record_evidence_usage(app_offer.id, item_id, result="offer")
    repo.record_evidence_usage(app_interview.id, item_id, result="interview")
    repo.record_evidence_usage(app_reject.id, item_id, result="rejected")

    weight = repo.get_success_weight(item_id)
    # interview_rate = 2/3 (interview or offer), offer_rate = 1/3
    expected = 0.1 * (2 / 3) + 0.2 * (1 / 3)
    assert weight == pytest.approx(expected)
    assert 0.0 <= weight <= 0.3
    assert repo.get_success_weight("unknown-item") == 0.0
