"""End-to-end integration tests: import -> search -> build -> validate -> export.

These exercise the public HTTP API exclusively against a real temporary
database, mirroring what a user performs through the UI. Frontend
click-through coverage is handled by the Sentinel integration testers
(Sprint 33).
"""

import io
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from docx import Document as DocxDocument

FIXTURES = Path(__file__).resolve().parent / "fixtures"

USER_PROFILE = {
    "name": "John Doe",
    "location": "Hesperia, CA",
    "email": "john@example.com",
    "phone": "(909) 555-0100",
}


def _upload(client: TestClient, filename: str, data: bytes) -> dict:
    response = client.post(
        "/api/v1/import/",
        files={"file": (filename, data, "application/octet-stream")},
    )
    assert response.status_code == 200, response.text
    return response.json()


def _list_items(client: TestClient, item_type: str | None = None) -> list[dict]:
    params = {"limit": 100}
    if item_type:
        params["type"] = item_type
    response = client.get("/api/v1/knowledge-items/", params=params)
    assert response.status_code == 200
    return response.json()["items"]


def _download(client: TestClient, document_id: str, fmt: str) -> bytes:
    response = client.post(
        "/api/v1/export/download",
        json={"document_id": document_id, "format": fmt},
    )
    assert response.status_code == 200, response.text
    return response.content


def test_resume_pipeline_import_to_export(client: TestClient) -> None:
    """Full resume workflow: import, search, suggest, build, validate, export."""
    # 1. Import the sample resume.
    result = _upload(
        client, "sample_resume.docx", (FIXTURES / "sample_resume.docx").read_bytes()
    )
    assert result["items_created"] >= 5

    bullets = _list_items(client, "resume_bullet")
    assert len(bullets) >= 5

    # 2. Search finds relevant evidence.
    search = client.post(
        "/api/v1/search/", json={"query": "confidential records"}
    )
    assert search.status_code == 200
    assert search.json()["total"] >= 1

    # 3. Suggestions rank the imported evidence.
    suggest = client.post(
        "/api/v1/build/suggest",
        json={"query": "handled confidential customer records", "top_k": 5},
    )
    assert suggest.status_code == 200
    assert len(suggest.json()) >= 1

    # 4. A real user adds skills manually before building.
    skill_ids = []
    for skill_name in ("Customer Service", "Data Analysis", "Records Management"):
        created = client.post(
            "/api/v1/knowledge-items/",
            json={"type": "skill", "content": skill_name},
        )
        assert created.status_code == 201
        skill_ids.append(created.json()["id"])

    # 5. Build a resume from every imported bullet plus the skills.
    build = client.post(
        "/api/v1/build/resume",
        json={
            "item_ids": [b["id"] for b in bullets] + skill_ids,
            "user_profile": USER_PROFILE,
        },
    )
    assert build.status_code == 200, build.text
    document = build.json()
    assert document["document_id"]
    section_types = [s["section_type"] for s in document["sections"]]
    assert "profile" in section_types
    assert "experience" in section_types
    assert "skills" in section_types
    # Traceability covers every imported bullet.
    assert set(document["traceability"].keys()) >= {b["id"] for b in bullets}

    # 6. Validation passes with zero errors.
    validation = client.post(
        "/api/v1/validate/",
        json={"document_id": document["document_id"], "doc_type": "resume"},
    )
    assert validation.status_code == 200
    body = validation.json()
    assert body["valid"] is True, body["errors"]
    assert body["errors"] == []

    # 7. Export to DOCX and TXT; both produce parseable artifacts.
    docx_bytes = _download(client, document["document_id"], "docx")
    parsed = DocxDocument(io.BytesIO(docx_bytes))
    paragraph_texts = [p.text for p in parsed.paragraphs]
    assert any("Summary" in t for t in paragraph_texts)
    assert any("Did valuable" in t or "confidential" in t.lower() for t in paragraph_texts)

    txt_bytes = _download(client, document["document_id"], "txt")
    assert b"SUMMARY" in txt_bytes.upper()


def test_soq_pipeline_import_to_export(client: TestClient) -> None:
    """SOQ workflow: import Q&A pairs, answer a new question, validate, export."""
    # A real user has resumes and SOQs in their knowledge base.
    _upload(
        client,
        "sample_resume.docx",
        (FIXTURES / "sample_resume.docx").read_bytes(),
    )
    _upload(client, "sample_soq.docx", (FIXTURES / "sample_soq.docx").read_bytes())
    soq_items = _list_items(client, "soq_paragraph")
    assert len(soq_items) >= 2

    # Suggest evidence for a new question.
    suggest = client.post(
        "/api/v1/build/suggest",
        json={
            "query": "Describe your experience handling confidential information",
            "item_types": ["soq_paragraph"],
        },
    )
    assert suggest.status_code == 200
    assert len(suggest.json()) >= 1

    question = "Describe your experience handling confidential information"
    # The two fixture answers total <50 words; as a real user would,
    # supplement the selection with a linked resume bullet.
    bullets = _list_items(client, "resume_bullet")
    supplemental = next(
        b for b in bullets if "confidential" in b["content"].lower()
    )
    build = client.post(
        "/api/v1/build/soq",
        json={
            "question": question,
            "selected_item_ids": [i["id"] for i in soq_items]
            + [supplemental["id"]],
            "max_words": 250,
        },
    )
    assert build.status_code == 200, build.text
    document = build.json()
    types = [s["section_type"] for s in document["sections"]]
    assert types == ["soq_question", "soq_response"]
    response_text = " ".join(document["sections"][1]["lines"])
    assert count_words(response_text) <= 250

    # Validation: enough words, question present, zero errors. (The
    # supplemental bullet links to evidence, so no traceability warning
    # fires — that check is all-or-nothing today.)
    validation = client.post(
        "/api/v1/validate/",
        json={"document_id": document["document_id"], "doc_type": "soq"},
    )
    assert validation.status_code == 200
    body = validation.json()
    assert body["valid"] is True, body["errors"]
    assert body["errors"] == []
    assert document["traceability"], "expected linked evidence for the bullet"

    txt_bytes = _download(client, document["document_id"], "txt")
    assert question.encode() in txt_bytes


def test_duty_pipeline_posting_to_response(client: TestClient) -> None:
    """Duty workflow: import evidence once, respond to a pasted posting."""
    _upload(
        client, "sample_resume.docx", (FIXTURES / "sample_resume.docx").read_bytes()
    )
    bullets = _list_items(client, "resume_bullet")

    posting_text = "\n".join(
        (FIXTURES / "sample_duty.txt").read_text(encoding="utf-8").splitlines()
    )
    build = client.post(
        "/api/v1/build/duty-statement",
        json={
            "raw_text": posting_text,
            "selected_item_ids": [b["id"] for b in bullets],
        },
    )
    assert build.status_code == 200, build.text
    document = build.json()

    groups = document["sections"][0]["groups"]
    # One response per parsed duty (the fixture has four).
    assert len(groups) == 4

    # Every cited bullet carries traceability back to evidence.
    assert document["traceability"]

    # Matching engine addresses the same posting.
    match = client.post("/api/v1/match/", json={"query": posting_text, "top_k": 5})
    assert match.status_code == 200
    assert match.json()["matches"]

    txt_bytes = _download(client, document["document_id"], "txt")
    assert b"DUTY STATEMENT RESPONSES" in txt_bytes.upper()


def count_words(text: str) -> int:
    return len(text.split())
