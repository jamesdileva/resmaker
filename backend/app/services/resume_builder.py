"""Resume builder: assembles resumes from selected knowledge items."""

import uuid
from typing import Optional

from sqlalchemy import select
from sqlmodel import Session

from app.core.exceptions import NotFoundError, ValidationAppError
from app.db.models import (
    Evidence,
    JobPosting,
    KnowledgeItem,
    KnowledgeItemEvidenceLink,
)
from app.models.build import BuiltDocument, Suggestion
from app.repositories.knowledge_item import KnowledgeItemRepository
from app.services.template_engine import TemplateEngine


class ResumeBuilderService:
    """Fetches items, groups them into sections, and builds documents."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def build_resume(
        self,
        item_ids: list[str],
        user_profile: Optional[dict] = None,
        template: str = "standard",
    ) -> BuiltDocument:
        """Assemble a resume from the selected knowledge items."""
        engine = TemplateEngine()
        template_model = engine.load_template(template)

        items = self._fetch_items(item_ids)
        if not items:
            raise ValidationAppError("No valid knowledge items selected")

        item_links = self._evidence_links([item.id for item in items])
        evidence_records = self._fetch_evidence(set(item_links.values()))

        rendered = engine.render(
            template_model,
            items,
            evidence_records,
            user_profile or {},
            item_links=item_links,
        )
        document = BuiltDocument(
            document_id=str(uuid.uuid4()),
            template_name=template_model.name,
            sections=rendered.sections,
            traceability=rendered.traceability,
            warnings=rendered.warnings,
        )
        from app.services.export_service import registry

        registry.register(document)
        return document

    def suggest_items(
        self,
        query: str,
        item_types: Optional[list[str]] = None,
        min_score: float = 0.3,
        top_k: int = 10,
    ) -> list[Suggestion]:
        """Rank knowledge items against a query.

        Routes through MatchingService so builders inherit TF-IDF
        scoring and historical success weighting (Sprint 26).
        """
        from app.services.matching_service import MatchingService

        matching = MatchingService(self.session)
        results = matching.match_query(
            query=query,
            item_types=item_types,
            min_score=min_score,
            limit=top_k,
            match_all=False,
        )
        return [
            Suggestion(
                knowledge_item=result.knowledge_item,
                score=result.score,
                evidence_id=(
                    result.evidence_ids[0] if result.evidence_ids else None
                ),
            )
            for result in results
        ]

    def auto_build_resume(
        self,
        job_posting_id: str,
        template: str = "standard",
        max_items: int = 15,
    ) -> BuiltDocument:
        """Auto-select the best-matching items for a job posting and build."""
        posting = self.session.get(JobPosting, job_posting_id)
        if posting is None:
            raise NotFoundError(f"Job posting not found: {job_posting_id}")

        query_text = " ".join(part for part in (posting.title, posting.raw_text) if part)
        suggestions = self.suggest_items(query_text, top_k=max_items)
        item_ids = [suggestion.knowledge_item.id for suggestion in suggestions]
        return self.build_resume(item_ids, {}, template)

    def _fetch_items(self, item_ids: list[str]) -> list[KnowledgeItem]:
        """Fetch items by id preserving request order without duplicates."""
        items: list[KnowledgeItem] = []
        seen: set[str] = set()
        for item_id in item_ids:
            if item_id in seen:
                continue
            seen.add(item_id)
            item = self.session.get(KnowledgeItem, item_id)
            if item is not None:
                items.append(item)
        return items

    def _evidence_links(self, item_ids: list[str]) -> dict[str, str]:
        """Map each item id to its first linked evidence id."""
        stmt = select(KnowledgeItemEvidenceLink).where(
            KnowledgeItemEvidenceLink.knowledge_item_id.in_(item_ids)  # type: ignore[attr-defined]
        )
        links: dict[str, str] = {}
        for link in self.session.execute(stmt).scalars():
            links.setdefault(link.knowledge_item_id, link.evidence_id)
        return links

    def _fetch_evidence(self, evidence_ids: set[str]) -> list[Evidence]:
        if not evidence_ids:
            return []
        stmt = select(Evidence).where(Evidence.id.in_(evidence_ids))  # type: ignore[attr-defined]
        return list(self.session.execute(stmt).scalars())

    def _primary_evidence(self, item_id: str) -> Optional[str]:
        stmt = (
            select(KnowledgeItemEvidenceLink.evidence_id)
            .where(KnowledgeItemEvidenceLink.knowledge_item_id == item_id)
            .limit(1)
        )
        row = self.session.execute(stmt).first()
        return row[0] if row else None
