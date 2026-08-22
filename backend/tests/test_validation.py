"""Tests for the validation engine (Sprint 29)."""

import pytest

from app.models.build import BuiltDocument
from app.models.resume import ExperienceGroup, RenderedSection
from app.services.export_service import registry
from app.services.validation_service import ValidationService


def _resume_document(
    *,
    contact: bool = True,
    bullets: int = 1,
    skills: int = 3,
) -> BuiltDocument:
    profile_lines = (
        ["John Doe", "john@example.com | (909) 555-0100"] if contact else ["John Doe"]
    )
    return BuiltDocument(
        document_id="doc-resume",
        template_name="standard",
        sections=[
            RenderedSection(
                title="Summary",
                section_type="profile",
                profile_lines=profile_lines,
                groups=[],
                lines=[],
            ),
            RenderedSection(
                title="Experience",
                section_type="experience",
                profile_lines=[],
                groups=[
                    ExperienceGroup(
                        evidence_id=f"ev-{i}",
                        title=f"Job {i}",
                        dates=None,
                        bullets=[f"Did valuable work number {i}"],
                    )
                    for i in range(bullets)
                ],
                lines=[],
            ),
            RenderedSection(
                title="Skills",
                section_type="skills",
                profile_lines=[],
                groups=[],
                lines=[f"Skill {i}" for i in range(skills)],
            ),
        ],
        traceability={"item-0": "ev-0"},
        warnings=[],
    )


def _soq_document(answer_words: int) -> BuiltDocument:
    answer = " ".join(f"word{i}" for i in range(answer_words))
    return BuiltDocument(
        document_id="doc-soq",
        template_name="soq_standard",
        sections=[
            RenderedSection(
                title="Question",
                section_type="soq_question",
                profile_lines=["Describe your experience"],
                groups=[],
                lines=[],
            ),
            RenderedSection(
                title="Response",
                section_type="soq_response",
                profile_lines=[],
                groups=[],
                lines=[answer],
            ),
        ],
        traceability={"item-1": "ev-9"},
        warnings=[],
    )


@pytest.fixture()
def service() -> ValidationService:
    return ValidationService()


# --- completeness: resume ---


def test_valid_resume_passes(service: ValidationService) -> None:
    result = service.validate(_resume_document(), doc_type="resume")
    assert result.valid is True
    assert result.errors == []
    assert result.score == 1.0


def test_missing_contact_information_is_error(service: ValidationService) -> None:
    result = service.validate(_resume_document(contact=False), doc_type="resume")
    assert any(i.field == "profile" for i in result.errors)
    assert result.valid is False


def test_no_experience_bullets_is_error(service: ValidationService) -> None:
    result = service.validate(_resume_document(bullets=0), doc_type="resume")
    assert any(i.field == "experience" for i in result.errors)


def test_fewer_than_three_skills_is_error(service: ValidationService) -> None:
    result = service.validate(_resume_document(skills=2), doc_type="resume")
    assert any(i.field == "skills" for i in result.errors)


# --- completeness: soq ---


def test_short_soq_answer_is_error(service: ValidationService) -> None:
    result = service.validate(_soq_document(20), doc_type="soq")
    assert any("minimum 50" in i.message for i in result.errors)


def test_adequate_soq_answer_passes(service: ValidationService) -> None:
    result = service.validate(_soq_document(60), doc_type="soq")
    assert result.valid is True


def test_soq_over_max_words_is_length_error(service: ValidationService) -> None:
    result = service.validate(
        _soq_document(300), doc_type="soq", soq_max_words=250
    )
    assert any(i.rule == "length" and i.field == "soq_response" for i in result.errors)


# --- keyword coverage ---


def test_keyword_coverage_reports_missing(service: ValidationService) -> None:
    document = _resume_document()
    result = service.validate(
        document,
        doc_type="resume",
        keywords=["work", "skill", "excel", "sql"],
    )

    coverage_issues = [i for i in result.warnings if i.rule == "keyword_coverage"]
    assert len(coverage_issues) == 1
    message = coverage_issues[0].message
    assert "50%" in message  # work + skill found, excel + sql missing
    assert "excel" in message and "sql" in message
    # Warnings are non-blocking.
    assert result.valid is True


def test_full_keyword_coverage_produces_no_warning(service: ValidationService) -> None:
    document = _resume_document()
    result = service.validate(document, doc_type="resume", keywords=["valuable"])
    assert not [i for i in result.warnings if i.rule == "keyword_coverage"]


# --- evidence traceability ---


def test_unlinked_group_warns(service: ValidationService) -> None:
    document = _resume_document()
    document.sections[1].groups.append(
        ExperienceGroup(
            evidence_id="_unlinked",
            title="Mystery Job",
            dates=None,
            bullets=["Orphaned content here"],
        )
    )
    result = service.validate(document, doc_type="resume")
    trace_warnings = [
        i for i in result.warnings if i.rule == "evidence_traceability"
    ]
    assert len(trace_warnings) == 1
    assert "1 content block" in trace_warnings[0].message


# --- length: resume / duty ---


def test_resume_over_max_words_is_error(service: ValidationService) -> None:
    document = _resume_document()
    filler = " ".join(["filler"] * 1200)
    document.sections[2].lines.append(filler)
    result = service.validate(document, doc_type="resume")
    assert any(i.rule == "length" for i in result.errors)


def test_duty_bullet_over_limit_warns(service: ValidationService) -> None:
    document = BuiltDocument(
        document_id="doc-duty",
        template_name="duty_standard",
        sections=[
            RenderedSection(
                title="Duty Statement Responses",
                section_type="duty_response",
                profile_lines=[],
                groups=[
                    ExperienceGroup(
                        evidence_id="ev-1",
                        title="Duty 1: long duty",
                        dates=None,
                        bullets=[" ".join(["word"] * 250)],
                    )
                ],
                lines=[],
            )
        ],
        traceability={"item": "ev-1"},
        warnings=[],
    )
    result = service.validate(document, doc_type="duty")
    assert result.valid is True  # warnings only
    assert any(i.rule == "length" for i in result.warnings)


# --- score behavior ---


def test_score_decreases_with_errors_and_warnings(service: ValidationService) -> None:
    perfect = service.validate(_resume_document(), doc_type="resume")
    flawed = service.validate(_resume_document(contact=False), doc_type="resume")
    assert perfect.score == 1.0
    assert flawed.score < perfect.score


def test_unknown_doc_type_raises(service: ValidationService) -> None:
    with pytest.raises(ValueError):
        service.validate(_resume_document(), doc_type="newsletter")


# --- endpoint ---


def test_validate_endpoint_happy_path(client) -> None:
    registry.register(_resume_document())
    response = client.post(
        "/api/v1/validate/",
        json={"document_id": "doc-resume", "doc_type": "resume"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is True
    assert {"valid", "errors", "warnings", "score"} <= set(body.keys())


def test_validate_endpoint_with_keywords(client) -> None:
    registry.register(_resume_document())
    response = client.post(
        "/api/v1/validate/",
        json={
            "document_id": "doc-resume",
            "doc_type": "resume",
            "keywords": ["valuable"],
        },
    )
    assert response.status_code == 200
    assert response.json()["valid"] is True


def test_validate_endpoint_blocks_invalid(client) -> None:
    registry.register(_resume_document(contact=False))
    response = client.post(
        "/api/v1/validate/", json={"document_id": "doc-resume"}
    )
    body = response.json()
    assert body["valid"] is False
    assert len(body["errors"]) >= 1


def test_validate_endpoint_unknown_document_404(client) -> None:
    response = client.post("/api/v1/validate/", json={"document_id": "missing"})
    assert response.status_code == 404


def test_validate_endpoint_bad_doc_type(client) -> None:
    registry.register(_resume_document())
    response = client.post(
        "/api/v1/validate/",
        json={"document_id": "doc-resume", "doc_type": "poem"},
    )
    assert response.status_code == 400
