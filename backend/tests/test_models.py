"""Tests for SQLModel defaults, constraints, and serialization."""

import pytest
from sqlalchemy import inspect
from sqlmodel import Session

from app.db.models import (
    Application,
    ApplicationEvidenceLink,
    Category,
    Evidence,
    JobPosting,
    Keyword,
    KnowledgeItem,
    Skill,
    SourceDocument,
)


def test_knowledge_item_defaults(session: Session) -> None:
    item = KnowledgeItem(type="resume_bullet", content="content")
    session.add(item)
    session.commit()
    session.refresh(item)

    assert item.id  # UUID assigned by default_factory
    assert len(item.id) == 36
    assert item.created_at is not None
    assert item.updated_at is not None
    assert item.metadata_json == {}
    assert item.confidence is None
    assert item.category is None


def test_metadata_json_round_trip(session: Session) -> None:
    item = KnowledgeItem(
        type="soq_paragraph",
        content="answer",
        metadata_json={"question": "Q1", "word_count": 42},
    )
    session.add(item)
    session.commit()
    session.refresh(item)
    stored = session.get(KnowledgeItem, item.id)
    assert stored.metadata_json == {"question": "Q1", "word_count": 42}


def test_unique_constraint_on_skill_name(session: Session) -> None:
    session.add(Skill(name="SQL"))
    session.commit()
    duplicate = Skill(name="SQL")
    session.add(duplicate)
    with pytest.raises(Exception):
        session.commit()
    session.rollback()


def test_unique_constraint_on_keyword_term(session: Session) -> None:
    session.add(Keyword(term="confidential"))
    session.commit()
    session.add(Keyword(term="confidential"))
    with pytest.raises(Exception):
        session.commit()
    session.rollback()


def test_unique_constraint_on_category_name(session: Session) -> None:
    session.add(Category(name="Analysis"))
    session.commit()
    session.add(Category(name="Analysis"))
    with pytest.raises(Exception):
        session.commit()
    session.rollback()


def test_junction_tables_enforce_composite_uniqueness(session: Session) -> None:
    from app.db.models import ApplicationEvidenceLink, KnowledgeItemEvidenceLink

    item = KnowledgeItem(type="skill", content="Python")
    evidence = Evidence(type="experience", title="Job", content="Work")
    posting = JobPosting(title="Role", raw_text="duties")
    session.add_all([item, evidence, posting])
    session.commit()
    application = Application(job_posting_id=posting.id)
    session.add(application)
    session.commit()

    session.add(
        KnowledgeItemEvidenceLink(
            knowledge_item_id=item.id, evidence_id=evidence.id, strength=3
        )
    )
    session.commit()
    duplicate = KnowledgeItemEvidenceLink(
        knowledge_item_id=item.id, evidence_id=evidence.id, strength=5
    )
    session.add(duplicate)
    with pytest.raises(Exception):
        session.commit()
    session.rollback()

    session.add(
        ApplicationEvidenceLink(
            application_id=application.id,
            knowledge_item_id=item.id,
            result="interview",
        )
    )
    session.commit()
    duplicate_usage = ApplicationEvidenceLink(
        application_id=application.id,
        knowledge_item_id=item.id,
        result="offer",
    )
    session.add(duplicate_usage)
    with pytest.raises(Exception):
        session.commit()
    session.rollback()


def test_source_document_link(session: Session) -> None:
    doc = SourceDocument(filename="resume.docx", file_type="docx")
    session.add(doc)
    session.commit()
    session.refresh(doc)

    item = KnowledgeItem(type="resume_bullet", content="x", source_doc_id=doc.id)
    session.add(item)
    session.commit()
    session.refresh(item)
    assert item.source_doc_id == doc.id


def test_application_requires_existing_posting(session: Session) -> None:
    application = Application(job_posting_id="missing-posting")
    session.add(application)
    with pytest.raises(Exception):
        session.commit()
    session.rollback()


def test_job_posting_defaults(session: Session) -> None:
    posting = JobPosting(title="Clerk", raw_text="duties here")
    session.add(posting)
    session.commit()
    session.refresh(posting)
    assert posting.posted_at is None
    assert posting.agency is None


def test_evidence_optional_fields(session: Session) -> None:
    evidence = Evidence(type="education", title="Degree", content="BSc CS")
    session.add(evidence)
    session.commit()
    session.refresh(evidence)
    assert evidence.company is None
    assert evidence.role is None
    assert evidence.start_date is None
