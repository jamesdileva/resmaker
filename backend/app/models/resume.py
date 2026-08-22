"""Pydantic schemas for resume templates and rendering."""

from typing import Any, Optional

from pydantic import BaseModel, Field


class ResumeTemplateSection(BaseModel):
    """One section definition inside a resume template."""

    title: str
    type: str  # "profile" | "experience" | "skills" | "projects"
    source: Optional[str] = None  # e.g. "user_profile"
    item_types: list[str] = []
    group_by: Optional[str] = None
    show_dates: bool = False


class ResumeTemplate(BaseModel):
    """A versionable JSON-defined resume layout."""

    name: str
    version: int = 1
    sections: list[ResumeTemplateSection]
    formatting: dict[str, Any] = Field(default_factory=dict)


class ExperienceGroup(BaseModel):
    """Bullets grouped under one evidence record (a job position)."""

    evidence_id: str
    title: str
    dates: Optional[str] = None
    bullets: list[str] = []


class RenderedSection(BaseModel):
    """A rendered output section."""

    title: str
    section_type: str
    profile_lines: list[str] = []
    groups: list[ExperienceGroup] = []
    lines: list[str] = []


class RenderedDocument(BaseModel):
    """The deterministic render result before formatting."""

    template_name: str
    sections: list[RenderedSection] = []
    warnings: list[str] = []
    traceability: dict[str, str] = {}  # knowledge_item_id -> evidence_id


class FormattedDocument(BaseModel):
    """A rendered document plus resolved formatting metadata."""

    document: RenderedDocument
    formatting: dict[str, Any]
