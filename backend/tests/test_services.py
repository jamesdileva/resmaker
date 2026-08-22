"""Tests for the ExtractionService (Sprint 10)."""

from pathlib import Path

import pytest

from app.models.knowledge import ParagraphType
from app.parsers.docx_parser import DocxParser
from app.parsers.txt_parser import TxtParser
from app.services.extraction_service import ExtractionService

FIXTURES = Path(__file__).resolve().parent / "fixtures"


@pytest.fixture()
def service() -> ExtractionService:
    return ExtractionService()


@pytest.fixture()
def resume_paragraphs() -> list:
    return DocxParser().parse(str(FIXTURES / "sample_resume.docx")).paragraphs


@pytest.fixture()
def soq_paragraphs() -> list:
    return DocxParser().parse(str(FIXTURES / "sample_soq.docx")).paragraphs


# --- classify_paragraph ---


def test_classifies_heading(service: ExtractionService, resume_paragraphs) -> None:
    heading = next(p for p in resume_paragraphs if p.is_heading)
    assert (
        service.classify_paragraph(heading.text, heading) == ParagraphType.HEADING
    )


def test_classifies_resume_bullet(service: ExtractionService, resume_paragraphs) -> None:
    bullet = next(p for p in resume_paragraphs if p.is_bullet)
    assert (
        service.classify_paragraph(bullet.text, bullet)
        == ParagraphType.RESUME_BULLET
    )


def test_classifies_soq_question(
    service: ExtractionService, soq_paragraphs
) -> None:
    question = next(
        p for p in soq_paragraphs if p.is_heading and "Question" in p.text
    )
    assert (
        service.classify_paragraph(question.text, question)
        == ParagraphType.SOQ_QUESTION
    )


def test_classifies_soq_answer_heuristic(service: ExtractionService) -> None:
    answer = (
        "Throughout my time there I managed confidential records and "
        "processed payments daily while maintaining compliance."
    )
    assert (
        service.classify_paragraph(answer) == ParagraphType.SOQ_ANSWER
    )


def test_classifies_question_by_text_only(service: ExtractionService) -> None:
    assert (
        service.classify_paragraph("Question 1: Describe your experience")
        == ParagraphType.SOQ_QUESTION
    )
    assert (
        service.classify_paragraph("Describe your analytical background")
        == ParagraphType.SOQ_QUESTION
    )


def test_classifies_normal_text(service: ExtractionService) -> None:
    assert (
        service.classify_paragraph("Proficient in Excel, SQL dashboards, and CRM tools.")
        == ParagraphType.NORMAL_TEXT
    )
    assert service.classify_paragraph("") == ParagraphType.NORMAL_TEXT


# --- extract_resume_bullets ---


def test_resume_bullets_grouped_under_jobs(
    service: ExtractionService, resume_paragraphs
) -> None:
    groups = service.extract_resume_bullets(resume_paragraphs)
    assert len(groups) == 2

    first = groups[0]
    assert first.role == "Sales Associate"
    assert first.company == "Boost Mobile"
    assert first.dates == "2019-2022"
    assert len(first.bullets) == 4
    assert any("confidential customer records" in b for b in first.bullets)
    assert any("cash drawers" in b for b in first.bullets)

    second = groups[1]
    assert second.role == "Data Entry Clerk"
    assert second.company == "County Office"
    assert second.dates == "2017-2019"
    assert len(second.bullets) == 2


def test_parse_job_heading_variants(service: ExtractionService) -> None:
    heading = service.parse_job_heading("Analyst - Dept of Justice (2020-2023)")
    assert heading.role == "Analyst"
    assert heading.company == "Dept of Justice"
    assert heading.dates == "2020-2023"

    no_dates = service.parse_job_heading("Clerk - City Hall")
    assert no_dates.dates is None
    assert service.parse_job_heading("John Doe") is None


# --- extract_soq_paragraphs ---


def test_soq_pairs_questions_with_answers(
    service: ExtractionService, soq_paragraphs
) -> None:
    pairs = service.extract_soq_paragraphs(soq_paragraphs)
    assert len(pairs) == 2

    assert pairs[0].question.startswith("Question 1")
    assert "confidential" in pairs[0].answer.lower()

    assert pairs[1].question.startswith("Question 2")
    assert "analysis of intake reports" in pairs[1].answer.lower()


# --- extract_skills ---


def test_skills_from_cue_phrase(service: ExtractionService) -> None:
    skills = service.extract_skills(
        "Proficient in Excel, SQL dashboards, and CRM tools."
    )
    assert "excel" in skills
    assert any("sql" in skill for skill in skills)


def test_skills_from_lexicon(service: ExtractionService) -> None:
    skills = service.extract_skills("Daily work involved data analysis and filing systems.")
    assert "data analysis" in skills
    assert "filing systems" in skills


def test_skills_deduplicated_and_bounded(service: ExtractionService) -> None:
    skills = service.extract_skills("Excel excel EXCEL; skilled in Excel.")
    assert skills.count("excel") == 1


# --- extract_metrics ---


def test_metrics_percent_dollar_count(service: ExtractionService) -> None:
    text = (
        "Maintained a 95% satisfaction rating, processed $1,200 in daily "
        "payments, filed over 500 sensitive documents."
    )
    metrics = service.extract_metrics(text)
    kinds = {(m.kind, m.value) for m in metrics}
    assert ("percent", "95%") in kinds
    assert ("dollar", "$1,200") in kinds
    assert any(kind == "count" and "500" in value for kind, value in kinds)


def test_metrics_empty_text(service: ExtractionService) -> None:
    assert service.extract_metrics("No numbers here at all.") == []


# --- assign_category ---


def test_assign_category_confidential(service: ExtractionService) -> None:
    category = service.assign_category(
        "Handled confidential customer records with privacy compliance",
        ParagraphType.RESUME_BULLET,
    )
    assert category == "Confidential Information"


def test_assign_category_analysis(service: ExtractionService) -> None:
    category = service.assign_category(
        "Performed data analysis on weekly reports using Excel dashboards",
        ParagraphType.RESUME_BULLET,
    )
    assert category == "Analysis"


def test_assign_category_customer_service(service: ExtractionService) -> None:
    category = service.assign_category(
        "Resolved customer complaints and answered inquiries",
        ParagraphType.RESUME_BULLET,
    )
    assert category == "Customer Service"


def test_assign_category_general_fallback(service: ExtractionService) -> None:
    assert (
        service.assign_category("Random unrelated content", ParagraphType.NORMAL_TEXT)
        == "General"
    )


# --- extract_keywords ---


def test_keywords_cleaned_and_stopwords_removed(service: ExtractionService) -> None:
    keywords = service.extract_keywords(
        "Handled confidential records and maintained the filing systems."
    )
    assert "handled" in keywords
    assert "confidential" in keywords
    assert "records" in keywords
    for stopword in ("and", "the", "was"):
        assert stopword not in keywords
    assert len(keywords) == len(set(keywords))


def test_txt_fixture_classification_flow(service: ExtractionService) -> None:
    """Duty statement lines classify as normal text (not bullets/headings)."""
    parsed = TxtParser().parse(str(FIXTURES / "sample_duty.txt"))
    kinds = [
        service.classify_paragraph(p.text, p) for p in parsed.paragraphs
    ]
    assert kinds[0] == ParagraphType.NORMAL_TEXT
    assert all(kind == ParagraphType.NORMAL_TEXT for kind in kinds[1:])
