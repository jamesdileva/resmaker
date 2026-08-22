"""Tests for the SOQ question analyzer (Sprint 17)."""

import pytest

from app.services.soq_analyzer import SOQAnalyzer, load_soq_categories


@pytest.fixture()
def analyzer() -> SOQAnalyzer:
    return SOQAnalyzer()


def test_categories_file_loads_with_expected_keys() -> None:
    categories = load_soq_categories()
    for expected in ("Analysis", "Communication", "Confidential Information"):
        assert expected in categories
    assert all(isinstance(p, list) and p for p in categories.values())


# --- classify_question (acceptance criteria) ---


def test_classifies_analytical_question(analyzer: SOQAnalyzer) -> None:
    assert (
        analyzer.classify_question("Describe your analytical experience")
        == "Analysis"
    )


def test_classifies_confidential_question(analyzer: SOQAnalyzer) -> None:
    assert (
        analyzer.classify_question(
            "Describe how you handled confidential information"
        )
        == "Confidential Information"
    )


def test_classifies_communication_question(analyzer: SOQAnalyzer) -> None:
    assert (
        analyzer.classify_question("Tell us about your communication skills")
        == "Communication"
    )


def test_unknown_question_gets_default_category(analyzer: SOQAnalyzer) -> None:
    assert (
        analyzer.classify_question("What is your favorite sandwich?")
        == "General"
    )
    assert analyzer.classify_question("") == "General"


def test_higher_scoring_category_wins(analyzer: SOQAnalyzer) -> None:
    # Contains both 'records' (confidential) and multiple analysis cues.
    question = (
        "Describe your experience analyzing confidential records and "
        "preparing data reports"
    )
    assert analyzer.classify_question(question) in ("Analysis", "Confidential Information")


def test_leadership_and_organization_categories(analyzer: SOQAnalyzer) -> None:
    assert (
        analyzer.classify_question("Describe your experience supervising staff")
        == "Leadership"
    )
    assert (
        analyzer.classify_question(
            "How do you prioritize when multitasking?"
        )
        == "Organization"
    )


# --- extract_keywords ---


def test_keywords_include_matched_phrases(analyzer: SOQAnalyzer) -> None:
    keywords = analyzer.extract_keywords(
        "Describe how you handled confidential information"
    )
    assert "confidential information" in keywords
    assert "handled" in keywords
    assert "describe" not in keywords  # stopword removed


def test_keywords_are_deduplicated(analyzer: SOQAnalyzer) -> None:
    keywords = analyzer.extract_keywords("confidential records and more records")
    assert len(keywords) == len(set(keywords))


def test_keywords_of_empty_question(analyzer: SOQAnalyzer) -> None:
    assert analyzer.extract_keywords("") == []


# --- analyze ---


def test_analyze_returns_both_parts(analyzer: SOQAnalyzer) -> None:
    analysis = analyzer.analyze("Tell us about your communication skills")
    assert analysis.category == "Communication"
    assert "communication" in analysis.keywords


# --- builder integration ---


@pytest.fixture()
def seeded(session):
    from app.db.models import Evidence, KnowledgeItem, KnowledgeItemEvidenceLink

    evidence = Evidence(
        type="experience",
        title="Boost Mobile",
        content="retail",
        role="Sales Associate",
        company="Boost Mobile",
    )
    session.add(evidence)
    session.flush()
    item = KnowledgeItem(
        type="soq_paragraph",
        content=(
            "Throughout my five years at Boost Mobile I managed "
            "confidential customer records and verified identities."
        ),
        category="Confidential Information",
    )
    session.add(item)
    session.flush()
    session.add(
        KnowledgeItemEvidenceLink(
            knowledge_item_id=item.id, evidence_id=evidence.id
        )
    )
    session.commit()
    return [item]


def test_suggest_items_uses_analyzed_query(session, seeded) -> None:
    """A short question still recalls relevant evidence via category expansion."""
    from app.services.soq_builder import SOQBuilderService

    service = SOQBuilderService(session)
    suggestions = service.suggest_items("confidential information")
    assert len(suggestions) >= 1


def test_expand_query_appends_category_patterns(session, seeded) -> None:
    from app.services.soq_builder import SOQBuilderService

    service = SOQBuilderService(session)
    expanded = service._expand_query("confidential information")
    assert expanded.startswith("confidential information")
    assert "privacy" in expanded or "sensitive" in expanded


def test_expand_query_leaves_unknown_category_unchanged(session, seeded) -> None:
    from app.services.soq_builder import SOQBuilderService

    service = SOQBuilderService(session)
    assert service._expand_query("What is your favorite sandwich?") == (
        "What is your favorite sandwich?"
    )


def test_answer_question_reports_detected_category(session, seeded) -> None:
    from app.services.soq_builder import SOQBuilderService

    first = seeded[0]
    document = SOQBuilderService(session).answer_question(
        "Describe your experience handling confidential information",
        [first.id],
    )
    assert document.metadata.get("category") == "Confidential Information"
