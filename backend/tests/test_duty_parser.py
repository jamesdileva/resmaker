"""Tests for the duty statement parser (Sprint 19)."""

import pytest

from app.services.duty_statement_parser import DutyStatementParser


@pytest.fixture()
def parser() -> DutyStatementParser:
    return DutyStatementParser()


NUMBERED_POSTING = """Duty Statement - Office Technician

1. Review and process confidential documents daily.
2. Prepare weekly statistical reports using Excel.
3. Answer customer inquiries via phone and email.
4. Maintain office filing systems and supply inventory.
"""

BULLETED_POSTING = """Staff Services Analyst Duties

• Analyze budget data and prepare summary reports for management
• Serve as a point of contact for customer complaints and resolution
- Coordinate meetings and maintain calendars for the unit
* Draft written correspondence to stakeholders and the public
"""

INDENTED_POSTING = """Key Responsibilities:

    1) Review confidential records with discretion and accuracy.
        2) Process data requests within required timelines.

  • Answer public inquiries in person and by telephone
"""


def test_parse_numbered_duties(parser: DutyStatementParser) -> None:
    duties = parser.parse(NUMBERED_POSTING)
    assert len(duties) == 4
    assert duties[0].text == "Review and process confidential documents daily."
    assert duties[0].order_index == 0
    assert duties[3].order_index == 3
    assert "Maintain office filing systems" in duties[3].text


def test_parse_bulleted_duties_all_markers(parser: DutyStatementParser) -> None:
    duties = parser.parse(BULLETED_POSTING)
    assert len(duties) == 4
    assert all(d.text and not d.text.startswith(("•", "-", "*")) for d in duties)
    assert any("budget data" in d.text for d in duties)


def test_parse_indented_and_mixed_formats(parser: DutyStatementParser) -> None:
    duties = parser.parse(INDENTED_POSTING)
    assert len(duties) == 3
    texts = [d.text for d in duties]
    assert any(texts[0] == t for t in ["Review confidential records with discretion and accuracy."])
    assert any("Answer public inquiries" in t for t in texts)


def test_parse_paragraph_prose_splits_sentences(parser: DutyStatementParser) -> None:
    prose = (
        "The incumbent will review incoming claims documentation and verify "
        "eligibility requirements. The position requires preparing detailed "
        "written reports summarizing case findings for management review. "
        "Additional duties include answering telephone inquiries from the "
        "public regarding application status."
    )
    duties = parser.parse(prose)
    assert len(duties) == 3
    assert all(len(d.text.split()) >= 6 for d in duties)


def test_short_fragments_and_headers_skipped(parser: DutyStatementParser) -> None:
    text = """Duty Statement

1. Filing.

1. Review and process confidential documents daily.
"""
    duties = parser.parse(text)
    assert len(duties) == 1
    assert "confidential" in duties[0].text


def test_requirements_have_categories(parser: DutyStatementParser) -> None:
    duties = parser.parse(NUMBERED_POSTING)
    by_text = {d.text: d.category for d in duties}
    confidential = next(c for t, c in by_text.items() if "confidential" in t.lower())
    analysis = next(c for t, c in by_text.items() if "statistical reports" in t.lower())
    service = next(c for t, c in by_text.items() if "customer inquiries" in t.lower())

    assert confidential == "Confidential Information"
    assert analysis == "Analysis"
    assert service == "Customer Service"


def test_requirements_have_keywords(parser: DutyStatementParser) -> None:
    duties = parser.parse(NUMBERED_POSTING)
    first = duties[0]
    assert first.keywords
    assert "confidential" in first.keywords
    # Stopwords are removed.
    assert "and" not in first.keywords


def test_extract_keywords_aggregates_across_requirements(
    parser: DutyStatementParser,
) -> None:
    duties = parser.parse(NUMBERED_POSTING)
    aggregated = parser.extract_keywords(duties)
    assert "confidential" in aggregated
    assert "excel" in aggregated or "reports" in aggregated
    assert len(aggregated) == len(set(aggregated))


def test_empty_input_returns_no_requirements(parser: DutyStatementParser) -> None:
    assert parser.parse("") == []
    assert parser.parse("   \n  \n") == []


def test_realistic_calcareers_style_posting(parser: DutyStatementParser) -> None:
    posting = """Office Technician
$3,200 - $4,100 per month

Under the direction of the Administrative Officer I, the Office Technician:

1. Reviews and processes incoming confidential correspondence, ensuring
proper routing of sensitive material to appropriate staff.
2. Maintains accurate logs and databases tracking document status using
Microsoft Excel and departmental systems.
3. Provides excellent customer service by responding to telephone and
in-person inquiries from the public.
"""
    duties = parser.parse(posting)
    assert len(duties) == 3
    categories = [d.category for d in duties]
    assert categories[0] == "Confidential Information"
    assert "Analysis" in categories[1] or categories[1] == "General"
    assert categories[2] == "Customer Service"
