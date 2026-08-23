"""SOQ builder: assembles question responses from knowledge items."""

import re
import uuid
from typing import Optional

from sqlalchemy import select
from sqlmodel import Session

from app.core.exceptions import ValidationAppError
from app.db.models import KnowledgeItem, KnowledgeItemEvidenceLink
from app.models.build import BuiltDocument, Suggestion
from app.models.resume import RenderedSection
from app.services.soq_analyzer import SOQAnalyzer, load_soq_categories


def count_words(text: str) -> int:
    """Count whitespace-separated words in text."""
    return len(text.split())


# Smallest share any selected item may be trimmed to (words). Keeps short
# contributions from being erased entirely when the budget is tight.
MIN_SHARE_WORDS = 15

_SENTENCE_END_RE = re.compile(r"[.!?][\"')\]]?\s")


def _trim_to_word_share(text: str, word_budget: int) -> str:
    """Trim *text* to at most *word_budget* words, preferring a sentence end.

    Falls back to a clean word boundary when the text has no usable
    sentence punctuation inside the budget (e.g. bullet fragments). Never
    breaks mid-word and never appends ellipses or other fabrications.
    """
    words = text.split()
    if word_budget >= len(words):
        return text
    cut = " ".join(words[:word_budget])
    best_end = 0
    for match in _SENTENCE_END_RE.finditer(cut):
        best_end = match.end()
    # A sentence boundary is only used when it leaves a meaningful chunk
    # of the allocated share intact.
    if best_end >= min(word_budget // 2, word_budget - 1):
        return cut[:best_end].rstrip()
    return cut


def _allocate_shares(word_costs: list[int], max_words: int) -> list[int]:
    """Split *max_words* across items proportionally to their length.

    Largest-remainder rounding keeps determinism; a floor protects tiny
    items from being squeezed to nothing (taken from the largest shares,
    single pass — good enough for realistic selections).
    """
    total = sum(word_costs)
    raw = [max_words * cost / total for cost in word_costs]
    shares = [int(share) for share in raw]
    remainder = max_words - sum(shares)
    order = sorted(range(len(raw)), key=lambda i: raw[i] - shares[i], reverse=True)
    for i in order[:remainder]:
        shares[i] += 1

    # Floor pass: lift sub-minimum shares and take the difference from the
    # largest ones while they stay above the floor themselves.
    for i, cost in enumerate(word_costs):
        if shares[i] < MIN_SHARE_WORDS:
            needed = min(MIN_SHARE_WORDS, cost) - shares[i]
            donors = sorted(
                (j for j in range(len(shares)) if j != i),
                key=lambda j: shares[j],
                reverse=True,
            )
            for j in donors:
                if needed <= 0:
                    break
                room = shares[j] - MIN_SHARE_WORDS
                if room > 0:
                    move = min(room, needed)
                    shares[j] -= move
                    shares[i] += move
                    needed -= move
            shares[i] += needed  # may briefly exceed the budget...
    # Infeasible floors (budget < N * MIN_SHARE): fall back to a
    # deterministic equal split rather than blowing the limit.
    if sum(shares) > max_words:
        base, extra = divmod(max_words, len(shares))
        shares = [
            base + (1 if i < extra else 0) for i in range(len(shares))
        ]
    # A share never exceeds the item's own length (no padding).
    return [min(share, cost) for share, cost in zip(shares, word_costs)]


class SOQBuilderService:
    """Answers SOQ questions using evidence from the knowledge base."""

    def __init__(self, session: Session, analyzer: Optional[SOQAnalyzer] = None) -> None:
        self.session = session
        self.analyzer = analyzer or SOQAnalyzer()

    def suggest_items(
        self,
        question: str,
        item_types: Optional[list[str]] = None,
        min_score: float = 0.3,
        top_k: int = 10,
    ) -> list[Suggestion]:
        """Find the most relevant evidence for an SOQ question.

        Short questions are broadened with unmatched category keywords
        from the analyzer to improve recall. Ranking is delegated to the
        resume builder so all builders share one pathway.

        (Live-fix 2026-08-23: a duplicate later definition of this method
        silently shadowed it, so category expansion never ran.)
        """
        expanded = self._expand_query(question)
        # Delegating keeps suggestion behavior consistent across builders.
        from app.services.resume_builder import ResumeBuilderService

        return ResumeBuilderService(self.session).suggest_items(
            expanded,
            item_types=item_types,
            min_score=min_score,
            top_k=top_k,
        )

    def _expand_query(self, question: str) -> str:
        """Broaden a question with its category's keyword patterns.

        Adds up to three patterns from the detected category that do not
        already appear in the question, improving OR-mode recall.
        """
        category = self.analyzer.classify_question(question)
        if category == self.analyzer.DEFAULT_CATEGORY:
            return question
        lowered = question.lower()
        additions = [
            pattern
            for pattern in load_soq_categories().get(category, [])
            if pattern.lower() not in lowered
        ][:3]
        if not additions:
            return question
        return f"{question} {' '.join(additions)}"

    def answer_question(
        self,
        question: str,
        selected_item_ids: list[str],
        max_words: int = 250,
    ) -> BuiltDocument:
        """Assemble a structured SOQ response within a word budget.

        Every selected item is represented. When the combined content
        exceeds the budget, each item is trimmed proportionally to its
        length (sentence boundaries preferred) instead of dropping whole
        blocks — the live-verified behavior of dropping later items made
        multi-item selections collapse to a single block.
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

        word_costs = [count_words(item.content) for item in items]
        total_words = sum(word_costs)

        warnings: list[str] = []
        if total_words > max_words:
            shares = _allocate_shares(word_costs, max_words)
            contents = [
                _trim_to_word_share(item.content, share)
                for item, share in zip(items, shares)
            ]
            warnings.append(
                f"{len(items)} item(s) trimmed proportionally to fit the "
                f"{max_words}-word limit"
            )
        else:
            contents = [item.content for item in items]

        included = items  # every valid selection is represented

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
                lines=contents,
            ),
        ]
        document = BuiltDocument(
            document_id=self._new_document_id(),
            template_name="soq_standard",
            sections=sections,
            traceability=traceability,
            warnings=warnings,
            metadata={"category": self.analyzer.classify_question(question)},
        )
        from app.services.export_service import registry

        registry.register(document)
        return document

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
