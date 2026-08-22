"""SOQ builder: assembles question responses from knowledge items."""

import uuid
from typing import Optional

from sqlalchemy import select
from sqlmodel import Session

from app.core.exceptions import ValidationAppError
from app.db.models import KnowledgeItem, KnowledgeItemEvidenceLink
from app.models.build import BuiltDocument, Suggestion
from app.models.resume import RenderedSection


def count_words(text: str) -> int:
    """Count whitespace-separated words in text."""
    return len(text.split())


class SOQBuilderService:
    """Answers SOQ questions using evidence from the knowledge base."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def suggest_items(
        self,
        question: str,
        item_types: Optional[list[str]] = None,
        min_score: float = 0.3,
        top_k: int = 10,
    ) -> list[Suggestion]:
        """Find the most relevant evidence for an SOQ question.

        Uses OR-semantics FTS5 ranking for recall; identical behavior to
        resume suggestions until the TF-IDF engine lands (Sprint 25).
        """
        # Delegating keeps suggestion behavior consistent across builders.
        from app.services.resume_builder import ResumeBuilderService

        return ResumeBuilderService(self.session).suggest_items(
            question,
            item_types=item_types,
            min_score=min_score,
            top_k=top_k,
        )

    def answer_question(
        self,
        question: str,
        selected_item_ids: list[str],
        max_words: int = 250,
    ) -> BuiltDocument:
        """Assemble a structured SOQ response within a word budget.

        Items are included in selection order while the budget lasts;
        items that would exceed it are omitted and reported as warnings.
        """
        if not question.strip():
            raise ValidationAppError("Question is required")

        items: list[KnowledgeItem] = []
        seen: set[str] = set()
        for item_id in selected_item_ids:
            if item_id in seen:
                continue
            seen.add(item_id)
            item = self.session.get(KnowledgeItem, item_id)
            if item is not None:
                items.append(item)

        if not items:
            raise ValidationAppError("No valid knowledge items selected")

        included: list[KnowledgeItem] = []
        used_words = 0
        for item in items:
            cost = count_words(item.content)
            if used_words + cost > max_words:
                continue
            included.append(item)
            used_words += cost

        warnings: list[str] = []
        omitted = len(items) - len(included)
        if omitted > 0:
            warnings.append(
                f"{omitted} item(s) omitted to satisfy the "
                f"{max_words}-word limit"
            )
        if not included:
            raise ValidationAppError(
                f"Selected items exceed the {max_words}-word limit"
            )

        item_links = self._evidence_links([item.id for item in included])
        traceability = {
            item.id: item_links[item.id]
            for item in included
            if item.id in item_links
        }

        sections = [
            RenderedSection(
                title="Question",
                section_type="soq_question",
                profile_lines=[question.strip()],
            ),
            RenderedSection(
                title="Response",
                section_type="soq_response",
                lines=[item.content for item in included],
            ),
        ]
        return BuiltDocument(
            document_id=self._new_document_id(),
            template_name="soq_standard",
            sections=sections,
            traceability=traceability,
            warnings=warnings,
        )

    @staticmethod
    def _new_document_id() -> str:
        return str(uuid.uuid4())

    def _evidence_links(self, item_ids: list[str]) -> dict[str, str]:
        stmt = select(KnowledgeItemEvidenceLink).where(
            KnowledgeItemEvidenceLink.knowledge_item_id.in_(item_ids)  # type: ignore[attr-defined]
        )
        links: dict[str, str] = {}
        for link in self.session.execute(stmt).scalars():
            links.setdefault(link.knowledge_item_id, link.evidence_id)
        return links
