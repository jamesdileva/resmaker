# Career OS — Sprint Plan

> **Version:** 1.1
> **Status:** Draft — Pre-MVP
> **Audience:** Developers, AI coding agents
> **Related:** See `docs/01_Master_Architecture.md` and `docs/02_Implementation_Guide.md`

This document is the **day-to-day build guide** for Career OS. It breaks the MVP into 30 small, verifiable sprints. Each sprint is self-contained and designed to be completed and verified before moving to the next.

---

## Sprint Planning Methodology

Each sprint follows this template:

| Field | Description |
|-------|-------------|
| **Objective** | What this sprint accomplishes in one sentence |
| **Inputs** | Data, files, or context needed to start |
| **Outputs** | Deliverables produced by this sprint |
| **Files Created** | New files to create |
| **Files Modified** | Existing files to change |
| **Database Changes** | Any schema changes |
| **Backend Changes** | Service, repository, or API updates |
| **Frontend Changes** | UI component, page, or hook updates |
| **API Endpoints** | New or modified endpoints |
| **Acceptance Criteria** | Specific, testable conditions |
| **Manual Testing** | Step-by-step verification checklist |
| **Definition of Done** | What "done" means for this sprint |
| **Estimated Time** | Rough developer time (AI agent) |
| **Dependencies** | Which previous sprints must be done first |

---

## Sprint Phases Overview

| Phase | Sprints | Description |
|-------|---------|-------------|
| Phase 0 | 1-5 | Backend foundation: scaffolding, DB, models, repos, API, tests |
| Phase 1 | 6-7 | Frontend foundation: scaffolding, contexts, API client |
| Phase 2 | 8-12 | Import pipeline: DOCX/PDF/TXT parsers, extraction, import UI |
| Phase 3 | 13-15 | Resume builder: template engine, service, UI |
| Phase 4 | 16-18 | SOQ builder: service, question analyzer, UI |
| Phase 5 | 19-21 | Duty statement generator: parser, service, UI |
| Phase 6 | 22-24 | Evidence explorer: search API, UI, provenance panel |
| Phase 7 | 25-26 | Matching engine: TF-IDF, historical weighting |
| Phase 8 | 27-28 | Export pipeline: DOCX/TXT exporters, UI |
| Phase 9 | 29 | Validation engine |
| Phase 10 | 30 | LLM integration (optional) |
| Phase 11 | 31-33 | E2E tests + MVP release + Sentinel integration testers |

---
## Phase 0: Foundation (Sprints 1-5)

### Sprint 1 — Project Scaffolding

**Objective:** Set up the Python backend project structure, dependencies, and configuration.

**Files Created:**
- `backend/pyproject.toml`
- `backend/app/__init__.py`
- `backend/app/main.py`
- `backend/requirements.txt`
- `.python-version`

**Files Modified:**
- `AGENTS.md` (create project rules)

**Database Changes:** None.

**Backend Changes:**
- Create FastAPI app with health check endpoint `/`
- Configure CORS middleware (localhost:5173 for frontend dev)
- Basic exception handler

**Frontend Changes:** None.

**API Endpoints:**
- `GET /` — Health check (returns `{"status": "ok"}`)
- `GET /health` — Health check (returns `{"status": "healthy"}`)

**Acceptance Criteria:**
- `pyproject.toml` includes FastAPI, SQLModel, Uvicorn, pytest, python-docx, pymupdf
- `python -m pip install -e backend/` succeeds
- `uvicorn app.main:app --reload` starts the server
- `GET /` returns `{"status": "ok"}`
- `GET /health` returns `{"status": "healthy"}`

**Manual Testing:**
1. Run `cd backend && uvicorn app.main:app --reload`
2. Open `http://127.0.0.1:8000/` → see `{"status": "ok"}`
3. Open `http://127.0.0.1:8000/health` → see `{"status": "healthy"}`
4. Open `http://127.0.0.1:8000/docs` → see FastAPI Swagger UI

**Definition of Done:** Server starts without errors, health check endpoints respond, Swagger UI is accessible.

**Estimated Time:** 30 minutes

**Dependencies:** None.

---

### Sprint 2 — Database Setup & Schema

**Objective:** Set up SQLite connection, create all database tables, and define SQLModel models.

**Files Created:**
- `backend/app/db/__init__.py`
- `backend/app/db/connection.py`
- `backend/app/db/models.py`

**Files Modified:**
- `backend/app/main.py` (add DB initialization)
- `backend/app/__init__.py` (add create_all call)

**Database Changes:**
Create all tables from the schema in Implementation Guide Section 1:
- `knowledge_items`, `evidence`, `knowledge_item_evidence`
- `source_documents`
- `resume_bullets`, `soq_paragraphs`
- `skills`, `knowledge_item_skills`
- `metrics`
- `job_postings`, `applications`, `application_evidence`
- `keywords`, `categories`, `knowledge_item_keywords`
- `knowledge_items_fts` (FTS5 virtual table)
- All triggers and indexes

**Backend Changes:**
- Database connection singleton using SQLModel
- Model definitions for all 11+ tables
- `init_db()` function to create all tables

**Frontend Changes:** None.

**API Endpoints:** None (no external API yet).

**Acceptance Criteria:**
- `init_db()` creates database file at configured path
- All 15+ tables exist after `init_db()`
- FTS5 virtual table is created
- All indexes and triggers are created
- `SQLModel.metadata.create_all(engine)` works without errors

**Manual Testing:**
1. Run a Python script that calls `init_db()`
2. Open the SQLite file in `sqlite3` or DB Browser for SQLite
3. Run `.tables` → see all tables listed
4. Run `SELECT name FROM sqlite_master WHERE type='table'` → verify all tables

**Definition of Done:** All tables, indexes, triggers, and FTS5 virtual table are created successfully via `init_db()`.

**Estimated Time:** 60 minutes

**Dependencies:** Sprint 1.

---

### Sprint 3 — Core Repositories

**Objective:** Implement repositories for knowledge items, evidence, and applications with full CRUD + search.

**Files Created:**
- `backend/app/repositories/__init__.py`
- `backend/app/repositories/base.py`
- `backend/app/repositories/knowledge_item.py`
- `backend/app/repositories/evidence.py`
- `backend/app/repositories/application.py`

**Files Modified:**
- `backend/app/db/models.py` (import models into `__all__`)

**Database Changes:** None (tables already exist from Sprint 2).

**Backend Changes:**
- `KnowledgeItemRepository`: create, get, get_multi, search (FTS5), update, delete, bulk_create, get_with_evidence
- `EvidenceRepository`: create, get (with linked items), get_multi, link_to_item, get_success_rate
- `ApplicationRepository`: create, get, update_result, record_evidence_usage, get_success_weight
- Base repository with common session management

**Frontend Changes:** None.

**API Endpoints:** None.

**Acceptance Criteria:**
- All repository methods return correct pydantic models
- `search()` uses FTS5 and returns ranked results
- `get_success_rate()` correctly computes interview/offer ratio
- `get_success_weight()` returns float between 0.0 and 0.3+
- All methods handle non-existent IDs gracefully

**Manual Testing:**
1. Run pytest on repository tests
2. In a REPL, create an evidence record and verify it persists
3. Create a knowledge item linked to evidence, then fetch with `get_with_evidence`
4. Search for a keyword and verify FTS5 returns results

**Definition of Done:** All repository tests pass, CRUD operations verified manually.

**Estimated Time:** 90 minutes

**Dependencies:** Sprint 2.

---

### Sprint 4 — API CRUD Layer

**Objective:** Implement FastAPI API endpoints for knowledge items, evidence, and applications.

**Files Created:**
- `backend/app/api/__init__.py`
- `backend/app/api/v1/__init__.py`
- `backend/app/api/v1/knowledge.py`
- `backend/app/api/v1/evidence.py`
- `backend/app/api/v1/applications.py`

**Files Modified:**
- `backend/app/main.py` (include routers)

**Database Changes:** None.

**Backend Changes:**
- FastAPI routers for knowledge items, evidence, applications
- Dependency injection for database session
- Pydantic schemas for request/response validation
- Error handling (404 for non-existent IDs, 400 for validation errors)

**Frontend Changes:** None.

**API Endpoints:**
- `GET /api/v1/knowledge-items/` — paginated list
- `GET /api/v1/knowledge-items/{id}` — get single
- `POST /api/v1/knowledge-items/` — create
- `PUT /api/v1/knowledge-items/{id}` — update
- `DELETE /api/v1/knowledge-items/{id}` — delete
- `GET /api/v1/knowledge-items/search?q=` — FTS5 search
- `GET /api/v1/evidence/` — list
- `GET /api/v1/evidence/{id}` — get with linked items
- `POST /api/v1/evidence/` — create
- `POST /api/v1/evidence/link` — link items to evidence
- `GET /api/v1/applications/` — list
- `POST /api/v1/applications/` — create
- `POST /api/v1/applications/{id}/result` — update result

**Acceptance Criteria:**
- All endpoints return correct HTTP status codes
- Request/response bodies match schemas
- Error responses are structured (not raw exceptions)
- Swagger UI shows all endpoints with schemas

**Manual Testing:**
1. Start server
2. Use Swagger UI or curl to test each endpoint
3. Verify 404 for non-existent IDs
4. Verify 200 for valid requests

**Definition of Done:** All API endpoints tested via Swagger UI, responses match schemas, error handling works.

**Estimated Time:** 120 minutes

**Dependencies:** Sprint 3.

---

### Sprint 5 — Backend Tests

**Objective:** Set up pytest framework and write tests for repositories and API endpoints.

**Files Created:**
- `backend/tests/__init__.py`
- `backend/tests/conftest.py`
- `backend/tests/test_repositories.py`
- `backend/tests/test_api.py`
- `backend/tests/test_models.py`

**Files Modified:**
- `backend/pyproject.toml` (add pytest config)

**Database Changes:** None (use in-memory SQLite for tests).

**Backend Changes:**
- pytest fixtures for database (in-memory SQLite)
- Factory functions for test data
- Tests for repository CRUD operations
- Tests for FTS5 search
- Tests for API endpoints (using TestClient)

**Frontend Changes:** None.

**API Endpoints:** N/A (testing existing endpoints).

**Acceptance Criteria:**
- `pytest` runs with 0 failures
- Repository tests cover create, get, update, delete, search
- API tests cover 200/404 responses for all endpoints
- Test coverage >= 80% for repositories and API

**Manual Testing:**
1. Run `cd backend && pytest -v`
2. Verify all tests pass
3. Run `pytest --cov=app` and verify coverage

**Definition of Done:** All backend tests pass, coverage >= 80% for repositories and API.

**Estimated Time:** 120 minutes

**Dependencies:** Sprint 4.

---
## Phase 1: Frontend Foundation (Sprints 6-7)

### Sprint 6 — Frontend Scaffolding

**Objective:** Set up the React + TypeScript + Vite + Tauri frontend project with routing and layout.

**Files Created:**
- `frontend/package.json`
- `frontend/tsconfig.json`
- `frontend/vite.config.ts`
- `frontend/src/main.tsx`
- `frontend/src/app.tsx`
- `frontend/src/routes/index.tsx`
- `frontend/src/pages/Dashboard.tsx`
- `frontend/src/components/layout.tsx`
- `frontend/tauri.conf.ts`
- `frontend/src/types/index.ts` (shared types)

**Files Modified:**
- `package.json` (root) — add frontend workspace reference

**Database Changes:** None.

**Backend Changes:** None.

**Frontend Changes:**
- Vite + React + TypeScript project
- Tauri configuration
- Basic routing (Dashboard as default route)
- Layout component (sidebar, header)
- Shared TypeScript types matching backend schemas

**API Endpoints:** None.

**Acceptance Criteria:**
- `npm install` (in frontend/) succeeds
- `npm run dev` starts the Vite dev server
- Tauri dev mode works (`npm run tauri dev`)
- Dashboard page renders with placeholder content
- TypeScript compiles without errors
- Shared types are compatible with backend schemas

**Manual Testing:**
1. Run `cd frontend && npm install`
2. Run `npm run dev` — Vite starts on port 5173
3. Run `npm run tauri dev` — Tauri window opens
4. Verify Dashboard page loads

**Definition of Done:** Frontend project runs in both browser dev mode and Tauri dev mode, Dashboard renders.

**Estimated Time:** 90 minutes

**Dependencies:** Sprint 1 (for shared type definitions).

---

### Sprint 7 — API Client & React Contexts

**Objective:** Create the Axios API client, React contexts, and data-fetching hooks.

**Files Created:**
- `frontend/src/api/client.ts` (Axios instance)
- `frontend/src/api/knowledge.ts` (typed API calls)
- `frontend/src/api/evidence.ts`
- `frontend/src/contexts/KnowledgeBaseContext.tsx`
- `frontend/src/contexts/BuilderContext.tsx`
- `frontend/src/contexts/UIContext.tsx`
- `frontend/src/hooks/useKnowledgeItems.ts`
- `frontend/src/hooks/useSearch.ts`

**Files Modified:**
- `frontend/src/app.tsx` (wrap app in providers)
- `frontend/src/routes/index.tsx` (add routes)

**Database Changes:** None.

**Backend Changes:** None.

**Frontend Changes:**
- Axios client with base URL `http://127.0.0.1:8000/api/v1`
- Typed API call functions for knowledge items and evidence
- KnowledgeBaseContext: provides items, evidence, search, refresh
- BuilderContext: manages builder state (selected items, current builder type)
- UIContext: theme, sidebar state, toast notifications
- useKnowledgeItems hook: fetches items, handles loading states
- useSearch hook: debounced search with filters

**API Endpoints:**
- `GET /api/v1/knowledge-items/` (consumed)
- `GET /api/v1/knowledge-items/search?q=` (consumed)

**Acceptance Criteria:**
- API client successfully calls backend endpoints
- React contexts provide correct initial state
- Hooks return loading states and data
- TypeScript types match backend schemas
- Error handling in API client (404, 500)

**Manual Testing:**
1. Start backend (`uvicorn app.main:app --reload`)
2. Start frontend (`npm run dev`)
3. Open browser dev tools → Network tab
4. Navigate to Dashboard → verify API calls are made
5. Verify error handling when backend is down

**Definition of Done:** API client works, contexts provide state, hooks fetch data, types match backend.

**Estimated Time:** 90 minutes

**Dependencies:** Sprints 1, 4, 6.

---
## Phase 2: Import Pipeline (Sprints 8-12)

### Sprint 8 — DOCX Parser

**Objective:** Implement the DOCX parser that extracts text, paragraphs, styling, and bullet/heading structure.

**Inputs:** A sample DOCX file (resume with bullets, SOQ with headings).

**Outputs:** `DocxParser` class that returns `ParsedDocument` with paragraphs, bullet levels, heading levels, and text content.

**Files Created:**
- `backend/app/parsers/__init__.py`
- `backend/app/parsers/base.py`
- `backend/app/parsers/docx_parser.py`
- `backend/tests/test_parsers.py` (DOCX tests)
- `backend/tests/fixtures/sample_resume.docx`
- `backend/tests/fixtures/sample_soq.docx`

**Files Modified:** None.

**Database Changes:** None.

**Backend Changes:**
- `BaseParser` abstract class with `parse()` method
- `ParsedDocument` and `Paragraph` pydantic models
- `DocxParser`: uses `python-docx`, extracts:
  - Paragraph text
  - Style name (Normal, Heading 1, List Bullet, etc.)
  - Bullet detection (based on style or numbering)
  - Bullet level (indent-based)
  - Heading level (extracted from style)

**Frontend Changes:** None.

**API Endpoints:** None.

**Acceptance Criteria:**
- `DocxParser().parse("sample_resume.docx")` returns `ParsedDocument` with paragraphs
- Bullets are correctly identified (style == "List Bullet" or has numbering)
- Bullet levels are correctly extracted from indentation
- Headings are correctly identified
- Text content matches the original document

**Manual Testing:**
1. Create a DOCX with 2-3 jobs, each with bullets
2. Parse it with `DocxParser`
3. Print the paragraphs → verify bullets and headings are identified
4. Verify bullet level hierarchy

**Definition of Done:** DOCX parser correctly extracts text, bullets, and headings from test fixtures. All parser tests pass.

**Estimated Time:** 90 minutes

**Dependencies:** Sprint 2 (models), Sprint 1 (project setup).

---

### Sprint 9 — PDF and TXT Parsers

**Objective:** Implement PDF and TXT parsers to complete the import pipeline's parsing layer.

**Files Created:**
- `backend/app/parsers/pdf_parser.py`
- `backend/app/parsers/txt_parser.py`

**Files Modified:**
- `backend/tests/fixtures/sample_duty.txt`
- `backend/tests/test_parsers.py` (add PDF and TXT tests)

**Database Changes:** None.

**Backend Changes:**
- `PdfParser`: uses `pymupdf` (fitz), extracts text with basic layout preservation
- `TxtParser`: simple line-by-line reader, all text as "Normal" style
- `get_parser()` factory function: dispatches to correct parser based on file type

**Frontend Changes:** None.

**API Endpoints:** None.

**Acceptance Criteria:**
- `PdfParser().parse("sample.pdf")` returns `ParsedDocument` with all text
- `TxtParser().parse("sample.txt")` returns `ParsedDocument` with all lines
- `get_parser("docx")` returns `DocxParser` instance
- `get_parser("pdf")` returns `PdfParser` instance
- `get_parser("txt")` returns `TxtParser` instance
- `get_parser("unknown")` raises `ValueError`

**Manual Testing:**
1. Create a simple PDF with text
2. Parse it with `PdfParser`
3. Verify all text is extracted correctly
4. Create a TXT file with multiple lines
5. Parse it with `TxtParser`
6. Verify factory function dispatches correctly

**Definition of Done:** All three parsers work with test fixtures, factory function correctly dispatches, all parser tests pass.

**Estimated Time:** 60 minutes

**Dependencies:** Sprint 8.

---

### Sprint 10 — Extraction Service (Content Classification)

**Objective:** Implement the content classifier that turns parsed paragraphs into structured Knowledge Items, evidence, and keywords.

**Files Created:**
- `backend/app/services/__init__.py`
- `backend/app/services/extraction_service.py`
- `backend/app/models/knowledge.py` (pydantic response schemas)
- `backend/app/models/evidence.py`
- `backend/app/data/synonyms.json` (small sample)
- `backend/app/data/categories.json` (small sample)

**Files Modified:** None.

**Database Changes:** None.

**Backend Changes:**
- `ExtractionService` class with:
  - `classify_paragraph(text, paragraph_info) -> ParagraphType`: rule-based (bullet patterns, heading detection, question-answer patterns)
  - `extract_resume_bullets(lines) -> list[BulletData]`: groups consecutive bullets under a job heading
  - `extract_soq_paragraphs(lines) -> list[SOQData]`: detects "Question: / Answer:" patterns, or heading-based Q&A
  - `extract_skills(text) -> list[str]`: standalone skill-like phrases
  - `extract_metrics(text) -> list[MetricData]`: numbers, percentages, dollar amounts
  - `assign_category(content, ptype) -> str`: keyword-based category assignment
  - `extract_keywords(content) -> list[str]`: simple tokenization + stopword removal

**Frontend Changes:** None.

**API Endpoints:** None.

**Acceptance Criteria:**
- `classify_paragraph()` correctly identifies: resume_bullet, soq_question, soq_answer, heading, normal_text
- `extract_resume_bullets()` groups bullets under job headings with company + role
- `extract_soq_paragraphs()` pairs questions with answers
- `extract_skills()` identifies standalone skill phrases
- `extract_metrics()` identifies percentages, dollar amounts, counts
- `assign_category()` assigns "Customer Service", "Analysis", "Confidential Information", etc.
- `extract_keywords()` returns cleaned tokens

**Manual Testing:**
1. Parse `sample_resume.docx` with DocxParser
2. Feed parsed paragraphs into `ExtractionService`
3. Verify bullets are extracted with job context
4. Parse `sample_soq.docx`
5. Verify Q&A pairs are extracted
6. Check category assignment on a few items

**Definition of Done:** Extraction service correctly classifies and extracts all content types from test fixtures. All extraction tests pass.

**Estimated Time:** 120 minutes

**Dependencies:** Sprints 8, 9 (parsers).

---

### Sprint 11 — Import Service & API

**Objective:** Implement the ImportService that orchestrates the full import pipeline, and create the API endpoints for upload and status checking.

**Files Created:**
- `backend/app/services/import_service.py`
- `backend/app/repositories/document.py` (source_documents repository)
- `backend/app/api/v1/import_.py`
- `backend/app/models/document.py` (pydantic schemas for import responses)
- `backend/app/core/exceptions.py`
- `backend/tests/fixtures/sample_resume.docx` (already exists)

**Files Modified:**
- `backend/app/main.py` (include import router)
- `backend/app/db/models.py` (add SourceDocument model)

**Database Changes:**
- Add `source_documents` model to database (already exists in schema, ensure SQLModel model is created)

**Backend Changes:**
- `ImportService.process_upload(file_path, file_type)`: saves source doc, parses, extracts, creates knowledge items + evidence + links
- `ImportService.process_text(text, source_doc_id, doc_type)`: in-memory processing for tests
- Repository for source_documents
- API router with:
  - `POST /import/` — accepts multipart form upload
  - `GET /import/status/{job_id}` — returns processing status

**Frontend Changes:** None.

**API Endpoints:**
- `POST /api/v1/import/` — Upload + process document
- `GET /api/v1/import/status/{job_id}` — Check import progress

**Acceptance Criteria:**
- Upload endpoint accepts DOCX, PDF, TXT files (max 50MB)
- Import returns `job_id` and `source_doc_id`
- Status endpoint returns "processing", "completed", or "failed"
- Import creates knowledge items + evidence records in DB
- Import creates source_documents record
- Errors are handled gracefully (failed import returns error message)

**Manual Testing:**
1. Start backend
2. POST a DOCX file to `/api/v1/import/`
3. Check response has `job_id` and `source_doc_id`
4. Query status endpoint → should return "completed"
5. Query `/api/v1/knowledge-items/` → should show imported items
6. Query `/api/v1/evidence/` → should show evidence records

**Definition of Done:** Import endpoint works end-to-end, creates correct database records, all import tests pass.

**Estimated Time:** 120 minutes

**Dependencies:** Sprints 9, 10.

---

### Sprint 12 — Import UI

**Objective:** Create the frontend Import page with file uploader and progress tracking.

**Files Created:**
- `frontend/src/pages/ImportDocuments.tsx`
- `frontend/src/components/FileUploader.tsx`
- `frontend/src/components/ProgressTracker.tsx`
- `frontend/src/api/import.ts`

**Files Modified:**
- `frontend/src/routes/index.tsx` (add /import route)
- `frontend/src/app.tsx` (add navigation link)

**Database Changes:** None.

**Backend Changes:** None.

**Frontend Changes:**
- `FileUploader`: drag-drop zone, file selection dialog, file type validation
- `ProgressTracker`: progress bar for upload and processing
- `ImportDocuments` page: file list, import history, status display
- API client for `/import/` and `/import/status/{job_id}`
- Polling for import status

**API Endpoints:**
- `POST /api/v1/import/` (consumed)
- `GET /api/v1/import/status/{job_id}` (consumed)

**Acceptance Criteria:**
- User can drag-drop or click to select a file
- File type validation prevents unsupported formats
- Progress bar shows during upload and processing
- Import results are displayed (items created, source document)
- Import history is visible on the page

**Manual Testing:**
1. Start backend + frontend
2. Navigate to Import page
3. Drag a DOCX file onto the drop zone
4. Verify progress bar appears during processing
5. Verify success message and item count after completion
6. Navigate to Knowledge Explorer → see imported items

**Definition of Done:** Import UI works end-to-end, user can import files and see results.

**Estimated Time:** 90 minutes

**Dependencies:** Sprint 11, Sprint 6, Sprint 7.

---
## Phase 3: Resume Builder (Sprints 13-15)

### Sprint 13 — Resume Template Engine

**Objective:** Implement the JSON-based template engine for resume assembly.

**Files Created:**
- `backend/app/services/template_engine.py`
- `backend/app/data/resume_templates/standard.json`
- `backend/app/models/resume.py` (pydantic schemas)
- `backend/tests/test_template_engine.py`

**Files Modified:** None.

**Database Changes:** None.

**Backend Changes:**
- `TemplateEngine` class:
  - `load_template(name: str) -> dict`: loads JSON template from `data/resume_templates/`
  - `render(template: dict, items: list[KnowledgeItem], evidence: list[Evidence], user_profile: dict) -> RenderedDocument`: assembles document structure
  - `apply_formatting(doc: RenderedDocument, fmt: dict) -> FormattedDocument`: applies font, spacing, etc. (metadata only in MVP)
- Template format: JSON with sections, item types, formatting rules (see Implementation Guide Section 9)
- Default "standard" template: Summary → Experience → Skills → Projects

**Frontend Changes:** None.

**API Endpoints:** None.

**Acceptance Criteria:**
- `load_template("standard")` returns valid JSON dict
- `render()` correctly groups bullets by evidence (job position)
- `render()` correctly separates skills and projects sections
- Empty sections are omitted
- Output document structure matches template definition

**Manual Testing:**
1. Load "standard" template
2. Create mock knowledge items (3 bullets from 2 jobs, 5 skills, 1 project)
3. Call `render()` with template + items + mock user profile
4. Verify document structure: Summary section with profile, Experience section with 2 job groups, Skills section, Projects section
5. Verify traceabilities are generated

**Definition of Done:** Template engine loads and renders templates correctly, all template tests pass.

**Estimated Time:** 120 minutes

**Dependencies:** Sprint 3 (models), Sprint 5 (tests).

---

### Sprint 14 — Resume Builder Service & API

**Objective:** Implement the ResumeBuilderService and its API endpoint.

**Files Created:**
- `backend/app/services/resume_builder.py`
- `backend/app/api/v1/build.py` (build endpoints)
- `backend/app/models/build.py` (BuiltDocument, TraceabilityMap schemas)

**Files Modified:**
- `backend/app/main.py` (include build router)

**Database Changes:** None.

**Backend Changes:**
- `ResumeBuilderService`:
  - `build_resume(item_ids, user_profile, template) -> BuiltDocument`: fetches items, groups by section, calls TemplateEngine
  - `auto_build_resume(job_posting_id, template) -> BuiltDocument`: auto-selects best evidence via MatchingService
- API endpoints:
  - `POST /api/v1/build/suggest` — get evidence suggestions for a query
  - `POST /api/v1/build/resume` — assemble resume from selected items
- BuiltDocument schema: includes `document_id`, `content` (sections), `traceability` (item_id → evidence_id)

**Frontend Changes:** None.

**API Endpoints:**
- `POST /api/v1/build/suggest` — Get evidence suggestions
- `POST /api/v1/build/resume` — Build resume

**Acceptance Criteria:**
- `build_resume()` returns structured document with sections and traceability
- `auto_build_resume()` uses MatchingService to select items
- `/build/suggest` returns ranked suggestions for a query
- `/build/resume` returns a BuiltDocument with correct structure
- Traceability dict maps all item IDs to evidence IDs

**Manual Testing:**
1. Start backend, import some resume bullets
2. POST to `/build/resume` with 3 item IDs and user profile
3. Verify response has document_id, sections, traceability
4. POST to `/build/suggest` with query "customer service"
5. Verify suggestions are returned with scores

**Definition of Done:** Resume builder service works, API endpoints return correct structures, all builder tests pass.

**Estimated Time:** 90 minutes

**Dependencies:** Sprint 13 (template engine), Sprint 3 (repositories).

---

### Sprint 15 — Resume Builder UI

**Objective:** Create the Resume Builder page with suggestion panel, content editor, and document preview.

**Files Created:**
- `frontend/src/pages/ResumeBuilder.tsx`
- `frontend/src/components/SuggestionPanel.tsx`
- `frontend/src/components/ContentEditor.tsx`
- `frontend/src/components/DocumentPreview.tsx`
- `frontend/src/components/SectionOrganizer.tsx`
- `frontend/src/api/build.ts`
- `frontend/src/types/resume.ts`

**Files Modified:**
- `frontend/src/routes/index.tsx` (add /resume route)
- `frontend/src/app.tsx` (add nav link)

**Database Changes:** None.

**Backend Changes:** None.

**Frontend Changes:**
- `ResumeBuilder` page: layout with left sidebar (suggestions), center (content editor), right (preview)
- `SuggestionPanel`: shows ranked evidence suggestions with scores and star ratings
- `ContentEditor`: editable text area with item selection
- `DocumentPreview`: renders the assembled resume with traceability markers
- `SectionOrganizer`: drag-drop reordering of sections
- API client for `/build/suggest` and `/build/resume`

**API Endpoints:**
- `POST /api/v1/build/suggest` (consumed)
- `POST /api/v1/build/resume` (consumed)

**Acceptance Criteria:**
- User can enter a job title or paste job description
- Suggestions panel shows ranked evidence items
- User can add/remove items from the resume
- Document preview updates in real-time
- User can reorder sections via drag-drop
- "Export" button triggers export flow (to be connected in Sprint 28)

**Manual Testing:**
1. Start backend + frontend
2. Navigate to Resume Builder
3. Type "customer service" in the prompt → see suggestions
4. Add 3 bullets → verify they appear in preview
5. Drag sections to reorder → verify order changes
6. Click Export → verify (stub) export call

**Definition of Done:** Resume builder UI is fully functional, user can assemble a resume from evidence, all component tests pass.

**Estimated Time:** 150 minutes

**Dependencies:** Sprint 14 (build API), Sprint 7 (API client), Sprint 6 (frontend scaff).

---
## Phase 4: SOQ Builder (Sprints 16-18)

### Sprint 16 — SOQ Builder Service

**Objective:** Implement the SOQBuilderService that answers SOQ questions using evidence from the knowledge base.

**Files Created:**
- `backend/app/services/soq_builder.py`
- `backend/app/models/soq.py` (pydantic schemas: SOQData, SOQResponse)

**Files Modified:**
- `backend/app/api/v1/build.py` (add SOQ endpoint)
- `backend/tests/test_services.py` (add SOQ tests)

**Database Changes:** None.

**Backend Changes:**
- `SOQBuilderService`:
  - `answer_question(question, selected_item_ids, max_words) -> BuiltDocument`: fetches items, assembles structured response
  - `suggest_items(question) -> list[Suggestion]`: uses MatchingService to find best evidence for the question
- API endpoint:
  - `POST /api/v1/build/soq` — answer an SOQ question

**Frontend Changes:** None.

**API Endpoints:**
- `POST /api/v1/build/soq` — Answer SOQ question
- `POST /api/v1/build/suggest` — (modified to accept SOQ question context)

**Acceptance Criteria:**
- `suggest_items()` returns relevant evidence for a given SOQ question
- `answer_question()` assembles a structured SOQ response from selected items
- Response includes traceability mapping
- Word count is enforced (max_words parameter)
- Empty items are filtered out

**Manual Testing:**
1. Start backend with imported SOQ paragraphs
2. POST to `/build/suggest` with "Describe your analytical experience"
3. Verify suggestions include relevant SOQ paragraphs
4. POST to `/build/soq` with question + selected item IDs
5. Verify response has content and traceability

**Definition of Done:** SOQ builder service works end-to-end, API endpoint returns correct structure, tests pass.

**Estimated Time:** 90 minutes

**Dependencies:** Sprint 14 (MatchingService integration), Sprint 3 (repositories).

---

### Sprint 17 — SOQ Question Analyzer

**Objective:** Implement the SOQ question analyzer that categorizes SOQ questions and extracts keywords for better matching.

**Files Created:**
- `backend/app/services/soq_analyzer.py`

**Files Modified:**
- `backend/app/services/soq_builder.py` (integrate analyzer)
- `backend/app/data/soq_categories.json` (category → keyword mapping)
- `backend/tests/test_soq_analyzer.py`

**Database Changes:** None.

**Backend Changes:**
- `SOQAnalyzer` class:
  - `classify_question(question: str) -> str`: returns category (e.g., "Analysis", "Communication", "Confidential Information", "Problem Solving")
  - `extract_keywords(question: str) -> list[str]`: extracts domain-relevant keywords
  - `analyze(question: str) -> SOQAnalysis`: returns both category and keywords
- Category mapping file: `soq_categories.json` with keyword patterns per category

**Frontend Changes:** None.

**API Endpoints:** None (internal service).

**Acceptance Criteria:**
- `classify_question("Describe your analytical experience")` → "Analysis"
- `classify_question("Describe how you handled confidential information")` → "Confidential Information"
- `classify_question("Tell us about your communication skills")` → "Communication"
- `extract_keywords()` returns relevant domain terms
- Unknown questions get a default category

**Manual Testing:**
1. Run analyzer on 4-5 sample SOQ questions
2. Verify correct categories are assigned
3. Verify keywords are extracted
4. Check edge cases (short questions, ambiguous topics)

**Definition of Done:** SOQ analyzer correctly classifies 90%+ of sample questions, tests pass.

**Estimated Time:** 60 minutes

**Dependencies:** Sprint 16.

---

### Sprint 18 — SOQ Builder UI

**Objective:** Create the SOQ Builder page with question input, evidence suggestions, content editor, and export.

**Files Created:**
- `frontend/src/pages/SOQBuilder.tsx`
- `frontend/src/components/SOQQuestionInput.tsx`
- `frontend/src/components/SOQEditor.tsx`

**Files Modified:**
- `frontend/src/routes/index.tsx` (add /soq route)
- `frontend/src/app.tsx` (add nav link)

**Database Changes:** None.

**Backend Changes:** None.

**Frontend Changes:**
- `SOQBuilder` page: question input at top, suggestions panel on left, editor in center, preview on right
- `SOQQuestionInput`: text area for the SOQ question, with category auto-detection display
- `SOQEditor`: editable response area with evidence markers, word count display
- Integration with `/build/suggest` and `/build/soq` API endpoints
- Word count visualization (progress bar toward max_words limit)

**API Endpoints:**
- `POST /api/v1/build/suggest` (consumed)
- `POST /api/v1/build/soq` (consumed)

**Acceptance Criteria:**
- User enters an SOQ question and sees category auto-detection
- Suggestions panel shows ranked evidence with star ratings
- User can select/deselect evidence items
- Editor shows word count and updates in real-time
- Preview shows assembled SOQ response
- Export button triggers export (stub until Sprint 27)

**Manual Testing:**
1. Start backend + frontend
2. Navigate to SOQ Builder
3. Enter "Describe your experience handling confidential information"
4. Verify category is detected as "Confidential Information"
5. Add suggestions → verify they appear in editor
6. Check word count updates

**Definition of Done:** SOQ builder UI is fully functional, user can answer SOQ questions from evidence, component tests pass.

**Estimated Time:** 120 minutes

**Dependencies:** Sprint 16, Sprint 17, Sprint 7, Sprint 6.

---
## Phase 5: Duty Statement Generator (Sprints 19-21)

### Sprint 19 — Duty Statement Parser

**Objective:** Implement the duty statement parser that extracts requirements and responsibilities from a job posting's duty statement.

**Files Created:**
- `backend/app/services/duty_statement_parser.py`
- `backend/app/models/duty.py` (pydantic schemas)

**Files Modified:** None.

**Database Changes:** None.

**Backend Changes:**
- `DutyStatementParser` class:
  - `parse(text: str) -> list[DutyRequirement]`: extracts individual duty statements from raw text
  - `extract_keywords(requirements: list[DutyRequirement]) -> list[str]`: pulls key terms from duties
  - `classify_requirement(req: DutyRequirement) -> str`: maps to a category (e.g., "Customer Service", "Analysis")
- DutyStatement model: list of requirements, each with text, category, keywords

**Frontend Changes:** None.

**API Endpoints:** None.

**Acceptance Criteria:**
- `parse()` correctly extracts individual duty statements from a paragraph-formatted text
- Each requirement has correct category classification
- Keywords are extracted from each requirement
- Handles numbered and bulleted duty statements
- Handles indented and non-indented formats

**Manual Testing:**
1. Provide a sample duty statement text
2. Parse it → verify individual duties are extracted
3. Check categories on a few duties
4. Verify keywords are extracted

**Definition of Done:** Duty statement parser correctly parses sample job postings, tests pass.

**Estimated Time:** 60 minutes

**Dependencies:** Sprint 10 (ExtractionService), Sprint 17 (category classification patterns).

---

### Sprint 20 — Duty Statement Builder Service

**Objective:** Implement the DutyStatementBuilderService that generates duty statement responses by matching job requirements to existing evidence.

**Files Created:**
- `backend/app/services/duty_statement_builder.py`

**Files Modified:**
- `backend/app/api/v1/build.py` (add duty statement endpoint)
- `backend/tests/test_duty_statement.py`

**Database Changes:** None.

**Backend Changes:**
- `DutyStatementBuilderService`:
  - `generate_response(job_posting_id, selected_item_ids) -> BuiltDocument`: for each duty requirement, find matching evidence and assemble response paragraph
  - `suggest_items(duty_statement_text) -> list[Suggestion]`: uses MatchingService to find best evidence for each duty
- API endpoint:
  - `POST /api/v1/build/duty-statement` — generate duty statement response

**Frontend Changes:** None.

**API Endpoints:**
- `POST /api/v1/build/duty-statement` — Generate duty statement

**Acceptance Criteria:**
- `suggest_items()` returns relevant evidence for duty requirements
- `generate_response()` creates a structured response with one paragraph per duty
- Each paragraph is backed by evidence with traceability
- Response mirrors the duty statement's language using existing evidence

**Manual Testing:**
1. Start backend with imported resume bullets
2. Create a job posting with a duty statement
3. POST to `/build/duty-statement` with job_posting_id
4. Verify response has paragraphs, each linked to evidence
5. Verify traceability mapping

**Definition of Done:** Duty statement builder service works end-to-end, API returns correct structure, tests pass.

**Estimated Time:** 90 minutes

**Dependencies:** Sprint 19, Sprint 14 (build API), Sprint 25 (MatchingEngine - stub if not ready).

---

### Sprint 21 — Duty Statement Builder UI

**Objective:** Create the Duty Statement Builder page where users can paste a job posting and generate evidence-backed duty statement responses.

**Files Created:**
- `frontend/src/pages/DutyStatementBuilder.tsx`
- `frontend/src/components/DutyStatementInput.tsx`
- `frontend/src/components/DutyStatementResponse.tsx`

**Files Modified:**
- `frontend/src/routes/index.tsx` (add /duty route)
- `frontend/src/app.tsx` (add nav link)

**Database Changes:** None.

**Backend Changes:** None.

**Frontend Changes:**
- `DutyStatementBuilder` page: job posting input on left, matched evidence suggestions in center, assembled response on right
- `DutyStatementInput`: text area for job posting duty statement, with "Parse Duties" button
- `DutyStatementResponse`: shows each duty requirement with matched evidence, allows editing
- Integration with `/build/suggest` and `/build/duty-statement` API endpoints

**API Endpoints:**
- `POST /api/v1/build/suggest` (consumed)
- `POST /api/v1/build/duty-statement` (consumed)

**Acceptance Criteria:**
- User can paste a duty statement and see parsed requirements
- Each requirement shows matched evidence suggestions
- User can select/deselect evidence items
- Response preview shows assembled paragraphs
- All content is traceability-linked to evidence
- Export button triggers export (stub until Sprint 27)

**Manual Testing:**
1. Start backend + frontend
2. Navigate to Duty Statement Builder
3. Paste a sample duty statement
4. Verify duties are parsed and displayed
5. Click "Suggest Evidence" → see matches
6. Select evidence → verify response is assembled
7. Check traceability markers

**Definition of Done:** Duty statement UI is fully functional, user can generate evidence-backed responses, component tests pass.

**Estimated Time:** 120 minutes

**Dependencies:** Sprint 20, Sprint 7, Sprint 6.

---
## Phase 6: Evidence Explorer (Sprints 22-24)

### Sprint 22 — Search API Endpoint

**Objective:** Implement the search API endpoint that the Evidence Explorer uses, including matching engine integration.

**Files Created:**
- `backend/app/api/v1/search.py`
- `backend/app/api/v1/match.py` (matching endpoints)

**Files Modified:**
- `backend/app/main.py` (include search/match routers)
- `backend/app/services/matching_service.py` (add search method)

**Database Changes:** None.

**Backend Changes:**
- `MatchingService.match_query()`: TF-IDF vectorization + cosine similarity + historical weighting
- `MatchingService.get_suggestions()`: enriched suggestions with evidence links
- `POST /api/v1/search/` — full evidence explorer search
- `POST /api/v1/match/` — match a job posting to knowledge items
- Response schema: ranked results with items, scores, star ratings, evidence links

**Frontend Changes:** None.

**API Endpoints:**
- `POST /api/v1/search/` — Evidence explorer search
- `POST /api/v1/match/` — Job posting match

**Acceptance Criteria:**
- Search endpoint accepts query, item types, categories, min star rating
- Returns ranked results with scores and star ratings
- Match endpoint returns items that would best address a job posting
- Results are limited by `top_k` parameter
- Search works across all knowledge item types

**Manual Testing:**
1. Start backend with imported data
2. POST to `/search/` with "confidential"
3. Verify results are returned with scores
4. POST to `/match/` with a job posting
5. Verify top suggestions match job requirements

**Definition of Done:** Search and match API endpoints return correctly ranked results, tests pass.

**Estimated Time:** 90 minutes

**Dependencies:** Sprint 3 (repositories), Sprint 25 (TF-IDF may need stub).

---

### Sprint 23 — Evidence Explorer UI (Search + Results)

**Objective:** Create the Evidence Explorer page with VS Code-like search interface and results display.

**Files Created:**
- `frontend/src/pages/KnowledgeExplorer.tsx`
- `frontend/src/components/SearchBar.tsx`
- `frontend/src/components/SearchFilters.tsx`
- `frontend/src/components/ResultsList.tsx`
- `frontend/src/components/StarRating.tsx`

**Files Modified:**
- `frontend/src/routes/index.tsx` (add /explore route)
- `frontend/src/app.tsx` (add nav link)

**Database Changes:** None.

**Backend Changes:** None.

**Frontend Changes:**
- `KnowledgeExplorer` page: search bar at top, filters sidebar, results list
- `SearchBar`: text input with debouncing, "Search" button
- `SearchFilters`: collapsible panel for type, category, star rating filters
- `ResultsList`: grid/list of `MatchResult` components
- `StarRating` component: 5-star display with match quality
- API client for `/search/`

**API Endpoints:**
- `POST /api/v1/search/` (consumed)

**Acceptance Criteria:**
- Search bar triggers debounced search
- Filters can be applied (type, category, min star rating)
- Results show: item content, score, star rating, category tag, evidence badge
- Results are sortable (by relevance, date, star rating)
- Loading state is displayed during search

**Manual Testing:**
1. Start backend + frontend
2. Navigate to Knowledge Explorer
3. Search "confidential" → verify results appear
4. Apply type filter "soq_paragraph" → verify only SOQ paragraphs show
5. Apply min star rating 4 → verify only 4+ star items show
6. Verify star ratings are displayed correctly

**Definition of Done:** Evidence Explorer search works, filters function, results display with star ratings, component tests pass.

**Estimated Time:** 150 minutes

**Dependencies:** Sprint 22 (search API), Sprint 7 (contexts), Sprint 6.

---

### Sprint 24 — Evidence Explorer (Provenance Panel)

**Objective:** Add the provenance panel that shows detailed trace information when a search result is clicked.

**Files Created:**
- `frontend/src/components/ProvenancePanel.tsx`
- `frontend/src/components/EvidenceBadge.tsx`

**Files Modified:**
- `frontend/src/pages/KnowledgeExplorer.tsx` (add click handler)
- `frontend/src/components/MatchResult.tsx` (add click)
- `frontend/src/api/knowledge.ts` (add evidence detail endpoint call)

**Database Changes:** None.

**Backend Changes:** None (uses existing endpoints).

**Frontend Changes:**
- `ProvenancePanel`: side panel or modal showing item details
- Displays: original source document, linked evidence, which resumes/SOQs use this item, which skills it supports, which applications it was used in, whether it contributed to an interview
- `EvidenceBadge`: small badge showing evidence source name + success icons
- Click handler on MatchResult opens ProvenancePanel
- API calls to fetch linked evidence and usage history

**API Endpoints:**
- `GET /api/v1/knowledge-items/{id}` (consumed — with evidence links)
- `GET /api/v1/evidence/{id}` (consumed)

**Acceptance Criteria:**
- Clicking a search result opens provenance panel
- Panel shows source document and link
- Panel shows linked evidence with star ratings
- Panel shows usage history (which applications used this item)
- Panel shows interview/offer outcomes if any
- EvidenceBadge displays correctly in results

**Manual Testing:**
1. Start backend + frontend
2. Search and click a result
3. Verify provenance panel opens
4. Verify source document is shown
5. Verify evidence links are clickable
6. Verify usage history shows (if any applications exist)

**Definition of Done:** Provenance panel works with full traceability info, component tests pass.

**Estimated Time:** 120 minutes

**Dependencies:** Sprint 23, Sprint 7.

---
## Phase 7: Matching Engine (Sprints 25-26)

### Sprint 25 — TF-IDF Service & Vectorization

**Objective:** Implement the TF-IDF vectorization service with cosine similarity computation and caching.

**Files Created:**
- `backend/app/services/tfidf_service.py`
- `backend/tests/test_tfidf.py`

**Files Modified:**
- `backend/app/db/models.py` (add TfidfVector model)

**Database Changes:**
- Add `tfidf_vectors` table migration (already in schema from Sprint 2)

**Backend Changes:**
- `TfidfVectorizer` class:
  - `fit(documents: list[str])`: builds vocabulary, computes IDF
  - `transform(text: str) -> dict[str, float]`: TF-IDF vector for text
  - `cosine_similarity(vec_a, vec_b) -> float`
  - `save_index()`: caches vectors in SQLite `tfidf_vectors` table
  - `load_index()`: loads cached vectors
- `TfidfService` class:
  - `build_index(items: list[KnowledgeItem])`: builds and caches TF-IDF index
  - `vectorize_query(query: str) -> SparseVector`
  - `similarity(item_id: str, query_vec: SparseVector) -> float`
  - `rebuild_if_needed()`: checks if index is stale, rebuilds if so

**Frontend Changes:** None.

**API Endpoints:** None.

**Acceptance Criteria:**
- TF-IDF vectors are built from knowledge base content
- Cosine similarity returns correct scores (1.0 for identical, 0.0 for no overlap)
- Vectors are cached in SQLite
- `rebuild_if_needed()` detects new/deleted items
- Caching prevents redundant computation

**Manual Testing:**
1. Create mock knowledge items with known content
2. Call `build_index()`
3. Verify vectors are stored in `tfidf_vectors` table
4. Call `cosine_similarity()` with two identical texts → expect ~1.0
5. Call with two unrelated texts → expect ~0.0
6. Call `rebuild_if_needed()` after adding a new item → expect rebuild

**Definition of Done:** TF-IDF service builds and caches vectors, cosine similarity works correctly, rebuild logic works.

**Estimated Time:** 120 minutes

**Dependencies:** Sprint 3 (repositories), Sprint 2 (DB setup).

---

### Sprint 26 — Historical Success Weighting & Application Tracking

**Objective:** Implement historical success weighting that boosts evidence which has historically led to interviews or offers, and create application tracking endpoints.

**Files Created:**
- `backend/app/services/historical_weighting.py`
- `backend/app/models/application.py`

**Files Modified:**
- `backend/app/services/matching_service.py` (integrate weighting)
- `backend/app/api/v1/applications.py` (add result endpoint)
- `backend/app/repositories/application.py` (add get_success_weight)

**Database Changes:**
- Ensure `applications` and `application_evidence` tables exist with correct schema

**Backend Changes:**
- `HistoricalWeightingService`:
  - `calculate_weight(item_id: str) -> float`: queries application_evidence, computes: `alpha * interview_rate + beta * offer_rate`
  - `update_weights()`: batch recalculates all weights
- Modified `MatchingService.match_query()`: applies historical weight to cosine similarity
- `ApplicationRepository.get_success_weight(item_id)`: returns weight for a given item
- `ApplicationRepository.record_evidence_usage()`: records which items were used in an application
- `POST /api/v1/applications/{id}/result`: update status + record evidence usage

**Frontend Changes:** None.

**API Endpoints:**
- `POST /api/v1/applications/{id}/result` (modified)

**Acceptance Criteria:**
- Historical weight is calculated correctly from application_evidence
- Items used in successful applications get higher weights
- Weights are applied to matching scores (final_score = cosine_sim * (1 + weight))
- Application result endpoint correctly records evidence usage
- Weights are recalculated after application results are updated

**Manual Testing:**
1. Create 3 applications with different results (rejected, interview, offer)
2. Record evidence usage for each
3. Call `calculate_weight()` on a knowledge item used in offer → expect higher weight
4. Call `calculate_weight()` on an item used only in rejected → expect lower/0 weight
5. Run `match_query()` → verify weighted scores differ

**Definition of Done:** Historical weighting is correctly applied to matching scores, application tracking endpoints work.

**Estimated Time:** 90 minutes

**Dependencies:** Sprint 25 (TF-IDF), Sprint 4 (applications API).

---
## Phase 8: Export Pipeline (Sprints 27-28)

### Sprint 27 — Export Service (DOCX + TXT)

**Objective:** Implement the export service that generates DOCX and TXT files from built documents, with embedded traceability.

**Files Created:**
- `backend/app/services/export_service.py`
- `backend/app/api/v1/export.py`
- `backend/tests/test_export.py`

**Files Modified:**
- `backend/app/main.py` (include export router)
- `backend/app/services/resume_builder.py` (call export on build)

**Database Changes:** None.

**Backend Changes:**
- `ExportService` class:
  - `export_to_docx(doc: BuiltDocument, include_traceability: bool = True) -> str`: generates DOCX with python-docx, embeds traceability in custom XML
  - `export_to_txt(doc: BuiltDocument) -> str`: plain text output
  - `save_file(content: bytes, filename: str) -> str`: saves to disk, returns path
- API endpoint:
  - `POST /api/v1/export/` — export a built document

**Frontend Changes:** None.

**API Endpoints:**
- `POST /api/v1/export/` — Export document

**Acceptance Criteria:**
- DOCX export produces a valid .docx file openable in Word/LibreOffice
- DOCX includes section headers, bullet lists, proper formatting
- Traceability XML is embedded when `include_traceability=true`
- TXT export produces readable plain text with bullets and headers
- Export returns file path and size

**Manual Testing:**
1. Start backend
2. Build a resume via API
3. POST to `/api/v1/export/` with format="docx"
4. Open the file in Word/LibreOffice → verify formatting
5. Export as TXT → verify readable text
6. Check traceability file exists (if requested)

**Definition of Done:** Export service generates valid DOCX and TXT files, API works, all export tests pass.

**Estimated Time:** 120 minutes

**Dependencies:** Sprint 14 (build API), Sprint 13 (template engine).

---

### Sprint 28 — Export UI Integration

**Objective:** Wire up the export functionality to the builder UIs and add export controls.

**Files Created:**
- `frontend/src/components/ExportToolbar.tsx`
- `frontend/src/hooks/useExport.ts`
- `frontend/src/components/ExportDialog.tsx`

**Files Modified:**
- `frontend/src/pages/ResumeBuilder.tsx` (add export toolbar)
- `frontend/src/pages/SOQBuilder.tsx` (add export toolbar)
- `frontend/src/pages/DutyStatementBuilder.tsx` (add export toolbar)
- `frontend/src/api/build.ts` (add export API call)

**Database Changes:** None.

**Backend Changes:** None (uses Sprint 27 API).

**Frontend Changes:**
- `ExportToolbar`: buttons for DOCX, PDF, TXT export formats
- `ExportDialog`: format selection, traceability toggle, save location
- `useExport` hook: calls `/api/v1/export/`, handles file saving via Tauri
- Integration in all three builder pages
- Loading state and success/error notifications

**API Endpoints:**
- `POST /api/v1/export/` (consumed)

**Acceptance Criteria:**
- All three builder pages have an Export button
- Export dialog shows format options (DOCX, TXT; PDF is stub)
- Export calls the API with correct format and document_id
- Exported file is saved to disk (via Tauri or download in dev mode)
- Success notification appears after export
- Error handling for failed exports

**Manual Testing:**
1. Start backend + frontend
2. Navigate to Resume Builder
3. Assemble a resume
4. Click Export → choose DOCX → verify file downloads/opens
5. Repeat for SOQ Builder and Duty Statement Builder
6. Try exporting with no items selected → expect validation error

**Definition of Done:** Export is integrated in all three builders, files are generated correctly, component tests pass.

**Estimated Time:** 120 minutes

**Dependencies:** Sprint 27 (export API), Sprint 7 (API client).

---
## Phase 9: Validation Engine (Sprint 29)

### Sprint 29 — Validation Engine

**Objective:** Implement the validation engine that checks document completeness, keyword coverage, and evidence traceability before export.

**Files Created:**
- `backend/app/services/validation_service.py`
- `backend/app/api/v1/validate.py`
- `backend/tests/test_validation.py`

**Files Modified:**
- `backend/app/main.py` (include validate router)
- `frontend/src/pages/ResumeBuilder.tsx` (add validation integration)
- `frontend/src/components/ExportToolbar.tsx` (block export if errors)

**Database Changes:** None.

**Backend Changes:**
- `ValidationService` class:
  - `validate(doc: BuiltDocument, job_posting_keywords: list[str] | None) -> ValidationResult`
  - `CompletenessValidator`: checks required sections present and non-empty
  - `KeywordCoverageValidator`: checks job posting keywords present in content
  - `EvidenceTraceabilityValidator`: verifies all content links to evidence
  - `LengthValidator`: checks word/page limits
- API endpoint:
  - `POST /api/v1/validate/` — validate an assembled document

**Frontend Changes:**
- Validation results displayed as warnings/errors in builder pages
- Export button disabled when there are validation errors
- Validation warnings shown as non-blocking alerts

**API Endpoints:**
- `POST /api/v1/validate/` — Validate document
- `POST /api/v1/validate/` (consumed by builders)

**Acceptance Criteria:**
- Completeness validator catches missing sections
- Keyword coverage validator reports missing keywords and percentage
- Evidence traceability validator flags orphaned content
- Length validator enforces resume and SOQ limits
- Validation result has `valid`, `errors`, `warnings`, `score`
- API returns structured validation result

**Manual Testing:**
1. Build a resume with all sections → validate → expect 0 errors
2. Build a resume missing contact info → validate → expect completeness error
3. Provide job posting keywords → validate → check coverage percentage
4. Verify export is blocked when errors exist

**Definition of Done:** Validation engine checks all four rule types, API returns structured results, UI integration prevents invalid exports.

**Estimated Time:** 120 minutes

**Dependencies:** Sprint 27 (export), Sprint 22 (search/match), Sprint 7 (API client).

---

## Phase 10: LLM Integration (Sprint 30)

### Sprint 30 — Local LLM Integration (Optional)

**Objective:** Implement optional LLM integration for grammar polishing and keyword expansion, with strict safety filters to prevent fact creation.

**Files Created:**
- `backend/app/services/llm_service.py`
- `backend/app/api/v1/llm.py`
- `backend/app/core/llm_config.py`
- `frontend/src/pages/LlmSettings.tsx`
- `frontend/src/components/GrammarSuggestions.tsx`

**Files Modified:**
- `backend/app/main.py` (include LLM router, behind feature flag)
- `backend/app/core/config.py` (add LLM config)
- `frontend/src/pages/Settings.tsx` (add LLM config section)
- `frontend/src/components/SOQEditor.tsx` (add grammar polish button)

**Database Changes:** None.

**Backend Changes:**
- `LLMConfig`: feature flag, endpoint, model, max_tokens, temperature
- `LLMService` class (only initialized when enabled):
  - `grammar_suggestions(text: str) -> list[Suggestion]`: requests only grammar/transitions, filters factual changes
  - `transition_suggestions(text: str) -> list[Suggestion]`
  - `keyword_expansion(query: str) -> list[str]`
- System prompt enforces: "You may ONLY suggest grammar, punctuation, and transition changes. NEVER create new facts."
- `_filter_factual_changes()`: heuristic filter that rejects suggestions altering factual content
- All LLM interactions logged to `logs/llm_audit.log`
- API endpoints behind `/api/v1/llm/` (only registered when `llm.enabled` is true)

**Frontend Changes:**
- `LlmSettings` page: enable/disable, endpoint config, model selection
- `GrammarSuggestions` component: shows suggestions as diffs, accept/reject buttons
- Grammar polish button in SOQEditor and ResumeBuilder

**API Endpoints:**
- `POST /api/v1/llm/grammar` — Grammar suggestions (feature-flagged)
- `POST /api/v1/llm/transitions` — Transition suggestions (feature-flagged)
- `POST /api/v1/llm/keywords` — Keyword expansion (feature-flagged)

**Acceptance Criteria:**
- LLM service is disabled by default
- When enabled, connects to Ollama at configured endpoint
- System prompt is sent with every request
- Grammar suggestions are presented as diffs
- User must explicitly accept each suggestion
- Factual changes are filtered out by heuristics
- All interactions logged to audit file
- Feature flag can be toggled in Settings

**Manual Testing:**
1. Start Ollama with gemma2 model
2. Enable LLM in Settings
3. In SOQ Editor, click "Polish with AI"
4. Verify grammar suggestions appear as diffs
5. Accept a suggestion → verify only grammar changed
6. Try to get a fact-creating suggestion → verify it is filtered
7. Check `logs/llm_audit.log` for logged interactions

**Definition of Done:** LLM integration works as optional feature, safety filters prevent fact creation, audit logging works, all LLM tests pass.

**Estimated Time:** 120 minutes

**Dependencies:** Sprint 16 (SOQ builder), Sprint 7, Sprint 1 (config).

---
## Phase 11: Integration & Polish (Sprints 31-32)

### Sprint 31 — End-to-End Integration Tests

**Objective:** Write and verify end-to-end tests that cover the full workflow from import to export.

**Files Created:**
- `backend/tests/test_e2e.py`
- `backend/tests/fixtures/sample_duty.txt` (already exists)
- `frontend/src/tests/e2e.test.tsx` (optional, if time permits)

**Files Modified:**
- `backend/tests/conftest.py` (add fixtures)

**Database Changes:** None.

**Backend Changes:**
- E2E test suite covering:
  1. Import `sample_resume.docx` → verify 5+ knowledge items created
  2. Import `sample_soq.docx` → verify 2+ SOQ paragraphs created
  3. Search "confidential" → verify results returned
  4. Build resume from extracted bullets → verify traceability
  5. Export resume to DOCX → verify file created
  6. Validate resume → verify 0 errors
  7. Build SOQ response → verify traceability
  8. Export SOQ → verify file created
  9. Match against job posting → verify suggestions
  10. Validate SOQ → verify keyword coverage

**Frontend Changes:** None.

**API Endpoints:** All (consumed in tests).

**Acceptance Criteria:**
- All E2E tests pass
- Full workflow works without errors
- No data loss between import and export
- Traceability is preserved through the entire pipeline
- Test execution time < 30 seconds

**Manual Testing:**
1. Run `cd backend && pytest tests/test_e2e.py -v`
2. Verify all tests pass
3. Manually repeat the flow in the UI to confirm parity

**Definition of Done:** All end-to-end tests pass, full import → search → build → export workflow verified.

**Estimated Time:** 120 minutes

**Dependencies:** All previous sprints.

---

### Sprint 32 — MVP Release & Packaging

**Objective:** Package the Tauri desktop application, create build scripts, and finalize documentation.

**Files Created:**
- `scripts/build.py` (build script)
- `scripts/dev.py` (development mode script)
- `scripts/release.py` (release script)
- `backend/requirements.txt` (final)
- `frontend/package.json` scripts
- `docs/resources/architecture-diagram.png` or ASCII
- `CHANGELOG.md`

**Files Modified:**
- `AGENTS.md` (final review)
- `docs/01_Master_Architecture.md` (update changelog section)
- `frontend/tauri.conf.ts` (final build config)
- `backend/pyproject.toml` (final dependencies)

**Database Changes:** None.

**Backend Changes:**
- Ensure all migrations are compatible with fresh database
- Production startup script that initializes DB + starts uvicorn
- `scripts/dev.py`: starts backend + frontend in parallel

**Frontend Changes:**
- Production build script
- Tauri build configuration
- Error boundaries for all pages

**API Endpoints:** N/A.

**Acceptance Criteria:**
- `scripts/dev.py` starts both backend and frontend in dev mode
- `scripts/build.py` builds the Tauri application for current platform
- `scripts/release.py` creates distributable package
- Application installs and runs on target platform
- All documentation is up to date
- CHANGELOG.md lists all completed features

**Manual Testing:**
1. Run `python scripts/dev.py` → backend + frontend start
2. Run `python scripts/build.py` → Tauri app builds successfully
3. Install and run the built application
4. Import a sample document → verify end-to-end flow works
5. Review all docs are current

**Definition of Done:** Application is packaged and distributable, dev/build scripts work, all docs are finalized, CHANGELOG is complete.

**Estimated Time:** 150 minutes

**Dependencies:** All previous sprints.

---

### Sprint 33 — Sentinel Integration Testers

**Objective:** Register Career OS with Sentinel by writing Tier 1 HTTP testers covering the full API surface, so Sentinel can launch, smoke-test, and feature-test the app automatically.

> **Deferral note:** Intentionally scheduled last. Per `integration.md`, tester facts (launch command, port, auth, served routes) must be verified live against the finished app, and batching all API assertions into one sprint avoids churn across 32 evolving sprints. Pytest suites remain per-sprint throughout (AGENTS.md rule 6); this sprint covers Sentinel-side testing only.

**Inputs:**
- Completed Sprints 1-32 (full API surface, see Implementation Guide Section 2)
- `integration.md` (Sentinel integration checklist)
- Verified live facts: launch command, port 8000, no auth, `GET /health` body marker

**Outputs:**
- Tier 1 HTTP tester module registered in the Sentinel repo (`backend/app/testers/career-os.py`)
- Verified ground-truth block in the tester docstring (launch, port, auth, fallback)
- Updated `integration.md` section documenting the Career OS integration pattern

**Files Created:** None in this repo (tester lives in the Sentinel codebase).

**Files Modified:**
- `integration.md` (document Career OS integration)

**Acceptance Criteria:**
- Sentinel indexes Career OS commands (install/test/startup) from `backend/pyproject.toml`
- Default smoke runs the pytest suite, launches uvicorn, waits, crash-scans cleanly
- Tester asserts `GET /` returns `{"status": "ok"}` and `GET /health` returns `{"status": "healthy"}`
- Each major API group (knowledge-items, evidence, import, build, search, export, validate) has at least one live assertion
- Targeted Sentinel tests green; screenshots non-blank

**Definition of Done:** Sentinel discovers, launches, and asserts Career OS end-to-end without manual steps.

**Dependencies:** All previous sprints.

---

## Sprint Summary Table

| Sprint | Phase | Objective | Est. Time |
|--------|-------|-----------|-----------|
| 1 | Foundation | Project scaffolding | 30 min |
| 2 | Foundation | Database + schema | 60 min |
| 3 | Foundation | Core repositories | 90 min |
| 4 | Foundation | API CRUD layer | 120 min |
| 5 | Foundation | Backend tests | 120 min |
| 6 | Frontend | Frontend scaffolding | 90 min |
| 7 | Frontend | API client + contexts | 90 min |
| 8 | Import | DOCX parser | 90 min |
| 9 | Import | PDF + TXT parsers | 60 min |
| 10 | Import | Extraction service | 120 min |
| 11 | Import | Import Service + API | 120 min |
| 12 | Import | Import UI | 90 min |
| 13 | Resume | Template engine | 120 min |
| 14 | Resume | Builder service + API | 90 min |
| 15 | Resume | Builder UI | 150 min |
| 16 | SOQ | Builder service | 90 min |
| 17 | SOQ | Question analyzer | 60 min |
| 18 | SOQ | Builder UI | 120 min |
| 19 | Duty | Statement parser | 60 min |
| 20 | Duty | Builder service | 90 min |
| 21 | Duty | Builder UI | 120 min |
| 22 | Explorer | Search API | 90 min |
| 23 | Explorer | Explorer UI | 150 min |
| 24 | Explorer | Provenance panel | 120 min |
| 25 | Matching | TF-IDF service | 120 min |
| 26 | Matching | Historical weighting | 90 min |
| 27 | Export | Export service | 120 min |
| 28 | Export | Export UI integration | 120 min |
| 29 | Validate | Validation engine | 120 min |
| 30 | LLM | Local LLM integration | 120 min |
| 31 | Integration | E2E tests | 120 min |
| 32 | Release | MVP packaging | 150 min |
| 33 | Integration | Sentinel integration testers | 90 min |
| | | **Total: 33 sprints** | **~58 hours** |

---

## Notes for AI Agents

- **Sprint order is flexible** for parallelizable work. Sprints 13-21 (Resume/SOQ/Duty builders) can be partially parallelized since they share infrastructure.
- **Matching Engine (Sprints 25-26)** can be implemented as a stub earlier (returning simple keyword matches) and replaced with TF-IDF in Sprint 25.
- **Sprint 30 (LLM)** is entirely optional and feature-flagged. All other features work without it.
- **Each sprint's acceptance criteria must pass** before marking the sprint done. Do not skip tests.
- **Never modify code outside the current sprint's file list** unless it is a critical dependency fix (document in AGENTS.md).

