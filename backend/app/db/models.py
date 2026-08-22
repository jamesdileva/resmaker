"""SQLModel table definitions for the Career OS knowledge base."""

from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import Column, JSON, UniqueConstraint
from sqlmodel import Field, SQLModel


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _uuid() -> str:
    import uuid

    return str(uuid.uuid4())


class SourceDocument(SQLModel, table=True):
    """An original document imported from disk."""

    __tablename__ = "source_documents"

    id: str = Field(default_factory=_uuid, primary_key=True)
    filename: str = Field(index=True)
    file_type: str  # "docx" | "pdf" | "txt"
    file_path: str | None = None
    imported_at: datetime = Field(default_factory=_utcnow)


class Evidence(SQLModel, table=True):
    """A verified experience/project/education record backing knowledge items."""

    __tablename__ = "evidence"

    id: str = Field(default_factory=_uuid, primary_key=True)
    title: str = Field(index=True)
    type: str  # "experience" | "project" | "education"
    content: str
    start_date: str | None = None
    end_date: str | None = None
    company: str | None = None
    role: str | None = None
    source_doc_id: str | None = Field(
        default=None, foreign_key="source_documents.id"
    )


class KnowledgeItem(SQLModel, table=True):
    """A reusable unit of career knowledge (bullet, SOQ paragraph, etc.)."""

    __tablename__ = "knowledge_items"

    id: str = Field(default_factory=_uuid, primary_key=True)
    type: str = Field(index=True)  # "resume_bullet", "soq_paragraph", ...
    title: str | None = None
    content: str
    category: str | None = Field(default=None, index=True)
    confidence: float | None = None
    metadata_json: dict[str, Any] = Field(
        default={}, sa_column=Column("metadata", JSON)
    )
    source_doc_id: str | None = Field(
        default=None, foreign_key="source_documents.id"
    )
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)


class ResumeBullet(SQLModel, table=True):
    """Resume-bullet-specific extension data for a knowledge item."""

    __tablename__ = "resume_bullets"

    id: str = Field(default_factory=_uuid, primary_key=True)
    knowledge_item_id: str = Field(foreign_key="knowledge_items.id", index=True)
    order_index: int = 0


class SOQParagraph(SQLModel, table=True):
    """SOQ-paragraph-specific extension data for a knowledge item."""

    __tablename__ = "soq_paragraphs"

    id: str = Field(default_factory=_uuid, primary_key=True)
    knowledge_item_id: str = Field(foreign_key="knowledge_items.id", index=True)
    question_text: str | None = None
    order_index: int = 0


class KnowledgeItemEvidenceLink(SQLModel, table=True):
    """Junction table linking knowledge items to evidence with a strength."""

    __tablename__ = "knowledge_item_evidence"
    __table_args__ = (
        UniqueConstraint("knowledge_item_id", "evidence_id", name="uq_kie_pair"),
    )

    id: str = Field(default_factory=_uuid, primary_key=True)
    knowledge_item_id: str = Field(foreign_key="knowledge_items.id", index=True)
    evidence_id: str = Field(foreign_key="evidence.id", index=True)
    strength: int = 3  # 1-5


class Skill(SQLModel, table=True):
    """A standalone skill extracted from knowledge items."""

    __tablename__ = "skills"

    id: str = Field(default_factory=_uuid, primary_key=True)
    name: str = Field(unique=True, index=True)


class KnowledgeItemSkillLink(SQLModel, table=True):
    """Junction table linking knowledge items to skills."""

    __tablename__ = "knowledge_item_skills"
    __table_args__ = (
        UniqueConstraint("knowledge_item_id", "skill_id", name="uq_kis_pair"),
    )

    id: str = Field(default_factory=_uuid, primary_key=True)
    knowledge_item_id: str = Field(foreign_key="knowledge_items.id", index=True)
    skill_id: str = Field(foreign_key="skills.id")


class Metric(SQLModel, table=True):
    """A quantitative achievement linked to a knowledge item."""

    __tablename__ = "metrics"

    id: str = Field(default_factory=_uuid, primary_key=True)
    knowledge_item_id: str = Field(foreign_key="knowledge_items.id", index=True)
    name: str
    value: str


class Keyword(SQLModel, table=True):
    """A searchable keyword."""

    __tablename__ = "keywords"

    id: str = Field(default_factory=_uuid, primary_key=True)
    term: str = Field(unique=True, index=True)


class Category(SQLModel, table=True):
    """A topic classification for knowledge items."""

    __tablename__ = "categories"

    id: str = Field(default_factory=_uuid, primary_key=True)
    name: str = Field(unique=True, index=True)
    description: str | None = None


class KnowledgeItemKeywordLink(SQLModel, table=True):
    """Junction table linking knowledge items to keywords."""

    __tablename__ = "knowledge_item_keywords"
    __table_args__ = (
        UniqueConstraint("knowledge_item_id", "keyword_id", name="uq_kik_pair"),
    )

    id: str = Field(default_factory=_uuid, primary_key=True)
    knowledge_item_id: str = Field(foreign_key="knowledge_items.id", index=True)
    keyword_id: str = Field(foreign_key="keywords.id")


class JobPosting(SQLModel, table=True):
    """An external job posting used as a build target."""

    __tablename__ = "job_postings"

    id: str = Field(default_factory=_uuid, primary_key=True)
    title: str
    agency: str | None = None
    raw_text: str
    posted_at: datetime | None = None
    source_url: str | None = None


class Application(SQLModel, table=True):
    """A job application with success tracking."""

    __tablename__ = "applications"

    id: str = Field(default_factory=_uuid, primary_key=True)
    job_posting_id: str = Field(foreign_key="job_postings.id", index=True)
    status: str = "applied"  # "applied" | "interview" | "offer" | "rejected"
    applied_at: datetime = Field(default_factory=_utcnow)


class ApplicationEvidenceLink(SQLModel, table=True):
    """Tracks which knowledge items were used in which application and outcome."""

    __tablename__ = "application_evidence"
    __table_args__ = (
        UniqueConstraint("application_id", "knowledge_item_id", name="uq_ae_pair"),
    )

    id: str = Field(default_factory=_uuid, primary_key=True)
    application_id: str = Field(foreign_key="applications.id", index=True)
    knowledge_item_id: str = Field(foreign_key="knowledge_items.id", index=True)
    used_in_resume: bool = False
    used_in_soq: bool = False
    used_in_duty: bool = False
    result: str | None = None  # "interview" | "offer" | "rejected"


__all__ = [
    "SourceDocument",
    "Evidence",
    "KnowledgeItem",
    "ResumeBullet",
    "SOQParagraph",
    "KnowledgeItemEvidenceLink",
    "Skill",
    "KnowledgeItemSkillLink",
    "Metric",
    "Keyword",
    "Category",
    "KnowledgeItemKeywordLink",
    "JobPosting",
    "Application",
    "ApplicationEvidenceLink",
]
