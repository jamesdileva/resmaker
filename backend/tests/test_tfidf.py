"""Tests for the TF-IDF service (Sprint 25)."""

import pytest
from sqlmodel import Session, select

from app.db.models import KnowledgeItem, TfidfVector
from app.services.tfidf_service import (
    META_KEY,
    TfidfService,
    TfidfVectorizer,
    tokenize,
)


# --- TfidfVectorizer ---


def test_tokenize_lowercase_words() -> None:
    tokens = tokenize("Handled CONFIDENTIAL customer-records daily")
    assert tokens == ["handled", "confidential", "customer-records", "daily"]


def test_transform_produces_weighted_terms() -> None:
    vectorizer = TfidfVectorizer()
    # 'records' appears in 2 of 3 docs (positive idf); 'confidential' in
    # only one (higher idf).
    vectorizer.fit(
        ["confidential records", "public records reports", "unrelated content"]
    )
    vector = vectorizer.transform("confidential records records")
    assert set(vector.keys()) == {"confidential", "records"}
    assert vector["records"] < vector["confidential"]
    assert all(weight > 0 for weight in vector.values())


def test_transform_drops_zero_idf_terms() -> None:
    """A term present in every document carries no signal."""
    vectorizer = TfidfVectorizer()
    vectorizer.fit(["confidential records", "public records"])
    vector = vectorizer.transform("confidential records")
    assert "records" not in vector
    assert "confidential" in vector


def test_transform_drops_out_of_vocabulary_terms() -> None:
    vectorizer = TfidfVectorizer()
    vectorizer.fit(["confidential records"])
    assert vectorizer.transform("quantum physics") == {}


def test_cosine_identical_texts_is_one() -> None:
    vectorizer = TfidfVectorizer()
    vectorizer.fit(["handled confidential records", "other document text"])
    vec = vectorizer.transform("handled confidential records")
    assert TfidfVectorizer.cosine_similarity(vec, vec) == pytest.approx(1.0)


def test_cosine_disjoint_texts_is_zero() -> None:
    assert TfidfVectorizer.cosine_similarity({"alpha": 1.0}, {"beta": 1.0}) == 0.0


def test_cosine_partial_overlap_between_zero_and_one() -> None:
    a = {"confidential": 0.6, "records": 0.4}
    b = {"confidential": 0.5, "reports": 0.5}
    score = TfidfVectorizer.cosine_similarity(a, b)
    assert 0.0 < score < 1.0


def test_cosine_with_precomputed_norms() -> None:
    a = {"x": 3.0, "y": 4.0}
    score = TfidfVectorizer.cosine_similarity(a, a, norm_a=5.0, norm_b=5.0)
    assert score == pytest.approx(1.0)


def test_empty_corpus_fit_is_safe() -> None:
    vectorizer = TfidfVectorizer()
    vectorizer.fit([])
    assert vectorizer.transform("anything") == {}


# --- TfidfService (DB-backed) ---


@pytest.fixture()
def items(session: Session) -> list[KnowledgeItem]:
    created = [
        KnowledgeItem(type="resume_bullet", content="Handled confidential records daily"),
        KnowledgeItem(type="resume_bullet", content="Resolved customer complaints quickly"),
        KnowledgeItem(
            type="soq_paragraph",
            content="Performed data analysis on weekly reports using Excel dashboards",
        ),
    ]
    session.add_all(created)
    session.commit()
    for item in created:
        session.refresh(item)
    return created


def test_build_index_persists_vectors_and_meta(session: Session, items) -> None:
    service = TfidfService(session)
    count = service.build_index()

    assert count == 3
    rows = list(session.exec(select(TfidfVector)).all())
    keys = {row.key for row in rows}
    assert keys == {item.id for item in items} | {META_KEY}

    meta = session.get(TfidfVector, META_KEY)
    assert meta is not None and meta.vector_json


def test_similarity_ranks_matching_item_highest(session: Session, items) -> None:
    service = TfidfService(session)
    service.build_index()

    query_vec = service.vectorize_query("confidential records handling")
    scores = {
        item.id: service.similarity(item.id, query_vec) for item in items
    }
    best_id = max(scores, key=scores.get)
    assert best_id == items[0].id
    assert scores[items[0].id] > scores[items[2].id]


def test_similarity_unknown_item_is_zero(session: Session, items) -> None:
    service = TfidfService(session)
    service.build_index()
    query_vec = service.vectorize_query("confidential")
    assert service.similarity("missing-id", query_vec) == 0.0


def test_vectorize_query_without_index_returns_empty(session: Session) -> None:
    service = TfidfService(session)
    assert service.vectorize_query("anything at all") == {}
    assert service.similarity("whatever", {"x": 1.0}) == 0.0


def test_rebuild_detects_added_items(session: Session, items) -> None:
    service = TfidfService(session)
    service.build_index()
    assert service.rebuild_if_needed() is False

    new_item = KnowledgeItem(type="skill", content="brand new skill entry")
    session.add(new_item)
    session.commit()
    assert service.rebuild_if_needed() is True

    keys = {row.key for row in session.exec(select(TfidfVector)).all()}
    assert new_item.id in keys


def test_rebuild_detects_deleted_items(session: Session, items) -> None:
    service = TfidfService(session)
    service.build_index()

    session.delete(items[0])
    session.commit()
    assert service.rebuild_if_needed() is True

    keys = {row.key for row in session.exec(select(TfidfVector)).all()}
    assert items[0].id not in keys


def test_cached_query_does_not_rebuild(session: Session, items) -> None:
    """A second rebuild check with no changes skips the work."""
    service = TfidfService(session)
    service.build_index()
    assert service.rebuild_if_needed() is False
    assert service.rebuild_if_needed() is False
