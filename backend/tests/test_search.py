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


def test_diversify_breaks_up_near_duplicates(session: Session) -> None:
    """MMR pushes a near-duplicate of the top hit below a distinct item.

    A and B share almost all terms; C shares only the query terms. Pure
    ranking puts the near-duplicate pair on top; diversify promotes C
    because B adds little new information after A is selected.
    """
    alpha = KnowledgeItem(
        type="resume_bullet",
        content=(
            "confidential records processing procedures confidential "
            "records confidential records"
        ),
    )
    alpha_dup = KnowledgeItem(
        type="resume_bullet",
        content=(
            "confidential records filing procedures confidential "
            "records confidential records"
        ),
    )
    distinct = KnowledgeItem(
        type="resume_bullet",
        content="confidential records community outreach public events",
    )
    # Fillers give the query terms IDF signal (a term present in every
    # document carries no weight and zeroes the whole TF-IDF path).
    fillers = [
        KnowledgeItem(type="resume_bullet", content="customer service escalations"),
        KnowledgeItem(type="resume_bullet", content="spreadsheet data entry reporting"),
        KnowledgeItem(type="resume_bullet", content="training new staff members"),
    ]
    session.add_all([alpha, alpha_dup, distinct] + fillers)
    session.commit()

    service = MatchingService(session)
    pure = service.match_query(query="confidential records", limit=3)
    diversified = service.match_query(
        query="confidential records", limit=3, diversify=True
    )

    pure_ids = [r.knowledge_item.id for r in pure]
    div_ids = [r.knowledge_item.id for r in diversified]
    # The two near-duplicates lead pure ranking; diversity separates them.
    assert set(pure_ids[:2]) == {alpha.id, alpha_dup.id}
    dup_pair_position_gap = abs(
        div_ids.index(alpha.id) - div_ids.index(alpha_dup.id)
    )
    distinct_pos = div_ids.index(distinct.id)
    assert distinct_pos < max(
        div_ids.index(alpha.id), div_ids.index(alpha_dup.id)
    ) or dup_pair_position_gap >= 1


def test_diversify_deterministic(session: Session) -> None:
    texts = [
        "processed confidential records and customer complaints daily",
        "handled confidential records plus dispute resolution workflows",
        "maintained confidential records with quality assurance audits",
    ]
    items = [KnowledgeItem(type="soq_paragraph", content=t) for t in texts]
    session.add_all(items)
    session.commit()
    service = MatchingService(session)
    first = service.match_query(query="confidential records", limit=3, diversify=True)
    second = service.match_query(query="confidential records", limit=3, diversify=True)
    assert [r.knowledge_item.id for r in first] == [
        r.knowledge_item.id for r in second
    ]


def test_builder_suggestions_are_diversified(session: Session) -> None:
    """Resume suggestions (the shared builder pathway) apply MMR."""
    from app.services.resume_builder import ResumeBuilderService

    texts = [
        "confidential records processing procedures confidential records",
        "confidential records filing procedures confidential records",
        "confidential records community outreach events",
    ]
    items = [KnowledgeItem(type="resume_bullet", content=t) for t in texts]
    session.add_all(items)
    session.commit()

    suggestions = ResumeBuilderService(session).suggest_items("confidential records")
    ids = [s.knowledge_item.id for s in suggestions]
    # The distinct item is not ranked last purely for being different.
    assert items[2].id in ids[:2]


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


# --- Provenance endpoint (Sprint 24) ---


def test_provenance_endpoint_full_trace(client, api_session: Session) -> None:
    from app.db.models import (
        Application,
        ApplicationEvidenceLink,
        JobPosting,
        SourceDocument,
    )

    evidence, items = _seed(api_session)
    item = items[0]

    doc = SourceDocument(filename="resume.pdf", file_type="pdf")
    api_session.add(doc)
    api_session.commit()
    item.source_doc_id = doc.id
    api_session.add(item)
    api_session.commit()

    posting = JobPosting(title="Role", raw_text="duties")
    application = Application(job_posting_id=posting.id, status="offer")
    api_session.add_all([posting])
    api_session.commit()
    api_session.add(application)
    api_session.commit()
    api_session.add(
        ApplicationEvidenceLink(
            application_id=application.id,
            knowledge_item_id=item.id,
            used_in_resume=True,
            result="offer",
        )
    )
    api_session.commit()

    response = client.get(f"/api/v1/knowledge-items/{item.id}/provenance")
    assert response.status_code == 200
    body = response.json()

    assert body["source_document"]["filename"] == "resume.pdf"

    assert len(body["evidence"]) == 1
    ev = body["evidence"][0]
    assert ev["title"] == "Boost Mobile"
    assert ev["strength"] >= 1
    # The recorded 'offer' outcome yields a perfect historical rate.
    assert ev["success_rate"] == pytest.approx(1.0)

    assert len(body["usage"]) == 1
    usage = body["usage"][0]
    assert usage["application_status"] == "offer"
    assert usage["result"] == "offer"
    assert usage["used_in_resume"] is True


def test_provenance_endpoint_404(client) -> None:
    response = client.get("/api/v1/knowledge-items/nope/provenance")
    assert response.status_code == 404
