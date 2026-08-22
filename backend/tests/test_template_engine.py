"""Tests for the resume template engine (Sprint 13)."""

import pytest

from app.db.models import Evidence, KnowledgeItem
from app.services.template_engine import TemplateEngine


@pytest.fixture()
def engine() -> TemplateEngine:
    return TemplateEngine()


def _bullet(content: str, item_id: str, evidence_id: str | None = None) -> KnowledgeItem:
    metadata = {"evidence_id": evidence_id} if evidence_id else {}
    return KnowledgeItem(
        id=item_id,
        type="resume_bullet",
        content=content,
        metadata_json=metadata,
    )


def _evidence(evidence_id: str, title: str, role: str) -> Evidence:
    return Evidence(
        id=evidence_id,
        type="experience",
        title=title,
        content="work",
        role=role,
        company=title,
        start_date="2019-01-01",
        end_date="2022-12-31",
    )


PROFILE = {
    "name": "John Doe",
    "location": "Hesperia, CA",
    "phone": "(909) 555-0100",
    "email": "john@example.com",
    "summary": "Customer service professional.",
}


# --- load_template ---


def test_load_standard_template(engine: TemplateEngine) -> None:
    template = engine.load_template("standard")
    assert template.name == "standard"
    section_types = [s.type for s in template.sections]
    assert section_types == ["profile", "experience", "skills", "projects"]
    assert template.formatting["font"] == "Calibri"


def test_load_unknown_template_raises(engine: TemplateEngine) -> None:
    with pytest.raises(ValueError):
        engine.load_template("does-not-exist")


# --- render: profile ---


def test_render_profile_section_from_user_profile(engine: TemplateEngine) -> None:
    template = engine.load_template("standard")
    result = engine.render(template, [], [], PROFILE)

    profile_section = result.sections[0]
    assert profile_section.section_type == "profile"
    assert profile_section.profile_lines[0] == "John Doe"
    assert "(909) 555-0100" in profile_section.profile_lines[1]
    assert any("Customer service" in line for line in profile_section.profile_lines)


# --- render: experience grouping ---


def test_render_groups_bullets_by_evidence(engine: TemplateEngine) -> None:
    template = engine.load_template("standard")
    items = [
        _bullet("Bullet A1", "i1", "ev1"),
        _bullet("Bullet A2", "i2", "ev1"),
        _bullet("Bullet B1", "i3", "ev2"),
    ]
    evidence = [
        _evidence("ev1", "Boost Mobile", "Sales Associate"),
        _evidence("ev2", "County Office", "Data Clerk"),
    ]

    result = engine.render(
        template, items, evidence, PROFILE,
        item_links={"i1": "ev1", "i2": "ev1", "i3": "ev2"},
    )

    experience = next(s for s in result.sections if s.section_type == "experience")
    assert len(experience.groups) == 2

    first, second = experience.groups
    assert first.title == "Sales Associate"
    assert first.evidence_id == "ev1"
    assert first.bullets == ["Bullet A1", "Bullet A2"]
    assert first.dates == "2019-01-01 - 2022-12-31"

    assert second.bullets == ["Bullet B1"]


def test_render_traceability_maps_items_to_evidence(engine: TemplateEngine) -> None:
    template = engine.load_template("standard")
    items = [_bullet("A", "i1", "ev1"), _bullet("B", "i2", "ev2")]
    evidence = [
        _evidence("ev1", "Job One", "Role One"),
        _evidence("ev2", "Job Two", "Role Two"),
    ]
    result = engine.render(
        template, items, evidence, PROFILE,
        item_links={"i1": "ev1", "i2": "ev2"},
    )
    assert result.traceability == {"i1": "ev1", "i2": "ev2"}


def test_unlinked_bullets_fall_into_unlinked_group(engine: TemplateEngine) -> None:
    template = engine.load_template("standard")
    items = [_bullet("Orphan bullet", "i1")]
    result = engine.render(template, items, [], PROFILE)
    experience = next(s for s in result.sections if s.section_type == "experience")
    assert len(experience.groups) == 1
    assert experience.groups[0].bullets == ["Orphan bullet"]
    # No evidence mapping means no traceability entry.
    assert result.traceability == {}


# --- render: skills / projects separation + empty omission ---


def test_skills_and_projects_rendered_separately(engine: TemplateEngine) -> None:
    template = engine.load_template("standard")
    skills = [KnowledgeItem(id=f"s{i}", type="skill", content=t)
              for i, t in enumerate(["Excel", "SQL", "CRM"])]
    projects = [KnowledgeItem(id="p1", type="project", content="Built an app")]
    bullets = [_bullet("B", "i1", "ev1")]
    evidence = [_evidence("ev1", "Job", "Role")]

    result = engine.render(template, bullets + skills + projects, evidence, PROFILE)

    by_type = {s.section_type: s for s in result.sections}
    assert by_type["skills"].lines == ["Excel", "SQL", "CRM"]
    assert by_type["projects"].lines == ["Built an app"]
    assert by_type["experience"].groups[0].title == "Role"


def test_empty_sections_omitted_with_warnings(engine: TemplateEngine) -> None:
    template = engine.load_template("standard")
    result = engine.render(template, [], [], PROFILE)

    rendered_types = {s.section_type for s in result.sections}
    assert "experience" not in rendered_types
    assert "skills" not in rendered_types
    assert "projects" not in rendered_types

    warned = " ".join(result.warnings)
    for title in ("Experience", "Skills", "Projects"):
        assert title in warned


# --- apply_formatting ---


def test_apply_formatting_merges_defaults(engine: TemplateEngine) -> None:
    template = engine.load_template("standard")
    document = engine.render(template, [], [], PROFILE)

    formatted = engine.apply_formatting(document, {"font_size": 10})
    assert formatted.document is document
    assert formatted.formatting["font_size"] == 10
    assert formatted.formatting["font"] == "Calibri"  # default preserved


def test_apply_formatting_without_overrides(engine: TemplateEngine) -> None:
    template = engine.load_template("standard")
    document = engine.render(template, [], [], PROFILE)
    formatted = engine.apply_formatting(document)
    assert formatted.formatting == {
        "font": "Calibri",
        "font_size": 11,
        "line_spacing": 1.15,
    }
