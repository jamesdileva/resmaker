"""Shared pytest fixtures and test-data factories."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.db.connection import get_engine, init_db
from app.db.models import (
    Application,
    Evidence,
    JobPosting,
    KnowledgeItem,
)


@pytest.fixture()
def session(tmp_path: Path):
    """Yield a session over a freshly initialized temp database."""
    engine = get_engine(str(tmp_path / "test.db"))
    init_db(engine)
    with Session(engine) as sess:
        yield sess


@pytest.fixture()
def client(tmp_path: Path, monkeypatch):
    """TestClient over an app bound to a fresh temp database."""
    monkeypatch.setenv("CAREER_OS_DB_PATH", str(tmp_path / "api_test.db"))
    from app.main import app

    with TestClient(app) as test_client:
        yield test_client


def make_knowledge_item(
    type: str = "resume_bullet",
    content: str = "Did a thing",
    **overrides,
) -> KnowledgeItem:
    """Build a knowledge item with sensible test defaults."""
    return KnowledgeItem(type=type, content=content, **overrides)


def make_evidence(title: str = "Test job", **overrides) -> Evidence:
    """Build an evidence record with sensible test defaults."""
    defaults = {"type": "experience", "title": title, "content": "Work done"}
    return Evidence(**{**defaults, **overrides})


@pytest.fixture()
def job_posting(client) -> JobPosting:
    """A committed job posting in the API test database (for FK references)."""
    posting = JobPosting(title="Analyst", raw_text="duties")
    engine = get_engine()  # resolves the env-configured API test database
    with Session(engine) as sess:
        sess.add(posting)
        sess.commit()
        sess.refresh(posting)
    return posting


def commit_all(session: Session, *instances):
    """Add instances to the session, commit, and refresh them."""
    session.add_all(instances)
    session.commit()
    for instance in instances:
        session.refresh(instance)
    return instances


def seeded_knowledge_items(session: Session) -> list[KnowledgeItem]:
    """Create three representative knowledge items."""
    items = [
        make_knowledge_item(
            title="Confidential records",
            content="Handled confidential customer records daily",
            category="Confidential Information",
        ),
        make_knowledge_item(
            type="soq_paragraph",
            title="Analysis work",
            content="Performed data analysis and produced weekly reports",
            category="Analysis",
        ),
        make_knowledge_item(
            title="Customer service",
            content="Resolved customer complaints with empathy",
            category="Customer Service",
        ),
    ]
    return commit_all(session, *items)


@pytest.fixture()
def knowledge_items(session):
    """Three committed knowledge items covering distinct categories."""
    return seeded_knowledge_items(session)


@pytest.fixture()
def application_with_history(session, knowledge_items) -> Application:
    """An application plus usage history on the first knowledge item."""
    posting = JobPosting(title="Role", raw_text="duties")
    application = Application(job_posting_id=posting.id)
    session.add(posting)
    session.add(application)
    session.commit()
    session.refresh(application)
    return application
