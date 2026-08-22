"""Tests for the search and match endpoints (Sprint 22)."""

import pytest
from sqlmodel import Session

from app.db.models import Evidence, KnowledgeItem, KnowledgeItemEvidenceLink
from app.services.matching_service import MatchingService, stars_for_score


def _seed(session: Session):
    evidence = Evidence(
        type="experience",
        title="Boost Mobile",
        content="retail work",
        role="Sales Associate",
        company="Boost Mobile",
    )
    session.add(evidence)
    session.flush()

    items = [
        KnowledgeItem(
            type="resume_bullet",
            content="Handled confidential customer records daily",
            category="Confidential Information",
        ),
        KnowledgeItem(
            type="soq_paragraph",
            content="Performed data analysis and produced weekly reports",
            category="Analysis",
        ),
        KnowledgeItem(
            type="resume_bullet",
            content="Resolved customer complaints quickly",
            category="Customer Service",
        ),
    ]
    for index, item in enumerate(items):
        session.add(item)
        session.flush()
        if index == 0:
            session.add(
                KnowledgeItemEvidenceLink(
                    knowledge_item_id=item.id, evidence_id=evidence.id
                )
            )
    session.commit()
    return evidence, items


@pytest.fixture()
def seeded(session: Session):
    return _seed(session)


# --- MatchingService ---


def test_stars_for_score_thresholds() -> None:
    assert stars_for_score(0.95) == 5
    assert stars_for_score(0.85) == 4
    assert stars_for_score(0.75) == 3
    assert stars_for_score(0.65) == 2
    assert stars_for_score(0.55) == 1
    assert stars_for_score(0.40) == 0


def test_match_query_ranks_and_enriches(session: Session, seeded) -> None:
    service = MatchingService(session)
    results = service.match_query(query="confidential customer")

    assert len(results) >= 1
    top = results[0]
    assert top.star_rating >= 1
    assert "confidential" in top.knowledge_item.content.lower()
    # First item is linked to the seeded evidence.
    linked = next((r for r in results if r.evidence_ids), None)
    assert linked is not None


def test_match_query_filters_by_type_and_category(session: Session, seeded) -> None:
    service = MatchingService(session)
    soq_only = service.match_query(query="data analysis", item_types=["soq_paragraph"])
    assert all(r.knowledge_item.type == "soq_paragraph" for r in soq_only)

    by_category = service.match_query(categories=["Customer Service"])
    assert all(r.knowledge_item.category == "Customer Service" for r in by_category)


def test_match_query_min_star_filtering(session: Session, seeded) -> None:
    service = MatchingService(session)
    strong = service.match_query(query="confidential customer", min_star_rating=4)
    assert all(r.star_rating >= 4 for r in strong)


def test_empty_query_returns_recent_items(session: Session, seeded) -> None:
    service = MatchingService(session)
    browse = service.match_query(query="")
    assert len(browse) == 3


def test_sort_by_date_orders_newest_first(session: Session, seeded) -> None:
    _, items = seeded
    service = MatchingService(session)
    ordered = service.match_query(query="", sort_by="date")
    dates = [r.knowledge_item.created_at for r in ordered]
    assert dates == sorted(dates, reverse=True)


# --- Search API ---


def test_search_endpoint_with_filters(client, api_session: Session) -> None:
    _seed(api_session)

    response = client.post(
        "/api/v1/search/",
        json={"query": "confidential customer", "limit": 10},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 1
    first = body["items"][0]
    assert {"knowledge_item", "score", "star_rating", "evidence_ids"} <= set(first.keys())


def test_search_endpoint_browse_mode(client, api_session: Session) -> None:
    _seed(api_session)
    response = client.post("/api/v1/search/", json={})
    assert response.status_code == 200
    assert response.json()["total"] == 3


def test_search_endpoint_star_filter(client, api_session: Session) -> None:
    _seed(api_session)
    response = client.post(
        "/api/v1/search/", json={"min_star_rating": 5}
    )
    body = response.json()
    assert all(item["star_rating"] == 5 for item in body["items"]) or body["total"] == 0


# --- Match API ---


def test_match_endpoint_with_posting_id(client, api_session: Session) -> None:
    from app.db.models import JobPosting

    _seed(api_session)
    posting = JobPosting(
        title="Records Clerk",
        raw_text="Handle confidential records and resolve complaints",
    )
    api_session.add(posting)
    api_session.commit()

    response = client.post(
        "/api/v1/match/", json={"job_posting_id": posting.id, "top_k": 5}
    )
    assert response.status_code == 200
    matches = response.json()["matches"]
    assert len(matches) >= 1
    scores = [m["score"] for m in matches]
    assert scores == sorted(scores, reverse=True)


def test_match_endpoint_unknown_posting_404(client) -> None:
    response = client.post(
        "/api/v1/match/", json={"job_posting_id": "missing"}
    )
    assert response.status_code == 404


def test_match_endpoint_requires_input(client) -> None:
    response = client.post("/api/v1/match/", json={"query": ""})
    assert response.status_code == 400
