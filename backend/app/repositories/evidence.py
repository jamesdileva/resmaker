"""Evidence repository with knowledge-item linking and success rates."""

from typing import Optional

from pydantic import BaseModel
from sqlalchemy import text
from sqlmodel import select

from app.db.models import (
    ApplicationEvidenceLink,
    Evidence,
    KnowledgeItem,
    KnowledgeItemEvidenceLink,
)
from app.repositories.base import BaseRepository


class EvidenceWithItems(BaseModel):
    """Evidence record paired with its linked knowledge items."""

    evidence: Evidence
    items: list[KnowledgeItem] = []


class EvidenceRepository(BaseRepository[Evidence]):
    """CRUD for evidence records plus item links and success history."""

    model = Evidence

    def create(self, evidence: Evidence) -> Evidence:
        return self.add(evidence)

    def get(self, evidence_id: str) -> Optional[EvidenceWithItems]:
        """Fetch evidence together with its linked knowledge items."""
        evidence = self.session.get(Evidence, evidence_id)
        if evidence is None:
            return None
        stmt = (
            select(KnowledgeItem)
            .join(
                KnowledgeItemEvidenceLink,
                KnowledgeItemEvidenceLink.knowledge_item_id == KnowledgeItem.id,
            )
            .where(KnowledgeItemEvidenceLink.evidence_id == evidence_id)
        )
        linked = list(self.session.exec(stmt))
        return EvidenceWithItems(evidence=evidence, items=linked)

    def get_multi(self, skip: int = 0, limit: int = 50) -> list[Evidence]:
        stmt = select(Evidence).offset(skip).limit(limit).order_by(Evidence.title)
        return list(self.session.exec(stmt))

    def link_to_item(self, evidence_id: str, item_id: str, strength: int = 3) -> None:
        """Create a knowledge_item_evidence link if it does not already exist."""
        existing = self.session.exec(
            select(KnowledgeItemEvidenceLink)
            .where(KnowledgeItemEvidenceLink.evidence_id == evidence_id)
            .where(KnowledgeItemEvidenceLink.knowledge_item_id == item_id)
        ).first()
        if existing is not None:
            existing.strength = strength
            self.session.add(existing)
        else:
            self.session.add(
                KnowledgeItemEvidenceLink(
                    evidence_id=evidence_id,
                    knowledge_item_id=item_id,
                    strength=strength,
                )
            )
        self.session.commit()

    def get_success_rate(self, evidence_id: str) -> float:
        """Fraction of recorded application results that reached interview/offer.

        Considers every application_evidence row whose knowledge item is
        linked to this evidence. Rows without a result are ignored. An
        offer counts as both an interview and an offer.
        """
        sql = text(
            "SELECT ae.result FROM application_evidence ae "
            "JOIN knowledge_item_evidence kie "
            "ON kie.knowledge_item_id = ae.knowledge_item_id "
            "WHERE kie.evidence_id = :evidence_id AND ae.result IS NOT NULL"
        )
        rows = self.session.execute(sql, {"evidence_id": evidence_id}).all()
        if not rows:
            return 0.0
        results = [row[0] for row in rows]
        total = len(results)
        interviews = sum(1 for r in results if r in ("interview", "offer"))
        offers = sum(1 for r in results if r == "offer")
        return (interviews + offers) / (2 * total)
