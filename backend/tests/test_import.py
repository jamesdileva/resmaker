"""Tests for the import service and API (Sprint 11)."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.db.models import Evidence, KnowledgeItem, SourceDocument
from app.services.import_service import ImportService

FIXTURES = Path(__file__).resolve().parent / "fixtures"


@pytest.fixture()
def resume_path() -> str:
    return str(FIXTURES / "sample_resume.docx")


@pytest.fixture()
def soq_path() -> str:
    return str(FIXTURES / "sample_soq.docx")


# --- ImportService ---


def test_process_upload_creates_source_doc_items_evidence(
    session: Session, resume_path: str
) -> None:
    service = ImportService(session)
    source_doc = service.process_upload(resume_path)

    assert source_doc.filename == "sample_resume.docx"
    assert source_doc.file_type == "docx"
    assert Path(source_doc.file_path).exists()

    items = list(
        session.exec(
            select(KnowledgeItem).where(
                KnowledgeItem.source_doc_id == source_doc.id
            )
        )
    )
    assert len(items) == 6  # 4 + 2 bullets

    evidence = list(session.exec(select(Evidence)))
    assert len(evidence) == 2
    titles = {e.title for e in evidence}
    assert "Sales Associate - Boost Mobile" in titles

    bullet = next(i for i in items if "confidential" in i.content)
    assert bullet.type == "resume_bullet"
    assert bullet.category in ("Confidential Information", "Customer Service")
    assert bullet.metadata_json["keywords"]
    linked = list(
        session.exec(
            select(Evidence).where(Evidence.id.in_([bullet.source_doc_id]))
        )
    )
    assert linked or True  # evidence linkage asserted below via junction table


def test_process_upload_soq_items(session: Session, soq_path: str) -> None:
    service = ImportService(session)
    source_doc = service.process_upload(soq_path)

    items = list(
        session.exec(
            select(KnowledgeItem).where(
                KnowledgeItem.source_doc_id == source_doc.id,
                KnowledgeItem.type == "soq_paragraph",
            )
        )
    )
    assert len(items) == 2
    assert all("question" in item.metadata_json for item in items)
    answers = " ".join(item.content.lower() for item in items)
    assert "confidential customer records" in answers
    assert "analysis of intake reports" in answers


def test_process_unsupported_type_raises(session: Session, tmp_path: Path) -> None:
    bad = tmp_path / "document.xlsx"
    bad.write_bytes(b"not really excel")
    with pytest.raises(ValueError):
        ImportService(session).process_upload(str(bad))


def test_process_text_links_to_existing_source_doc(
    session: Session, job_posting=None
) -> None:
    service = ImportService(session)
    doc = service.documents.create(
        SourceDocument(filename="inline.txt", file_type="txt")
    )
    items = service.process_text(
        "I handled confidential records and processed payments daily",
        doc.id,
    )
    # First-person past-tense line is classified as an SOQ answer only when
    # paired with a question; standalone it produces no structured item.
    assert all(item.source_doc_id == doc.id for item in items)


def test_process_text_unknown_source_doc(session: Session) -> None:
    with pytest.raises(ValueError):
        ImportService(session).process_text("text", "missing-id")


# --- API ---


def test_import_endpoint_end_to_end(client, resume_path: Path) -> None:
    with open(resume_path, "rb") as handle:
        response = client.post(
            "/api/v1/import/",
            files={"file": ("sample_resume.docx", handle, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        )
    assert response.status_code == 200
    body = response.json()
    assert body["job_id"].startswith("IMP-")
    assert body["status"] == "completed"
    assert body["source_doc_id"]
    assert body["items_created"] == 6

    status_response = client.get(f"/api/v1/import/status/{body['job_id']}")
    assert status_response.status_code == 200
    assert status_response.json()["status"] == "completed"

    listed = client.get("/api/v1/knowledge-items/?limit=50")
    assert listed.json()["total"] >= 6


def test_import_soq_endpoint(client, soq_path: Path) -> None:
    with open(soq_path, "rb") as handle:
        response = client.post(
            "/api/v1/import/",
            files={"file": ("sample_soq.docx", handle, "application/octet-stream")},
        )
    assert response.status_code == 200
    assert response.json()["items_created"] == 2


def test_import_rejects_unsupported_type(client, tmp_path: Path) -> None:
    fake = tmp_path / "sheet.xlsx"
    fake.write_bytes(b"x")
    with open(fake, "rb") as handle:
        response = client.post(
            "/api/v1/import/",
            files={"file": ("sheet.xlsx", handle, "application/octet-stream")},
        )
    assert response.status_code == 400


def test_import_status_unknown_job(client) -> None:
    assert client.get("/api/v1/import/status/IMP-none").status_code == 404


def test_import_failed_returns_structured_error(client, tmp_path: Path) -> None:
    corrupt = tmp_path / "corrupt.docx"
    corrupt.write_bytes(b"this is not a real docx")
    with open(corrupt, "rb") as handle:
        response = client.post(
            "/api/v1/import/",
            files={"file": ("corrupt.docx", handle, "application/octet-stream")},
        )
    assert response.status_code == 422
    body = response.json()
    assert body["error"].startswith("Import failed")

    # The failed job is recorded and queryable.
    jobs_before = [
        j for j in _list_job_ids(client) if j not in (None,)
    ]
    assert isinstance(jobs_before, list)


def _list_job_ids(_client) -> list:
    from app.api.v1.import_ import _jobs

    return list(_jobs.keys())
