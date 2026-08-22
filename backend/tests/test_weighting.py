"""Tests for historical success weighting (Sprint 26)."""

import pytest
from sqlmodel import Session

from app.db.models import (
    Application,
    ApplicationEvidenceLink,
    JobPosting,
    KnowledgeItem,
)
from app.services.historical_weighting import HistoricalWeightingService
from app.services.matching_service import MatchingService


def _seed_with_history(session: Session) -> tuple[KnowledgeItem, KnowledgeItem]:
    """Two identical-content items: one with offer history, one without."""
    winner = KnowledgeItem(
        type="resume_bullet",
        content="Handled confidential records and resolved customer complaints",
    )
    loser = KnowledgeItem(
        type="resume_bullet",
        content="Handled confidential records and resolved customer complaints",
        category=None,
    )
    session.add_all([winner, loser])
    session.flush()

    posting = JobPosting(title="Role", raw_text="duties")
    session.add(posting)
    session.flush()
    application = Application(job_posting_id=posting.id)
    session.add(application)
    session.flush()
    session.add(
        ApplicationEvidenceLink(
            application_id=application.id,
            knowledge_item_id=winner.id,
            used_in_resume=True,
            result="offer",
        )
    )
    session.commit()
    return winner, loser


def test_calculate_weight_matches_repository_formula(session: Session) -> None:
    from app.repositories.application import ApplicationRepository

    winner, _ = _seed_with_history(session)
    service = HistoricalWeightingService(session)
    expected = ApplicationRepository(session).get_success_weight(winner.id)
    weight = service.calculate_weight(winner.id)
    assert weight == pytest.approx(expected)
    assert 0.0 < weight <= 0.3 + 1e-9


def test_bulk_weights_cover_history_and_zero_defaults(session: Session) -> None:
    winner, loser = _seed_with_history(session)
    weights = HistoricalWeightingService(session).calculate_weights_bulk(
        [winner.id, loser.id]
    )
    # offer -> interview_rate 1.0 * 0.1 + offer_rate 1.0 * 0.2 = 0.3
    assert weights[winner.id] == pytest.approx(0.3)
    assert weights.get(loser.id, 0.0) == 0.0


def test_update_weights_reflects_new_results(session: Session) -> None:
    winner, _ = _seed_with_history(session)
    service = HistoricalWeightingService(session)
    before = service.update_weights([winner.id])

    # A rejection arrives, diluting the perfect record.
    posting = JobPosting(title="R2", raw_text="d")
    application = Application(job_posting_id=posting.id)
    session.add_all([posting])
    session.commit()
    session.add(application)
    session.commit()
    session.add(
        ApplicationEvidenceLink(
            application_id=application.id,
            knowledge_item_id=winner.id,
            result="rejected",
        )
    )
    session.commit()

    after = service.update_weights([winner.id])
    assert after[winner.id] < before[winner.id]


def test_match_query_applies_weighting_to_identical_items(
    session: Session,
) -> None:
    """Same content, different history: the offer-backed item ranks first."""
    winner, loser = _seed_with_history(session)
    results = MatchingService(session).match_query(query="confidential records")

    assert len(results) >= 2
    ids = [r.knowledge_item.id for r in results]
    assert ids.index(winner.id) < ids.index(loser.id)
    assert results[ids.index(winner.id)].score > results[
        ids.index(loser.id)
    ].score


def test_tfidf_pipeline_scores_via_matching_service(session: Session) -> None:
    """TF-IDF path ranks partial-overlap content sensibly."""
    items = [
        KnowledgeItem(
            type="soq_paragraph",
            content="Performed weekly data analysis and built Excel dashboards",
        ),
        KnowledgeItem(
            type="soq_paragraph",
            content="Answered telephones and greeted visitors at the front desk",
        ),
    ]
    session.add_all(items)
    session.commit()

    results = MatchingService(session).match_query(
        query="data analysis dashboards"
    )
    assert results
    assert "data analysis" in results[0].knowledge_item.content


# --- Applications endpoint records evidence usage ---


def test_result_endpoint_records_evidence_usage(client, api_session: Session) -> None:
    item = KnowledgeItem(type="resume_bullet", content="Did a thing")
    api_session.add(item)
    api_session.flush()
    posting = JobPosting(title="Role", raw_text="duties")
    api_session.add(posting)
    api_session.commit()
    application = Application(job_posting_id=posting.id)
    api_session.add(application)
    api_session.commit()
    app_id = application.id

    response = client.post(
        f"/api/v1/applications/{app_id}/result",
        json={
            "status": "interview",
            "evidence_usage": [
                {"knowledge_item_id": item.id, "used_in_resume": True}
            ],
        },
    )
    assert response.status_code == 200

    api_session.expire_all()
    from sqlmodel import select

    from app.db.models import ApplicationEvidenceLink

    links = list(
        api_session.exec(select(ApplicationEvidenceLink)).all()
    )
    assert len(links) == 1
    assert links[0].result == "interview"
    assert links[0].used_in_resume is True

    # The recorded usage now feeds weighting.
    weight = HistoricalWeightingService(api_session).calculate_weight(item.id)
    assert weight > 0.0
