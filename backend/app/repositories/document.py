"""Repository for source documents."""

from typing import Optional

from sqlmodel import select

from app.db.models import SourceDocument
from app.repositories.base import BaseRepository


class DocumentRepository(BaseRepository[SourceDocument]):
    """CRUD for source_documents records."""

    model = SourceDocument

    def create(self, document: SourceDocument) -> SourceDocument:
        return self.add(document)

    def get(self, document_id: str) -> Optional[SourceDocument]:
        return self.session.get(SourceDocument, document_id)

    def get_by_filename(self, filename: str) -> list[SourceDocument]:
        stmt = select(SourceDocument).where(
            SourceDocument.filename == filename
        )
        return list(self.session.exec(stmt))
