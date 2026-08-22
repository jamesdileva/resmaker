"""Matching engine service: search, ranking, and star ratings.

FTS5-backed MVP implementation; TF-IDF vectorization and historical
weighting upgrade this in Sprints 25-26 without changing the interface.
"""

from typing import Optional

from pydantic import BaseModel
from sqlalchemy import select
from sqlmodel import Session

from app.db.models import KnowledgeItem, KnowledgeItemEvidenceLink
from app.repositories.knowledge_item import KnowledgeItemRepository

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

        An empty query returns recent items (browse mode, zero scores).
        ``match_all=False`` switches FTS5 to OR semantics for broad
        recall against long texts like job postings.
        """
        repo = KnowledgeItemRepository(self.session)
        if query.strip():
            matches = repo.search(query, min_score=min_score, match_all=match_all)
            candidates = [(m.knowledge_item, m.score) for m in matches]
        else:
            items = repo.get_multi(skip=0, limit=500)
            candidates = [(item, 0.0) for item in items]

        results: list[SearchResult] = []
        for item, score in candidates:
            if item_types and item.type not in item_types:
                continue
            if categories and item.category not in categories:
                continue
            stars = stars_for_score(score)
            if stars < min_star_rating:
                continue
            results.append(
                SearchResult(
                    knowledge_item=item,
                    score=score,
                    star_rating=stars,
                    evidence_ids=self._evidence_ids(item.id),
                )
            )

        if sort_by == "date":
            results.sort(key=lambda r: r.knowledge_item.created_at, reverse=True)
        else:
            results.sort(key=lambda r: r.score, reverse=True)

        return results[:limit]

    def _evidence_ids(self, item_id: str) -> list[str]:
        stmt = select(KnowledgeItemEvidenceLink.evidence_id).where(
            KnowledgeItemEvidenceLink.knowledge_item_id == item_id
        )
        return [
            row[0]
            for row in self.session.execute(stmt).all()
        ]
