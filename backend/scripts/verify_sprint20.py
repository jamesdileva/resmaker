"""Live Sprint 20 verification: Lottery posting -> duty statement response."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.db.connection import get_engine, init_db
from app.db.models import JobPosting
from app.parsers.pdf_parser import PdfParser
from app.services.duty_statement_builder import DutyStatementBuilderService
from sqlmodel import Session

POSTING_PATH = (
    r"C:\Users\j\Desktop\Resumes"
    r"\duty statement for district sales representative california state lottery.pdf"
)

engine = get_engine()
init_db(engine)

with Session(engine) as session:
    parsed = PdfParser().parse(POSTING_PATH)
    raw_text = "\n".join(p.text for p in parsed.paragraphs)

    posting = JobPosting(
        title="District Sales Representative - CA State Lottery",
        agency="California State Lottery",
        raw_text=raw_text,
    )
    session.add(posting)
    session.commit()
    session.refresh(posting)
    print(f"posting id: {posting.id[:8]}...")

    # Use every knowledge item currently in the base; seed with the
    # real resume when the pool is thin.
    from sqlalchemy import select

    from app.db.models import KnowledgeItem

    items = list(session.execute(select(KnowledgeItem)).scalars())
    print(f"knowledge pool: {len(items)} items")
    if len(items) < 3:
        from app.services.import_service import ImportService

        source_doc = ImportService(session).process_upload(
            r"C:\Users\j\Desktop\Resumes\James Dileva Resume Office Tech.pdf"
        )
        session.refresh(source_doc)
        items = list(session.execute(select(KnowledgeItem)).scalars())
        print(f"seeded from resume -> {len(items)} items")

    service = DutyStatementBuilderService(session)
    document = service.generate_response(
        posting.id, [item.id for item in items]
    )

    print(f"document {document.document_id[:8]}... warnings={len(document.warnings)}")
    section = document.sections[0]
    print(f"{len(section.groups)} duty groups:")
    for group in section.groups:
        preview = group.bullets[0][:70] if group.bullets else "(no evidence)"
        print(f"  {group.title[:70]}")
        print(f"      -> [{group.evidence_id[:8]}...] {preview}")
    if document.warnings:
        print("warnings:")
        for warning in document.warnings:
            print(f"  - {warning}")
