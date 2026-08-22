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
