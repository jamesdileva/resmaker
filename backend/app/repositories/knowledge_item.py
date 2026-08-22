"""Knowledge item repository with FTS5-backed search."""

from typing import Optional

from pydantic import BaseModel
from sqlalchemy import text
from sqlmodel import select

from app.db.models import Evidence, KnowledgeItem, KnowledgeItemEvidenceLink
from app.repositories.base import BaseRepository


class MatchResult(BaseModel):
    """A ranked search hit."""

    knowledge_item: KnowledgeItem
    score: float


class KnowledgeItemRepository(BaseRepository[KnowledgeItem]):
    """CRUD and FTS5 search for knowledge items."""

    model = KnowledgeItem

    def create(self, item: KnowledgeItem) -> KnowledgeItem:
        return self.add(item)

    def get(self, item_id: str) -> Optional[KnowledgeItem]:
        return self.session.get(KnowledgeItem, item_id)

    def get_multi(
        self,
        skip: int = 0,
        limit: int = 50,
        type: Optional[str] = None,
        category: Optional[str] = None,
    ) -> list[KnowledgeItem]:
        stmt = select(KnowledgeItem)
        if type is not None:
            stmt = stmt.where(KnowledgeItem.type == type)
        if category is not None:
            stmt = stmt.where(KnowledgeItem.category == category)
        stmt = stmt.offset(skip).limit(limit).order_by(KnowledgeItem.created_at)
        return list(self.session.exec(stmt))

    def search(self, query: str, min_score: float = 0.0) -> list[MatchResult]:
        """Full-text search ranked by normalized BM25 relevance.

        Scores are mapped from FTS5 rank (negative, lower is better)
        to a 0.0-1.0 scale via 1 / (1 - rank).
        """
        escaped = query.replace('"', '""')
        sql = text(
            "SELECT ki.*, fts.rank AS fts_rank "
            "FROM knowledge_items_fts fts "
            "JOIN knowledge_items ki ON ki.id = fts.item_id "
            "WHERE knowledge_items_fts MATCH :q "
            "ORDER BY fts.rank"
        )
        rows = self.session.execute(sql, {"q": f'"{escaped}"'}).mappings().all()
        results = []
        for row in rows:
            score = 1.0 / (1.0 + abs(row["fts_rank"]))
            if score < min_score:
                continue
            item = self.get(row["id"])
            if item is not None:
                results.append(MatchResult(knowledge_item=item, score=score))
        return results

    def update(self, item_id: str, data: dict) -> Optional[KnowledgeItem]:
        item = self.get(item_id)
        if item is None:
            return None
        for field, value in data.items():
            if hasattr(item, field):
                setattr(item, field, value)
        self.session.add(item)
        self.session.commit()
        self.session.refresh(item)
        return item

    def delete(self, item_id: str) -> bool:
        item = self.get(item_id)
        if item is None:
            return False
        self.session.delete(item)
        self.session.commit()
        return True

    def bulk_create(self, items: list[KnowledgeItem]) -> list[KnowledgeItem]:
        for item in items:
            self.session.add(item)
        self.session.commit()
        for item in items:
            self.session.refresh(item)
        return items

    def get_with_evidence(
        self, item_id: str
    ) -> tuple[Optional[KnowledgeItem], list[Evidence]]:
        item = self.get(item_id)
        if item is None:
            return None, []
        stmt = (
            select(Evidence)
            .join(KnowledgeItemEvidenceLink, KnowledgeItemEvidenceLink.evidence_id == Evidence.id)
            .where(KnowledgeItemEvidenceLink.knowledge_item_id == item_id)
        )
        return item, list(self.session.exec(stmt))
