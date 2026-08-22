"""Database package: engine management and full schema creation."""

from sqlalchemy import text
from sqlalchemy.engine import Engine

FTS_TABLE_DDL = """
CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_items_fts USING fts5(
    item_id UNINDEXED,
    title,
    content
)
"""

FTS_TRIGGER_DDL = [
    """
    CREATE TRIGGER IF NOT EXISTS knowledge_items_fts_insert
    AFTER INSERT ON knowledge_items BEGIN
        INSERT INTO knowledge_items_fts (item_id, title, content)
        VALUES (new.id, new.title, new.content);
    END
    """,
    """
    CREATE TRIGGER IF NOT EXISTS knowledge_items_fts_delete
    AFTER DELETE ON knowledge_items BEGIN
        DELETE FROM knowledge_items_fts WHERE item_id = old.id;
    END
    """,
    """
    CREATE TRIGGER IF NOT EXISTS knowledge_items_fts_update
    AFTER UPDATE OF title, content ON knowledge_items BEGIN
        DELETE FROM knowledge_items_fts WHERE item_id = new.id;
        INSERT INTO knowledge_items_fts (item_id, title, content)
        VALUES (new.id, new.title, new.content);
    END
    """,
]

INDEX_DDL = [
    "CREATE INDEX IF NOT EXISTS ix_knowledge_items_type ON knowledge_items (type)",
    "CREATE INDEX IF NOT EXISTS ix_knowledge_items_category ON knowledge_items (category)",
    "CREATE INDEX IF NOT EXISTS ix_knowledge_items_source_doc ON knowledge_items (source_doc_id)",
    "CREATE INDEX IF NOT EXISTS ix_evidence_source_doc ON evidence (source_doc_id)",
    "CREATE INDEX IF NOT EXISTS ix_applications_job_posting ON applications (job_posting_id)",
]


def apply_schema_extras(engine: Engine) -> None:
    """Create the FTS5 virtual table, sync triggers, and indexes."""
    with engine.begin() as conn:
        conn.execute(text(FTS_TABLE_DDL))
        for ddl in FTS_TRIGGER_DDL + INDEX_DDL:
            conn.execute(text(ddl))
