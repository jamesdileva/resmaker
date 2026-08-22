"""Duty statement builder: matches duties to evidence and assembles responses."""

import uuid
from typing import Optional

from sqlalchemy import select
from sqlmodel import Session

from app.core.exceptions import NotFoundError, ValidationAppError
from app.db.models import (
    JobPosting,
    KnowledgeItem,
    KnowledgeItemEvidenceLink,
)
from app.models.build import BuiltDocument, Suggestion
from app.models.resume import ExperienceGroup, RenderedSection
from app.services.duty_statement_parser import DutyStatementParser


class DutyStatementBuilderService:
    """Generates duty statement responses backed by existing evidence."""

    MIN_DUTY_MATCH_SCORE = 0.15

    def __init__(self, session: Session) -> None:
        self.session = session

    def suggest_items(
        self,
        duty_text: str,
        item_types: Optional[list[str]] = None,
        top_k: int = 5,
    ) -> list[Suggestion]:
        """Rank evidence for a single duty requirement."""
        from app.services.resume_builder import ResumeBuilderService

        return ResumeBuilderService(self.session).suggest_items(
            duty_text,
            item_types=item_types,
            min_score=self.MIN_DUTY_MATCH_SCORE,
            top_k=top_k,
        )

    def generate_response(
        self,
        job_posting_id: Optional[str] = None,
        selected_item_ids: Optional[list[str]] = None,
        raw_text: Optional[str] = None,
    ) -> BuiltDocument:
        """Assemble one evidence-backed paragraph per parsed duty.

        Accepts either a stored posting id or raw posting text (which is
        persisted as a new JobPosting for provenance). Each duty is
        matched against the selected knowledge items via FTS5 ranking;
        the best match's existing content becomes the response paragraph
        (the builder never writes new experience). Duties prefer unused
        evidence so each draws on distinct support.
        """
        if raw_text:
            posting = JobPosting(
                title="Pasted duty statement",
                raw_text=raw_text,
            )
            self.session.add(posting)
            self.session.commit()
            self.session.refresh(posting)
        elif job_posting_id:
            posting = self.session.get(JobPosting, job_posting_id)
            if posting is None:
                raise NotFoundError(
                    f"Job posting not found: {job_posting_id}"
                )
        else:
            raise ValidationAppError(
                "Provide job_posting_id or raw_text"
            )

        duties = DutyStatementParser().parse(posting.raw_text)
        if not duties:
            raise ValidationAppError(
                "No duty requirements could be parsed from this posting"
            )

        allowed = self._fetch_items(selected_item_ids)
        if not allowed:
            raise ValidationAppError("No valid knowledge items selected")
        allowed_by_id = {item.id: item for item in allowed}

        links_by_item = self._evidence_links([item.id for item in allowed])

        warnings: list[str] = []
        traceability: dict[str, str] = {}
        groups: list[ExperienceGroup] = []
        used_evidence: set[str] = set()

        for index, duty in enumerate(duties):
            matches = self.suggest_items(duty.text, top_k=len(allowed))
            candidates = [
                m for m in matches if m.knowledge_item.id in allowed_by_id
            ]
            # Preference order: linked-but-unused evidence first (distinct
            # support per duty), then anything else.
            linked_unused = [
                m
                for m in candidates
                if links_by_item.get(m.knowledge_item.id)
                and links_by_item[m.knowledge_item.id] not in used_evidence
            ]
            best = (linked_unused or candidates or [None])[0]
            if best is None:
                warnings.append(f"No matching evidence found for duty {index + 1}")
                continue

            item = allowed_by_id[best.knowledge_item.id]
            evidence_id = links_by_item.get(item.id, "_unlinked")
            if evidence_id != "_unlinked":
                used_evidence.add(evidence_id)
                traceability[item.id] = evidence_id

            groups.append(
                ExperienceGroup(
                    evidence_id=evidence_id,
                    title=f"Duty {index + 1}: {_truncate(duty.text)}",
                    dates=None,
                    bullets=[item.content],
                )
            )

        if groups:
            sections = [
                RenderedSection(
                    title="Duty Statement Responses",
                    section_type="duty_response",
                    groups=groups,
                )
            ]
        else:
            sections = []

        return BuiltDocument(
            document_id=str(uuid.uuid4()),
            template_name="duty_standard",
            sections=sections,
            traceability=traceability,
            warnings=warnings,
        )

    def _fetch_items(self, item_ids: list[str]) -> list[KnowledgeItem]:
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
        stmt = select(KnowledgeItemEvidenceLink).where(
            KnowledgeItemEvidenceLink.knowledge_item_id.in_(item_ids)  # type: ignore[attr-defined]
        )
        links: dict[str, str] = {}
        for link in self.session.execute(stmt).scalars():
            links.setdefault(link.knowledge_item_id, link.evidence_id)
        return links


def _truncate(text: str, limit: int = 90) -> str:
    return text if len(text) <= limit else text[: limit - 3].rstrip() + "..."
