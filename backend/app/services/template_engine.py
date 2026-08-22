"""JSON-based template engine for resume assembly."""

import json
from pathlib import Path
from typing import Optional

from app.models.resume import (
    ExperienceGroup,
    FormattedDocument,
    RenderedDocument,
    RenderedSection,
    ResumeTemplate,
)
from app.db.models import Evidence, KnowledgeItem

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "data" / "resume_templates"

DEFAULT_FORMATTING: dict = {
    "font": "Calibri",
    "font_size": 11,
    "line_spacing": 1.15,
}


class TemplateEngine:
    """Loads JSON templates and renders knowledge items into sections."""

    @staticmethod
    def load_template(name: str) -> ResumeTemplate:
        """Load and validate a template definition by name."""
        path = TEMPLATES_DIR / f"{name}.json"
        if not path.exists():
            raise ValueError(f"Unknown template: {name}")
        with open(path, encoding="utf-8") as handle:
            payload = json.load(handle)
        return ResumeTemplate.model_validate(payload)

    def render(
        self,
        template: ResumeTemplate,
        items: list[KnowledgeItem],
        evidence: list[Evidence],
        user_profile: dict,
        item_links: Optional[dict[str, str]] = None,
    ) -> RenderedDocument:
        """Render sections in template order; omit empty ones with warnings."""
        item_links = item_links or {}
        evidence_by_id = {record.id: record for record in evidence}
        rendered = RenderedDocument(template_name=template.name)
        used_item_ids: set[str] = set()

        for section_def in template.sections:
            if section_def.type == "profile":
                rendered.sections.append(self._render_profile(section_def, user_profile))
                continue

            section_items = [
                item
                for item in items
                if not section_def.item_types or item.type in section_def.item_types
            ]
            if not section_items:
                rendered.warnings.append(f"Section '{section_def.title}' has no content; omitted")
                continue

            if section_def.group_by == "evidence_id":
                groups = self._group_by_evidence(
                    section_items, item_links, evidence_by_id
                )
                rendered.sections.append(
                    RenderedSection(
                        title=section_def.title,
                        section_type=section_def.type,
                        groups=groups,
                    )
                )
            else:
                rendered.sections.append(
                    RenderedSection(
                        title=section_def.title,
                        section_type=section_def.type,
                        lines=[item.content for item in section_items],
                    )
                )

            for item in section_items:
                used_item_ids.add(item.id)

        # Traceability: every used item that maps to an evidence record.
        traceability = {}
        for item in items:
            if item.id in used_item_ids:
                evidence_id = item_links.get(item.id) or item.metadata_json.get("evidence_id")
                if evidence_id:
                    traceability[item.id] = evidence_id
        rendered.traceability = traceability

        return rendered

    def _render_profile(self, section_def, user_profile: dict) -> RenderedSection:
        lines: list[str] = []
        name = user_profile.get("name")
        if name:
            lines.append(str(name))
        contact_parts = [
            str(user_profile[key])
            for key in ("location", "phone", "email", "linkedin")
            if user_profile.get(key)
        ]
        if contact_parts:
            lines.append("  |  ".join(contact_parts))
        summary = user_profile.get("summary")
        if summary:
            lines.append(str(summary))
        return RenderedSection(
            title=section_def.title,
            section_type=section_def.type,
            profile_lines=lines,
        )

    def _group_by_evidence(
        self,
        items: list[KnowledgeItem],
        item_links: dict[str, str],
        evidence_by_id: dict[str, Evidence],
    ) -> list[ExperienceGroup]:
        """Group items under their evidence records preserving first-seen order."""
        ordered_group_ids: list[str] = []
        grouped: dict[str, list[str]] = {}

        for item in items:
            evidence_id = item_links.get(item.id) or item.metadata_json.get(
                "evidence_id"
            )
            key = evidence_id if evidence_id else "_unlinked"
            if key not in grouped:
                grouped[key] = []
                ordered_group_ids.append(key)
            grouped[key].append(item.content)

        groups: list[ExperienceGroup] = []
        for key in ordered_group_ids:
            record = evidence_by_id.get(key)
            if record is not None:
                title = record.role or record.title
                dates = None
                if record.start_date or record.end_date:
                    dates = f"{record.start_date or ''} - {record.end_date or ''}".strip(" -")
            else:
                title = key.replace("_", " ").title() if key == "_unlinked" else key
                dates = None
            groups.append(
                ExperienceGroup(
                    evidence_id=key,
                    title=title,
                    dates=dates,
                    bullets=grouped[key],
                )
            )
        return groups

    def apply_formatting(
        self, document: RenderedDocument, formatting: Optional[dict] = None
    ) -> FormattedDocument:
        """Attach resolved formatting metadata (metadata-only in the MVP)."""
        merged = {**DEFAULT_FORMATTING, **(formatting or {})}
        return FormattedDocument(document=document, formatting=merged)
