"""Matching engine service: search, ranking, and star ratings.

FTS5-backed MVP implementation; TF-IDF vectorization and historical
weighting upgrade this in Sprints 25-26 without changing the interface.
"""

from typing import Optional

from pydantic import BaseModel
from sqlalchemy import select
from sqlmodel import Session

from app.db.models import (
    Application,
    ApplicationEvidenceLink,
    Evidence,
    KnowledgeItem,
    KnowledgeItemEvidenceLink,
)
from app.repositories.knowledge_item import KnowledgeItemRepository
from app.services.historical_weighting import HistoricalWeightingService
from app.services.tfidf_service import TfidfService

# Star rating thresholds per Implementation Guide section 13.3.
STAR_THRESHOLDS: list[tuple[float, int]] = [
    (0.90, 5),
    (0.80, 4),
    (0.70, 3),
    (0.60, 2),
    (0.50, 1),
]


def stars_for_score(score: float) -> int:
    """Map a 0.0-1.0 match score to the documented 1-5 star scale."""
    for threshold, stars in STAR_THRESHOLDS:
        if score >= threshold:
            return stars
    return 0


class SearchResult(BaseModel):
    """A ranked search hit with provenance enrichment."""

    knowledge_item: KnowledgeItem
    score: float
    star_rating: int
    evidence_ids: list[str] = []


class MatchingService:
    """Searches and ranks knowledge items for the explorer and builders."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def match_query(
        self,
        query: str = "",
        item_types: Optional[list[str]] = None,
        categories: Optional[list[str]] = None,
        min_star_rating: int = 0,
        min_score: float = 0.0,
        sort_by: str = "relevance",
        limit: int = 50,
        match_all: bool = True,
    ) -> list[SearchResult]:
        """Full explorer search with filters, stars, and provenance.

        Ranking pipeline: TF-IDF cosine similarity (rebuilding the cached
        index when stale), boosted by historical success weighting
        (final = cosine * (1 + weight)); falls back to FTS5 ranking when
        the corpus is too small for a meaningful IDF. An empty query
        returns recent items (browse mode).
        """
        repo = KnowledgeItemRepository(self.session)
        candidates = self._base_candidates(query, repo, match_all, min_score)

        weighting = HistoricalWeightingService(self.session)
        weights = weighting.calculate_weights_bulk(
            [item.id for item, _ in candidates]
        )

        results: list[SearchResult] = []
        for item, score in candidates:
            if item_types and item.type not in item_types:
                continue
            if categories and item.category not in categories:
                continue
            weighted = min(score * (1 + weights.get(item.id, 0.0)), 1.0)
            stars = stars_for_score(weighted)
            if stars < min_star_rating:
                continue
            results.append(
                SearchResult(
                    knowledge_item=item,
                    score=weighted,
                    star_rating=stars,
                    evidence_ids=self._evidence_ids(item.id),
                )
            )

        if sort_by == "date":
            results.sort(key=lambda r: r.knowledge_item.created_at, reverse=True)
        else:
            results.sort(key=lambda r: r.score, reverse=True)

        return results[:limit]

    def _base_candidates(
        self,
        query: str,
        repo: KnowledgeItemRepository,
        match_all: bool,
        min_score: float,
    ) -> list[tuple[KnowledgeItem, float]]:
        """Produce (item, base_score) pairs via TF-IDF with FTS5 fallback.

        TF-IDF is preferred at any corpus size: zero-IDF terms (e.g.
        stopwords) drop out of cosine scoring automatically, whereas
        normalized BM25 over OR queries rewards documents matching
        fewer, more common terms. FTS5 remains the fallback when no
        index vocabulary exists yet (e.g. an empty database).
        """
        if not query.strip():
            items = repo.get_multi(skip=0, limit=500)
            return [(item, 0.0) for item in items]

        tfidf = TfidfService(self.session)
        tfidf.rebuild_if_needed()
        query_vec = tfidf.vectorize_query(query)

        if query_vec:
            # Cosine similarity is honestly calibrated (~0 means no
            # relation), so only a small epsilon floor applies here;
            # the caller's min_score targets FTS5-score calibration.
            items = repo.get_multi(skip=0, limit=10000)
            scored = [
                (item, tfidf.similarity(item.id, query_vec))
                for item in items
            ]
            return [
                (item, score)
                for item, score in scored
                if score > 0.01
            ]

        matches = repo.search(query, min_score=min_score, match_all=match_all)
        return [(m.knowledge_item, m.score) for m in matches]

    def _evidence_ids(self, item_id: str) -> list[str]:
        stmt = select(KnowledgeItemEvidenceLink.evidence_id).where(
            KnowledgeItemEvidenceLink.knowledge_item_id == item_id
        )
        return [
            row[0]
            for row in self.session.execute(stmt).all()
        ]

    def get_provenance(self, item_id: str):
        """Assemble full trace info for one knowledge item."""
        from app.db.models import (
            Application,
            ApplicationEvidenceLink,
            SourceDocument,
        )
        from app.repositories.evidence import EvidenceRepository

        item = self.session.get(KnowledgeItem, item_id)
        if item is None:
            return None

        # Source document.
        source_doc = None
        if item.source_doc_id:
            doc = self.session.get(SourceDocument, item.source_doc_id)
            if doc is not None:
                source_doc = {
                    "id": doc.id,
                    "filename": doc.filename,
                    "file_type": doc.file_type,
                    "imported_at": doc.imported_at.isoformat(),
                }

        # Linked evidence with strength + historical success rate.
        evidence_repo = EvidenceRepository(self.session)
        evidence_info = []
        link_rows = self.session.execute(
            select(KnowledgeItemEvidenceLink).where(
                KnowledgeItemEvidenceLink.knowledge_item_id == item_id
            )
        ).scalars().all()
        for link in link_rows:
            evidence = self.session.get(Evidence, link.evidence_id)
            if evidence is None:
                continue
            evidence_info.append(
                {
                    "id": evidence.id,
                    "title": evidence.title,
                    "type": evidence.type,
                    "company": evidence.company,
                    "role": evidence.role,
                    "strength": link.strength,
                    "success_rate": evidence_repo.get_success_rate(evidence.id),
                }
            )

        # Applications that used this item and their outcomes.
        usage: list[dict] = []
        rows = self.session.execute(
            select(ApplicationEvidenceLink, Application)
            .join(
                Application,
                Application.id == ApplicationEvidenceLink.application_id,
            )
            .where(ApplicationEvidenceLink.knowledge_item_id == item_id)
        ).all()
        for ae_link, application in rows:
            usage.append(
                {
                    "application_id": application.id,
                    "applied_at": application.applied_at.isoformat(),
                    "application_status": application.status,
                    "result": ae_link.result,
                    "used_in_resume": ae_link.used_in_resume,
                    "used_in_soq": ae_link.used_in_soq,
                    "used_in_duty": ae_link.used_in_duty,
                }
            )

        return {
            "knowledge_item": item,
            "source_document": source_doc,
            "evidence": evidence_info,
            "usage": usage,
        }
