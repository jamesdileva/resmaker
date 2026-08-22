# AGENTS.md — Career OS Project Rules

> **Version:** 1.0
> **Purpose:** Operating contract for AI coding agents working on Career OS

Read `docs/01_Master_Architecture.md` fully before starting any work. These rules are derived from the Project Rules section (Section 3) of the Master Architecture.

---

## Core Rules

1. **Evidence is the source of truth.** Every factual claim in any output must be traceable to a stored Knowledge Item linked to original evidence.
2. **The application never invents experience.** No output may contain information not present in the knowledge base.
3. **All outputs must be traceable to evidence.** Each generated document includes inline provenance or a traceability report.
4. **Assembly is deterministic.** Given the same knowledge base state and inputs, the same output is produced.
5. **AI is optional and cannot create new facts.** LLMs may only refine language (grammar, transitions, keyword suggestions). They cannot add, remove, or alter factual content.
6. **Every feature must be testable independently.** No feature is deployed without unit or integration tests.
7. **Business logic belongs in backend services.** The frontend is a thin presentation layer. All logic lives in Python services.
8. **One responsibility per module.** Each module, service, and component does exactly one thing.
9. **Keep all user data local by default.** No data leaves the device unless the user explicitly opts into a sync feature.
10. **Prefer composition over duplication.** Knowledge items are linked, not copied.

---

## Sprint Execution Workflow

1. Read the sprint's section in `docs/03_Sprint_Plan.md` (including Inputs/Outputs)
2. Read the relevant section(s) of `docs/02_Implementation_Guide.md`
3. Review the sprint's Inputs and Outputs before starting
4. Create/modify ONLY the files listed in the sprint
5. Write or update tests
6. Run the full test suite for your component
7. Verify ALL acceptance criteria manually
8. Update the documentation changelog with what was accomplished

---

## Agent Development Guidelines

- **Never refactor unrelated code during a sprint.** If you see something that could be improved, note it and continue with the current sprint's scope.
- **Complete only the current sprint's scope.** Do not add "just one more feature."
- **Do not add future features early.** The YAGNI (You Aren't Gonna Need It) principle applies.
- **Keep changes localized to the relevant modules.** If you need to touch a file not listed in the sprint, ask.
- **Ensure all acceptance criteria pass before moving to the next sprint.** No exceptions.
- **Preserve deterministic behavior** unless explicitly changing it in the current sprint.
- **Test first.** Write the test, watch it fail, implement the code, watch it pass.
- **Run linting and type checking** before considering a sprint done.

---

## Prohibited Actions

- Adding dependencies not specified in the technology stack (`docs/01_Master_Architecture.md` Section 8)
- Refactoring code outside the current sprint's scope
- Bypassing the Validation Engine
- Making LLM-generated content factual (no fact-creation prompts)
- Storing or transmitting user data to external services
- Using "TODO" or "FIXME" comments as a substitute for implementation

---

## Testing Requirements

- Every sprint must have tests written or updated
- Backend: pytest with >= 80% coverage for new code
- Frontend: Vitest with >= 75% coverage for new components
- E2E tests: At least one end-to-end test per major feature
- All tests must pass before a sprint is marked "Done"

---

## Code Style

### Backend (Python)
- PEP 8 with 4-space indentation
- Type hints required (pydantic models, function signatures)
- Docstrings for all classes and public methods
- `pytest` for testing, `pytest-cov` for coverage
- `ruff` for linting (if available)

### Frontend (TypeScript + React)
- Prettier formatting (2-space indent, single quotes)
- ESLint with React rules
- TypeScript strict mode
- `shadcn/ui` components as base
- Vitest for testing

---

## File Naming Conventions

- Backend Python modules: `snake_case.py`
- Backend classes: `PascalCase`
- Backend API routers: prefixed with version (`v1/`)
- Frontend components: `PascalCase.tsx`
- Frontend hooks: `useCamelCase.ts`
- Frontend types: `PascalCase.ts` or `PascalCase.tsx`
- Database tables: `snake_case`
- Tests: `test_*.py` or `*.test.tsx`

---

## Documentation Update Protocol

When a sprint changes the architecture or API:
1. Update `docs/02_Implementation_Guide.md` if the change affects technical specs
2. Update `docs/01_Master_Architecture.md` if the change affects architecture decisions
3. Add a changelog entry to the relevant sprint in `docs/03_Sprint_Plan.md`
4. Update `AGENTS.md` if the change affects project rules

---

## Changelog

| Sprint | Date | Accomplished |
|--------|------|--------------|
| Sprint 1 — Project Scaffolding | 2026-08-21 | Created `backend/pyproject.toml` (canonical deps, `career-os-serve` script, pytest config), `backend/app/main.py` (FastAPI app, `GET /`, `GET /health`, CORS for Vite dev origins, structured exception handler), `.python-version` (3.11), health-check tests (`backend/tests/test_main.py`), generated `backend/requirements.txt` lock. All acceptance criteria verified: editable install, pytest 2/2 passed, uvicorn boots, both endpoints + Swagger UI return 200. Sprint 33 (Sentinel integration testers) added to sprint plan, deferred to end per `integration.md`. |
| Sprint 2 — Database Setup & Schema | 2026-08-21 | Created `backend/app/db/` (`connection.py`: cached engine factory, `CAREER_OS_DB_PATH` env override, FK pragma enforcement, `get_session()` dependency; `models.py`: 15 SQLModel tables incl. junction tables and JSON metadata column; `__init__.py`: FTS5 virtual table + insert/delete/update sync triggers + indexes via `apply_schema_extras`). DB init wired into FastAPI lifespan in `main.py`. Added `.gitignore`, tests (`tests/test_db.py`, startup test in `tests/test_main.py`) and `scripts/verify_sprint2.py`. All acceptance criteria verified: pytest 10/10 passed; init_db creates file, 15 tables + `knowledge_items_fts`, 3 triggers, 5 indexes; FTS stays in sync on insert/delete; foreign keys enforced. |
| Sprint 3 — Core Repositories | 2026-08-21 | Created `backend/app/repositories/` (`base.py`: generic session-managed CRUD base class; `knowledge_item.py`: create/get/get_multi with type+category filters/search via FTS5 BM25 normalized to 0-1/update/delete/bulk_create/get_with_evidence + `MatchResult` model; `evidence.py`: create/get with linked items/get_multi/link_to_item upsert/get_success_rate + `EvidenceWithItems` wrapper; `application.py`: create/get/update_result/record_evidence_usage upsert/get_success_weight = 0.1*interview_rate + 0.2*offer_rate). Tests: `tests/test_repositories.py` (18 tests). Verified: pytest 28/28 passed, coverage 98% total / >=95% per repo module; non-existent IDs return None/False gracefully; FTS5 search ranks and filters by min_score. |
| Sprint 4 — API CRUD Layer | 2026-08-22 | Created `backend/app/api/v1/` (`knowledge.py`: list `{items,total}` with filters/search/CRUD; `evidence.py`: list/get-with-items/create/link upsert with 404 checks on both IDs; `applications.py`: list/get/create (validates job posting FK)/result update with status Literal). Routers mounted under `/api/v1` in `main.py`; `RequestValidationError` handler returns structured 400 per sprint spec. Conventions: 201 on create, 204 on delete, payload models inline per router. Added filtered `count()` to `KnowledgeItemRepository` and tests (`tests/test_api.py`, 13 tests incl. OpenAPI contract check). Verified: pytest 41/41 passed, coverage 98%; live uvicorn check — list 200, create 201, validation 400, missing 404, Swagger UI 200. |
| Sprint 5 — Backend Tests | 2026-08-22 | Created `tests/__init__.py` and shared `tests/conftest.py` (`session`/`client` fixtures on fresh temp DBs, `job_posting` FK fixture, `make_knowledge_item`/`make_evidence` factories, `seeded_knowledge_items` helper); deduplicated fixtures from `test_repositories.py`/`test_api.py`; created `tests/test_models.py` (10 tests: UUID/timestamp/JSON defaults, metadata round-trip, unique constraints on skills/keywords/categories, composite uniqueness on junction tables, FK enforcement). Added `[tool.coverage]` config with `fail_under = 80`. Verified: pytest 51/51 passed; coverage 98.43% (>= 80% gate enforced); repo tests cover create/get/update/delete/search; API tests cover 200/400/404 for all endpoints. |
| Sprint 6 — Frontend Scaffolding | 2026-08-22 | **Architecture decision: Tauri → Electron** (no Rust toolchain required; proven Sentinel CDP testing path per `integration.md`; user-approved). All three docs updated: Master Architecture §8 stack tables, §9 folder structure, §11 shell description, export/config/security notes; Implementation Guide §10.4; Sprint Plan sprints 6/28/32. Created `frontend/`: Vite + React 18 + TS strict (`package.json`, `tsconfig.json`, `vite.config.ts`, `index.html`), app shell (`main.tsx`, `app.tsx`, `routes/index.tsx`, `components/layout.tsx`, `pages/Dashboard.tsx`), shared types (`src/types/index.ts`) mirroring backend schemas, Electron main process (`electron/main.cjs`, contextIsolation/sandbox on). Root `package.json` with npm workspace. Verified: npm install OK, `tsc --noEmit` clean, `npm run dev` serves 200 on 5173, `npm run electron:dev` (concurrently + wait-on) opens 'Career OS' BrowserWindow. Note: Vite pinned to host 127.0.0.1 for wait-on IPv4 compat. |
| Sprint 7 — API Client & Contexts | 2026-08-22 | Created `frontend/src/api/` (`client.ts`: axios instance, base URL via `VITE_API_BASE_URL` env override, response interceptor mapping errors to structured messages incl. timeout/404/status; `knowledge.ts`: list/get/search typed calls; `evidence.ts`: list/get-with-items). Created contexts per Implementation Guide §5.1: `KnowledgeBaseContext` (items/evidence/loading/error + search/getItem/refresh), `BuilderContext` (currentBuilder/selectedItems add-remove-clear), `UIContext` (theme/sidebar/toast with auto-dismiss); providers wrapped in `app.tsx`. Hooks: `useKnowledgeItems` (filters + loading/error/refetch), `useSearch` (debounced 300ms, stale-response guard). Added vitest + jsdom + testing-library; 16 tests across client/hooks/contexts. Verified: tsc clean, vitest 16/16, live end-to-end — electron window mounted and fetched knowledge-items + evidence with 200s from uvicorn. Notes: React Query deferred until server-state complexity warrants it; `buildAndExport` lands with builder sprints (14/28); routes stay Dashboard-only until page sprints. |
| Sprint 8 — DOCX Parser | 2026-08-22 | Created `backend/app/parsers/` (`base.py`: `BaseParser` ABC + `ParsedDocument`/`Paragraph` pydantic models per Implementation Guide §8.1; `docx_parser.py`: `DocxParser` using python-docx). Bullet detection: paragraph-level `numPr` XML (with `ilvl` nesting, malformed values tolerated) → `List Bullet N` style suffix → left-indent fallback (~0.25in per level); headings via style-name prefix + trailing digit. Created `scripts/make_fixtures.py` (reproducible) and committed binary fixtures `tests/fixtures/sample_resume.docx` (2 jobs, 6 bullets incl. nested level 2) + `sample_soq.docx` (2 Q&A pairs). Tests: `test_parsers.py` (12 tests incl. numbering-XML, indent fallback, missing file). Verified: pytest 63/63 passed, coverage 98% total / 98% parsers; manual parse dump confirms heading/bullet structure matches fixture layout. |
| Sprint 9 — PDF and TXT Parsers | 2026-08-22 | Created `backend/app/parsers/pdf_parser.py` (pymupdf block extraction in document order, wrapped lines merged per block, all Normal style per guide §8.3; uses modern `import pymupdf`) and `txt_parser.py` (line-by-line, blank lines skipped). Added `get_parser()` factory in `parsers/__init__.py` (case-insensitive, strips leading dot, `ValueError` on unknown type). Extended `scripts/make_fixtures.py`: `sample_posting.pdf` (via `insert_textbox` so text wraps within margins — plain `insert_text` clipped at page edge) + `sample_duty.txt`. Tests: 11 new (`test_parsers.py`, 23 total incl. factory dispatch/case-insensitivity/unknown-type). Verified: pytest 74/74 passed, coverage 98% total / parsers >=95%. |
