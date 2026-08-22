# Career OS — Changelog

Deterministic career knowledge platform. All dates 2026-08-22.

## v0.1.0 — MVP

### Phase 0 — Backend Foundation
- **Sprint 1**: FastAPI scaffolding, health endpoints, CORS, editable install
- **Sprint 2**: SQLite schema via SQLModel (15 tables), FTS5 full-text index + sync triggers
- **Sprint 3**: Repository layer (knowledge items / evidence / applications) with FTS5 search and historical success-rate math
- **Sprint 4**: `/api/v1/` CRUD for knowledge-items, evidence, applications; structured errors (201/204/400/404)
- **Sprint 5**: Shared pytest fixtures/factories, model tests, 80% coverage gate (98% achieved)

### Phase 1 — Frontend Foundation
- **Sprint 6**: Electron + Vite + React 18 + TS strict scaffolding (Tauri swapped for Electron pre-build)
- **Sprint 7**: Axios API client with error interceptor; KnowledgeBase/Builder/UI contexts; debounced search hook

### Phase 2 — Import Pipeline
- **Sprint 8–9**: DOCX/PDF/TXT parsers (bullets via numbering XML/styles/text markers; headings; soft-break splitting) + parser factory
- **Sprint 10**: Rule-based extraction service: classification, resume-bullet grouping, SOQ pairing, skills/metrics/keywords/categories
- **Sprint 11**: Import service & API (multipart upload, job registry); live-tested against real PDF resumes
- **Sprint 12**: Drag-drop import UI with progress tracking

### Phase 3–5 — Builders
- **Sprint 13**: JSON template engine (evidence grouping, traceability maps)
- **Sprint 14–15**: Resume builder service/API/UI (suggestions, editor, drag-drop section organizer)
- **Sprint 16–18**: SOQ builder service/analyzer/UI (word-budget enforcement, live category detection); fixed real-world docx quirks
- **Sprint 19–21**: Duty statement parser/builder/UI (numbered/bulleted/prose parsing, per-duty evidence matching, paste-to-parse flow)

### Phase 6–7 — Explorer & Matching Engine
- **Sprint 22–24**: Search/match APIs, Evidence Explorer UI (filters, star ratings, provenance panel)
- **Sprint 25–26**: Pure-Python TF-IDF with SQLite-cached vectors + historical success weighting; replaced inverted BM25 normalization as primary ranker

### Phase 8–9 — Export & Validation
- **Sprint 27–28**: DOCX/TXT export with embedded Word-comment traceability; streaming downloads wired into all builders
- **Sprint 29**: Validation engine (completeness, keyword coverage, traceability, length) blocking invalid exports

### Phase 11 — Integration & Release
- **Sprint 31**: End-to-end API pipeline tests; batch import of the full personal corpus (169 knowledge items) with real-world extraction fixes
- **Sprint 32**: Electron packaging (electron-builder NSIS), dev/build/release scripts, HashRouter production routing
- **Deferred**: Sprint 30 (optional local LLM polish), Sprint 33 (Sentinel integration testers)
