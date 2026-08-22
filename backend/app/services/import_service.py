"""Import service: orchestrates parse, extract, and persistence."""

import tempfile
from pathlib import Path
from typing import Optional

from sqlmodel import Session

from app.db.models import (
    Evidence,
    KnowledgeItem,
    KnowledgeItemEvidenceLink,
    SourceDocument,
)
from app.models.knowledge import ParagraphType
from app.parsers import get_parser
from app.repositories.document import DocumentRepository
from app.services.extraction_service import ExtractionService

SUPPORTED_TYPES = {"docx", "pdf", "txt"}


class ImportService:
    """Converts uploaded documents into knowledge items and evidence."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.extraction = ExtractionService()
        self.documents = DocumentRepository(session)

    def process_upload(
        self,
        file_path: str,
        filename: Optional[str] = None,
        file_type: Optional[str] = None,
    ) -> SourceDocument:
        """Process a file on disk and persist everything it yields."""
        path = Path(file_path)
        resolved_type = (file_type or path.suffix.lstrip(".")).lower()
        if resolved_type not in SUPPORTED_TYPES:
            raise ValueError(f"Unsupported file type: {resolved_type}")

        source_doc = self.documents.create(
            SourceDocument(
                filename=filename or path.name,
                file_type=resolved_type,
                file_path=str(path),
            )
        )
        try:
            self._process(path, source_doc, resolved_type)
        except Exception:
            self.session.rollback()
            raise
        return source_doc

    def process_text(
        self, text: str, source_doc_id: str, doc_type: str = "txt"
    ) -> list[KnowledgeItem]:
        """In-memory processing for tests: parse text directly."""
        from app.parsers.base import ParsedDocument, Paragraph

        source_doc = self.documents.get(source_doc_id)
        if source_doc is None:
            raise ValueError(f"Unknown source document: {source_doc_id}")

        parsed = ParsedDocument(
            filename=source_doc.filename,
            file_type=doc_type,
            paragraphs=[Paragraph(text=line) for line in text.splitlines()],
        )
        return self._persist(parsed, source_doc)

    def _process(self, path: Path, source_doc: SourceDocument, doc_type: str) -> None:
        parser = get_parser(doc_type)
        parsed = parser.parse(str(path))
        self._persist(parsed, source_doc)

    def _persist(self, parsed, source_doc: SourceDocument) -> list[KnowledgeItem]:
        created: list[KnowledgeItem] = []

        for group in self.extraction.extract_resume_bullets(parsed.paragraphs):
            evidence_title = f"{group.role} - {group.company}"
            evidence = Evidence(
                title=evidence_title,
                type="experience",
                content="; ".join(group.bullets),
                company=group.company,
                role=group.role,
                start_date=None,
                end_date=group.dates,
                source_doc_id=source_doc.id,
            )
            self.session.add(evidence)
            self.session.flush()

            for bullet_text in group.bullets:
                item = KnowledgeItem(
                    type="resume_bullet",
                    content=bullet_text,
                    category=self.extraction.assign_category(
                        bullet_text, ParagraphType.RESUME_BULLET
                    ),
                    metadata_json={
                        "keywords": self.extraction.extract_keywords(bullet_text),
                        "metrics": [
                            m.model_dump()
                            for m in self.extraction.extract_metrics(bullet_text)
                        ],
                    },
                    source_doc_id=source_doc.id,
                )
                self.session.add(item)
                self.session.flush()
                self.session.add(
                    KnowledgeItemEvidenceLink(
                        knowledge_item_id=item.id, evidence_id=evidence.id
                    )
                )
                created.append(item)

        for pair in self.extraction.extract_soq_paragraphs(parsed.paragraphs):
            question_short = pair.question[:80]
            item = KnowledgeItem(
                type="soq_paragraph",
                title=question_short,
                content=pair.answer,
                category=self.extraction.assign_category(
                    pair.answer + " " + pair.question, ParagraphType.SOQ_ANSWER
                ),
                metadata_json={
                    "question": pair.question,
                    "keywords": self.extraction.extract_keywords(pair.answer),
                },
                source_doc_id=source_doc.id,
            )
            self.session.add(item)
            self.session.flush()
            created.append(item)

        self.session.commit()
        return created


def save_upload_to_temp(data: bytes, suffix: str) -> str:
    """Persist uploaded bytes to a temp file and return its path."""
    handle = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    handle.write(data)
    handle.close()
    return handle.name
