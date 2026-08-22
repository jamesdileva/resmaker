"""Tests for database schema creation, FTS5 indexing, and triggers."""

from pathlib import Path

from sqlalchemy import inspect, text
from sqlmodel import Session, select

from app.db.connection import get_engine, init_db
from app.db.models import KnowledgeItem

EXPECTED_TABLES = {
    "source_documents",
    "evidence",
    "knowledge_items",
    "resume_bullets",
    "soq_paragraphs",
    "knowledge_item_evidence",
    "skills",
    "knowledge_item_skills",
    "metrics",
    "keywords",
    "categories",
    "knowledge_item_keywords",
    "job_postings",
    "applications",
    "application_evidence",
}

EXPECTED_TRIGGERS = {
    "knowledge_items_fts_insert",
    "knowledge_items_fts_delete",
    "knowledge_items_fts_update",
}

EXPECTED_INDEXES = {
    "ix_knowledge_items_type",
    "ix_knowledge_items_category",
    "ix_knowledge_items_source_doc",
    "ix_evidence_source_doc",
    "ix_applications_job_posting",
}


def make_initialized_engine(tmp_path: Path):
    """Return an engine with the full schema applied to a temp file."""
    db_file = tmp_path / "schema_test.db"
    engine = get_engine(str(db_file))
    init_db(engine)
    return engine


def list_tables(engine) -> set[str]:
    inspector = inspect(engine)
    return set(inspector.get_table_names())


def test_init_db_creates_database_file(tmp_path: Path) -> None:
    db_file = tmp_path / "fresh.db"
    assert not db_file.exists()
    engine = get_engine(str(db_file))
    init_db(engine)
    assert db_file.exists()


def test_init_db_creates_all_tables(tmp_path: Path) -> None:
    engine = make_initialized_engine(tmp_path)
    tables = list_tables(engine)
    missing = EXPECTED_TABLES - tables
    assert not missing, f"missing tables: {missing}"
    assert len(tables) >= 15


def test_fts5_virtual_table_created(tmp_path: Path) -> None:
    engine = make_initialized_engine(tmp_path)
    tables = list_tables(engine)
    assert "knowledge_items_fts" in tables
    with engine.begin() as conn:
        rows = conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'knowledge_items_fts%'")
        ).fetchall()
    names = {row[0] for row in rows}
    assert "knowledge_items_fts" in names
    assert any(name.endswith("_data") or name.endswith("_idx") for name in names)


def test_all_triggers_created(tmp_path: Path) -> None:
    engine = make_initialized_engine(tmp_path)
    with engine.begin() as conn:
        rows = conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='trigger'")
        ).fetchall()
    triggers = {row[0] for row in rows}
    assert EXPECTED_TRIGGERS <= triggers


def test_all_indexes_created(tmp_path: Path) -> None:
    engine = make_initialized_engine(tmp_path)
    with engine.begin() as conn:
        rows = conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'")
        ).fetchall()
    indexes = {row[0] for row in rows}
    assert EXPECTED_INDEXES <= indexes


def test_fts_stays_in_sync_with_knowledge_items(tmp_path: Path) -> None:
    engine = make_initialized_engine(tmp_path)
    item = KnowledgeItem(type="resume_bullet", content="Handled confidential records")
    with Session(engine) as session:
        session.add(item)
        session.commit()
        item_id = item.id

        results = session.exec(
            text("SELECT item_id FROM knowledge_items_fts WHERE knowledge_items_fts MATCH 'confidential'")
        ).all()
    assert len(results) == 1

    with Session(engine) as session:
        stored = session.get(KnowledgeItem, item_id)
        session.delete(stored)
        session.commit()
        remaining = session.exec(
            text("SELECT item_id FROM knowledge_items_fts WHERE knowledge_items_fts MATCH 'confidential'")
        ).all()
    assert remaining == []


def test_foreign_keys_enforced(tmp_path: Path) -> None:
    engine = make_initialized_engine(tmp_path)
    from app.db.models import ResumeBullet

    with Session(engine) as session:
        orphan = ResumeBullet(knowledge_item_id="nonexistent-id")
        session.add(orphan)
        try:
            session.commit()
            raised = False
        except Exception:
            raised = True
    assert raised, "expected FK violation for non-existent knowledge_item_id"
