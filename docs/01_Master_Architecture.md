# Career OS — Master Architecture

> **Version:** 1.0
> **Status:** Draft — Sprint 0 (Pre-MVP)
> **Audience:** Developers, AI coding agents, project maintainers

This is the single source of truth for what Career OS is and how it is structured. Every future document — implementation guides, sprint plans, API references — derives from and references this document. Read this first.

---

## Table of Contents

1. Vision
   - 1.1 Career Pipeline (diagram)
2. Design Philosophy
3. Project Rules
4. Goals
5. Non-Goals
6. MVP Definition
7. High-Level Architecture
   - 7.1 Knowledge Graph (Data Model)
8. Technology Stack
9. Folder Structure
10. Backend Architecture
11. Frontend Architecture
12. Database Architecture
13. Evidence Engine
14. Matching Engine
   - 14.5 Template Engine
15. Resume Builder
16. SOQ Builder
17. Duty Statement Generator
   - 17.5 Document Lifecycle
18. Import Pipeline
19. Export Pipeline
20. Validation Engine
21. Local LLM Integration
22. Configuration
23. Logging
24. Security
25. Performance
26. Future Architecture
   - 26.5 Responsibility Matrix
27. Agent Development Guidelines
28. Changelog

Appendix A: API Reference
Appendix B: Future Roadmap

## 1. Vision

> **North Star:** Career OS is a deterministic career knowledge platform that transforms verified evidence into tailored application documents through explainable, reusable workflows.

Career OS is a **deterministic, local-first career knowledge system**.

Most AI resume builders ask: "What should I write?"

Career OS asks: "What have I already proven?"

Instead of generating documents from scratch, Career OS treats every piece of career evidence — a resume bullet, an SOQ paragraph, an interview answer, a STAR story, a project, a skill, a metric — as a **Knowledge Item** in a personal knowledge graph. This knowledge base becomes the single source of truth for all career artifacts.

When a new job application arrives, the system does not write. It **searches**.

The Matching Engine finds the most relevant existing evidence, scores it by relevance and historical success (interviews, offers), and the Builders assemble deterministic outputs — resumes, SOQs, duty statements, cover letters — from these proven pieces. An optional local LLM may polish transitions and grammar, but it never invents facts.

The result is a system that gets smarter with each application: every successful submission becomes weighted evidence for future decisions.

### Career Pipeline

`
User's Career Documents (resumes, SOQs on disk)
        |
        v
Importers (File upload / Drag-drop)
        |
        v
Parsers (DOCX / PDF / TXT)
   Extract text, bullets, headings
        |
        v
Knowledge Extraction (Content Classifier)
   Classify paragraphs to Knowledge Items + Evidence
        |
        v
Knowledge Base (SQLite + FTS5)
   knowledge_items | evidence | skills | metrics
        |
        +---> Matching Engine (TF-IDF + Historical Weighting)
        |          |
        |          v
        |       Builders (Resume, SOQ, Duty Statement)
        |          |
        |          v
        +---> Validation Engine (Completeness, Keywords, Traceability)
        |          |
        |          v
        |       Export Pipeline (DOCX / PDF / TXT)
        |          |
        +---> Evidence Explorer (Search, Star Ratings, Provenance)
`

---

## 2. Design Philosophy

| Principle | Description |
|-----------|-------------|
| **Deterministic-first** | Outputs are assembled from known evidence, not generated from scratch. Given the same knowledge base and inputs, the same output is produced every time. |
| **Evidence-backed** | Every output must trace back to verified career evidence. No hallucinations, no invented experience. |
| **Local-first** | All user data lives on the user's device. No mandatory cloud sync, no third-party servers. |
| **Composable** | Knowledge items are reusable across all output types. A bullet on a resume may also appear in an SOQ, an interview answer, or a LinkedIn post. |
| **Optional AI** | LLMs are used exclusively for polish (grammar, transitions, keyword expansion). They cannot create new facts or invent experience. |
| **Search over generate** | The primary workflow is searching existing knowledge, not generating new content. |
| **Traceable** | Every piece of output can be traced back to its source evidence, with provenance metadata preserved. |

---

## 3. Project Rules

These are the "constitution" of Career OS. They must be upheld in every decision.

1. **Evidence is the source of truth.** Every factual claim in any output must be traceable to a stored Knowledge Item linked to original evidence.
2. **The application never invents experience.** No output may contain information not present in the knowledge base.
3. **All outputs must be traceable to evidence.** Each generated document includes inline provenance or a traceability report.
4. **Assembly is deterministic.** Given the same knowledge base state and inputs, the same output is produced.
5. **AI is optional and cannot create new facts.** LLMs may only refine language (grammar, transitions, keyword suggestions). They cannot add, remove, or alter factual content.
6. **Every feature must be testable independently.** No feature is deployed without unit or integration tests.
7. **Business logic belongs in backend services.** The frontend is a thin presentation layer. All logic lives in Python services.
8. **One responsibility per module.** Each module, service, and component does exactly one thing.
9. **Keep all user data local by default.** No data leaves the device unless the user explicitly opts into a sync feature (future).
10. **Prefer composition over duplication.** Knowledge items are linked, not copied. Changes to an item propagate to all outputs that reference it.

---
## 4. Goals

### Must-Have (MVP)

- Import existing career documents (DOCX, PDF, TXT) and extract reusable Knowledge Items
- Store all knowledge in a local SQLite database with full-text search
- Build a searchable Evidence Explorer with VS Code-like search and star ratings
- Assemble resumes from knowledge items using templates
- Assemble SOQ responses from knowledge items with evidence suggestions
- Generate duty statement responses that draw parallels between job postings and existing evidence
- Match job postings to existing knowledge with confidence scores
- Weight evidence by historical application success (interview received, rejected, offer)
- Export documents in DOCX, PDF, and TXT formats
- Validate outputs against completeness and keyword coverage rules
- Optional local LLM for grammar and transition polishing only
- Ship as a desktop application (Electron) with a local web server backend

### Should-Have (Post-MVP)

- Cover letter builder
- Interview answer builder (STAR story generator)
- LinkedIn post generator
- Multi-document batch assembly
- Template marketplace / import

### Could-Have (Future)

- Cloud sync (opt-in)
- Multi-user / team mode
- Web-based deployment
- Advanced LLM assistance (still fact-bound)
- API for external integrations

---

## 5. Non-Goals

- **Not a web service.** Career OS runs entirely on the user's device. No hosted deployment in MVP.
- **No real-time collaboration.** This is a personal tool, not a team platform.
- **No AI fact creation.** The LLM layer may only polish language, never create content.
- **No automatic job application submission.** The system generates documents; the user submits.
- **No data analytics dashboard.** Analytics (application tracking, success rates) is secondary to the core builder workflow.
- **No mobile app.** Desktop-first. Mobile is future work.

---

## 6. MVP Definition

The MVP is the minimal set of features that demonstrates the core value proposition: **import career evidence, search it, and assemble documents from it deterministically.**

### In Scope

| Component | Status |
|-----------|--------|
| SQLite knowledge base | Core |
| Import pipeline (DOCX + PDF) | Core |
| Knowledge item extraction | Core |
| Evidence Explorer (search + star ratings + provenance) | Core |
| Resume Builder (template + TXT/DOCX export) | Core |
| SOQ Builder (template + evidence suggestions + DOCX export) | Core |
| Duty Statement Generator (job posting to evidence-matched response) | Core |
| Matching Engine (TF-IDF + cosine similarity + historical weighting) | Core |
| Export Pipeline (DOCX, PDF, TXT) | Core |
| Validation Engine (completeness, keyword coverage) | Core |
| Local LLM Integration (grammar, transitions only) | Optional (feature-flagged) |
| Electron desktop packaging | Core |

### Out of Scope (MVP)

- Cover letter builder
- Interview answer builder
- STAR story generator
- LinkedIn post generator
- Cloud sync
- Web deployment
- Multi-user support

### Success Criteria

The MVP is complete when a user can:

1. Import 3-5 existing SOQs and 2-3 resumes from disk
2. See extracted knowledge items in the Evidence Explorer
3. Search for a keyword (e.g., "confidential") and see matching bullets, SOQ paragraphs, and experience records
4. Create a new resume by selecting evidence from the knowledge base
5. Answer a new SOQ question by reusing existing evidence with 80%+ similarity match
6. Generate a duty statement response for a new job posting by matching against existing experience
7. Export any document to DOCX and open it in Microsoft Word
8. Optionally, polish grammar/transition with a local LLM

---
## 7. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER (Desktop App)                       │
│                    ┌─────────────────────────────────┐         │
│                    │        Frontend (React/Electron)   │         │
│                    │  Dashboard, Explorer, Builders  │         │
│                    └────────────┬────────────────────┘         │
└─────────────────────────────────┼──────────────────────────────┘
                                  │ HTTP / REST API
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Backend (Python/FastAPI)                  │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │  Import      │  │  Builders    │  │  Matching    │           │
│  │  Pipeline    │  │  (Resume,    │  │  Engine      │           │
│  │              │  │  SOQ, Duty)  │  │              │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
│        │                 │                 │                    │
│        ▼                 ▼                 ▼                    │
│  ┌────────────────────────────────────────────────────────┐     │
│  │              Knowledge Base (SQLite)                   │     │
│  │  knowledge_items | evidence | skills | metrics         │     │
│  │  resume_bullets  | soq_*    | projects | experience    │     │
│  │  applications    | keywords | categories              │     │
│  └────────────────────────────────────────────────────────┘     │
│        │                                                        │
│        ▼                                                        │
│  ┌────────────────────────────────────────────────────────┐     │
│  │              Validation Engine                        │     │
│  │  completeness rules | keyword coverage | length limits │     │
│  └────────────────────────────────────────────────────────┘     │
│        │                                                        │
│        ▼                                                        │
│  ┌────────────────────────────────────────────────────────┐     │
│  │              Export Pipeline                           │     │
│  │  DOCX | PDF | TXT                                     │     │
│  └────────────────────────────────────────────────────────┘     │
│        │                                                        │
│        ▼                                                        │
│  ┌────────────────────────────────────────────────────────┐     │
│  │              Original Documents (filesystem)           │     │
│  │  *.docx | *.pdf | *.txt                                 │     │
│  └────────────────────────────────────────────────────────┘     │
└──────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│              Optional: Local LLM Service (Ollama)              │
│  Keywords expansion, grammar polish, transition suggestions     │
│  NEVER creates facts — only refines language                   │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow Summary

1. **Import**: User uploads a document → Parser extracts text → Extractor creates Knowledge Items, links evidence → Stored in SQLite
2. **Search**: User queries the Evidence Explorer → Matching Engine searches SQLite FTS5 → Results ranked by score + historical success → Star ratings displayed
3. **Build**: User selects job posting / SOQ question → Matching Engine finds best evidence → Builder assembles document deterministically → Validation Engine checks completeness → Export Pipeline renders format

### Knowledge Graph (Data Model)

Career OS is fundamentally a graph. The Experience (a job position, project, or education) is the root node that connects to all related evidence:

```
Experience / Project / Education
      │
      ├── Evidence (the core record)
      │     │
      │     ├── Resume Bullets (knowledge_items)
      │     ├── SOQ Paragraphs (knowledge_items)
      │     ├── Interview Answers (knowledge_items)
      │     ├── STAR Stories (knowledge_items)
      │     │
      │     ├── Skills (linked via knowledge_item_skills)
      │     ├── Metrics (quantitative achievements)
      │     ├── Keywords (indexed for search)
      │     └── Categories (topic classifications)
      │
      ├── Source Document (original file on disk)
      └── Applications (which job applications used this evidence)
              │
              ├── Application Result (interview / rejected / offer)
              └── Historical Success Weight
                      │
                      └── Boosts match scores in Matching Engine
```

---

## 8. Technology Stack

### Backend

| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.11+ | Runtime |
| FastAPI | 0.110+ | Web framework, API endpoints |
| SQLModel | 0.0.14+ | SQLite ORM with pydantic integration |
| python-docx | 1.1+ | DOCX parsing and generation |
| pymupdf (fitz) | 1.24+ | PDF text extraction |
| pydantic | 2.5+ | Data validation and serialization |
| pytest | 8.0+ | Backend testing |
| uvicorn | 0.29+ | ASGI server |

### Frontend

| Technology | Version | Purpose |
|------------|---------|---------|
| React | 18+ | UI library |
| TypeScript | 5.3+ | Type safety |
| Vite | 5.0+ | Build tool |
| React Router | 6.14+ | Client-side routing |
| Axios | 1.6+ | HTTP client |
| shadcn/ui | 0.6+ | Component library |
| React Query | 5.0+ | Server state management |
| Vitest | 1.2+ | Frontend testing |
| Electron | 30+ | Desktop shell and packaging |

### Infrastructure

| Technology | Purpose |
|------------|---------|
| SQLite | Local database (embedded) |
| electron-builder | Distributable packaging |
| Node.js | Build tooling and Electron host runtime |
| Ollama | Local LLM service (optional, feature-flagged) |

### Why This Stack

- **Python + FastAPI**: The document processing ecosystem (python-docx, pymupdf) is unmatched in Python. FastAPI's type safety and async support make it ideal for the service layer. SQLModel bridges pydantic and SQLAlchemy cleanly.
- **React + TypeScript**: Industry standard for desktop app UIs (via Electron). TypeScript catches errors early in the builder workflows.
- **Electron**: Mature desktop packaging with a bundled Chromium runtime and a proven automated-testing path (CDP). Larger distributables than Rust-based wrappers, but no native toolchain requirement.
- **SQLite**: Single-file, zero-config, fast enough for a personal knowledge base. FTS5 handles full-text search natively.
- **Ollama**: Runs LLMs locally with a clean HTTP API. Perfect for the optional AI layer.

---
## 9. Folder Structure

```
ResMaker/
├── docs/
│   ├── 01_Master_Architecture.md    ← This file
│   ├── 02_Implementation_Guide.md
│   ├── 03_Sprint_Plan.md
│   └── resources/                    # Diagrams, templates, assets
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                   # FastAPI app entry point
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── v1/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── knowledge.py      # Knowledge item CRUD
│   │   │   │   ├── import_.py        # Import endpoints
│   │   │   │   ├── build.py          # Builder endpoints
│   │   │   │   ├── search.py         # Evidence Explorer endpoints
│   │   │   │   ├── match.py          # Matching engine endpoints
│   │   │   │   └── export.py         # Export endpoints
│   │   ├── core/
│   │   │   ├── config.py             # Settings, env vars
│   │   │   ├── logging.py            # Logger setup
│   │   │   ├── security.py           # (future: encryption at rest)
│   │   │   └── exceptions.py         # Custom exceptions
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   ├── connection.py         # SQLite connection
│   │   │   ├── models.py             # SQLModel table definitions
│   │   │   └── migration.py          # (optional) migration runner
│   │   ├── schemas/                  # Pydantic schemas (domain models)
│   │   │   ├── knowledge.py
│   │   │   ├── evidence.py
│   │   │   ├── resume.py
│   │   │   └── soq.py
│   │   ├── repositories/             # Data access layer
│   │   │   ├── base.py
│   │   │   ├── knowledge_item.py
│   │   │   ├── evidence.py
│   │   │   └── application.py
│   │   ├── services/                 # Business logic layer
│   │   │   ├── import_service.py
│   │   │   ├── extraction_service.py
│   │   │   ├── matching_service.py
│   │   │   ├── resume_builder.py
│   │   │   ├── soq_builder.py
│   │   │   ├── duty_statement_builder.py
│   │   │   ├── export_service.py
│   │   │   ├── validation_service.py
│   │   │   └── llm_service.py
│   │   ├── parsers/                  # Document parsers
│   │   │   ├── __init__.py
│   │   │   ├── docx_parser.py
│   │   │   ├── pdf_parser.py
│   │   │   ├── txt_parser.py
│   │   │   └── base.py
│   │   └── tests/                    # Backend unit + integration tests
│   │       ├── conftest.py
│   │       ├── test_repositories.py
│   │       ├── test_services.py
│   │       ├── test_parsers.py
│   │       └── test_builders.py
│   ├── tests/                        # Integration tests
│   │   ├── conftest.py
│   │   └── test_e2e.py
│   ├── scripts/
│   │   ├── run.sh                    # Start backend server
│   │   └── migrate.sh
│   ├── pyproject.toml
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── main.tsx                  # React entry point (Electron renderer)
│   │   ├── app.tsx                   # Root component
│   │   ├── api/                      # Axios client + typed hooks
│   │   │   ├── client.ts
│   │   │   ├── knowledge.ts
│   │   │   ├── build.ts
│   │   │   └── search.ts
│   │   ├── components/
│   │   │   ├── KnowledgeItemCard.tsx
│   │   │   ├── StarRating.tsx
│   │   │   ├── EvidenceBadge.tsx
│   │   │   ├── MatchResult.tsx
│   │   │   ├── TemplateEditor.tsx
│   │   │   └── DocumentPreview.tsx
│   │   ├── contexts/
│   │   │   ├── KnowledgeBaseContext.tsx
│   │   │   ├── BuilderContext.tsx
│   │   │   └── UIContext.tsx
│   │   ├── hooks/
│   │   │   ├── useKnowledgeItems.ts
│   │   │   ├── useSearch.ts
│   │   │   ├── useBuilder.ts
│   │   │   └── useImport.ts
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx
│   │   │   ├── KnowledgeExplorer.tsx
│   │   │   ├── ResumeBuilder.tsx
│   │   │   ├── SOQBuilder.tsx
│   │   │   ├── DutyStatementBuilder.tsx
│   │   │   └── Settings.tsx
│   │   ├── routes/
│   │   │   └── index.tsx
│   │   ├── styles/
│   │   └── lib/
│   │       └── utils.ts
│   ├── public/
│   ├── electron/main.cjs
│   ├── vite.config.ts
│   ├── package.json
│   └── tsconfig.json
├── scripts/
│   ├── dev.py                         # Run both backend + frontend in dev mode
│   ├── build.py                       # Build all artifacts
│   └── release.py                     # Package Electron release
├── AGENTS.md                          # Project rules for AI agents
├── .python-version
├── pyproject.toml                     # Root pyproject (workspace)
└── README.md
```

---

## 10. Backend Architecture

### Purpose

The backend is the brain of Career OS. It handles all business logic, data persistence, document parsing, matching, building, export, and validation. The frontend is a thin presentation layer that communicates exclusively via HTTP/REST.

### Responsibilities

- Expose REST API endpoints (FastAPI) for all operations
- Manage SQLite connection and database access
- Parse uploaded documents (DOCX, PDF, TXT) and extract structured knowledge
- Implement the Matching Engine (TF-IDF, cosine similarity, historical weighting)
- Implement Builders (Resume, SOQ, Duty Statement) that assemble deterministic outputs
- Implement the Export Pipeline (DOCX, PDF, TXT generation)
- Implement the Validation Engine (completeness, keyword coverage, length limits)
- Optionally integrate with a local LLM service (Ollama) for grammar polish
- Handle configuration, logging, and error handling

### Layer Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         API Layer                               │
│  FastAPI Routers (v1: knowledge, import_, build, search,       │
│  match, export) — thin controllers, delegate to services         │
├─────────────────────────────────────────────────────────────────┤
│                      Service Layer                              │
│  ImportService, ExtractionService, MatchingService,             │
│  ResumeBuilderService, SOQBuilderService, DutyStatementService, │
│  ExportService, ValidationService, LLMService                   │
├─────────────────────────────────────────────────────────────────┤
│                    Repository Layer                             │
│  KnowledgeItemRepository, EvidenceRepository,                   │
│  ResumeBulletRepository, SOQParagraphRepository,                │
│  ApplicationRepository, ApplicationEvidenceRepository           │
├─────────────────────────────────────────────────────────────────┤
│                      Database Layer                             │
│  SQLite via SQLModel — tables, FTS5 indexes, relationships      │
└─────────────────────────────────────────────────────────────────┘
```

### Internal Components

| Component | Module Path | Description |
|-----------|-------------|-------------|
| FastAPI App | `app/main.py` | Application factory, middleware, dependency injection |
| API Routers | `app/api/v1/` | REST endpoints grouped by resource |
| Core Config | `app/core/config.py` | Pydantic settings, environment variables |
| Core Exceptions | `app/core/exceptions.py` | Custom exception hierarchy |
| Database | `app/db/` | Connection management, SQLModel models, migrations |
| Schemas | `app/schemas/` | Pydantic models for API request/response |
| Repositories | `app/repositories/` | CRUD operations, query building |
| Services | `app/services/` | Business logic, orchestration |
| Parsers | `app/parsers/` | DOCX, PDF, TXT text extraction |

### Future Expansion

- Background job queue (Celery/RQ) for heavy import/extraction tasks
- WebSocket endpoints for real-time import progress
- gRPC internal API between services for performance
- GraphQL endpoint for flexible queries

### Notes

- The backend starts as a single FastAPI app. Services are plain Python classes (not separate processes) for simplicity.
- The API runs on `http://localhost:8000` in development. In production, the Electron main process hosts the built frontend and targets the local API.
- All business logic must live in services. API routers should only handle request/response mapping and dependency injection.

---
## 11. Frontend Architecture

### Purpose

The frontend is a thin, reactive presentation layer that runs inside an Electron desktop shell. It communicates with the backend via HTTP REST API and invokes Electron IPC for filesystem access (file dialogs, saving exported documents).

### Responsibilities

- Dashboard: Overview of knowledge base statistics
- Evidence Explorer: Search and browse all knowledge items
- Resume Builder: Assemble, preview, and export resumes
- SOQ Builder: Answer SOQ questions using evidence suggestions
- Duty Statement Builder: Match job postings to existing evidence
- Settings: Configure LLM service, export defaults, import paths

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    State Management                            │
│  React Context: KnowledgeBaseContext, BuilderContext,          │
│  UIContext — shared state for knowledge access, builder state, │
│  and UI preferences                                             │
├─────────────────────────────────────────────────────────────────┤
│                    API Client Layer                             │
│  Axios-based client with typed request/response, React Query   │
│  for caching and background sync                                │
├─────────────────────────────────────────────────────────────────┤
│                    Component Layer                              │
│  Reusable components (shadcn/ui), page components, hooks      │
├─────────────────────────────────────────────────────────────────┤
│                    Routing Layer                                │
│  React Router v6 — declarative client-side routing               │
└─────────────────────────────────────────────────────────────────┘
```

### Internal Components

| Component | Module Path | Description |
|-----------|-------------|-------------|
| App Root | `src/app.tsx` | Root component, providers, router outlet |
| API Client | `src/api/client.ts` | Axios instance with interceptors |
| API Hooks | `src/api/` | Typed query/mutation hooks per resource |
| Contexts | `src/contexts/` | KnowledgeBaseContext, BuilderContext, UIContext |
| Custom Hooks | `src/hooks/` | useKnowledgeItems, useSearch, useBuilder, useImport |
| Pages | `src/pages/` | Dashboard, KnowledgeExplorer, ResumeBuilder, etc. |
| Components | `src/components/` | Reusable UI and domain-specific components |
| Utils | `src/lib/utils.ts` | Utility functions |

### Future Expansion

- Internationalization (i18n) support for multi-language resumes
- Theme selector (dark/light/material)
- Keyboard shortcuts for Evidence Explorer (VS Code-like)
- Plugin system for additional builder types

### Notes

- The frontend uses React Query to manage server state. No Redux or Zustand needed.
- Electron IPC is used only for file system operations (open/save dialogs, saving exports). All other data flows through the REST API.
- Components are built with shadcn/ui for consistency. Domain-specific components extend the base.

---

## 12. Database Architecture

### Purpose

The database is the heart of the knowledge base. It stores all Knowledge Items, their categories, keywords, evidence links, and application history. SQLite is used as an embedded, single-file database — no server required.

### Schema Overview

```
knowledge_items (parent table for all item types)
├── ResumeBullet (discriminator: "resume_bullet")
├── SOQParagraph (discriminator: "soq_paragraph")
├── InterviewAnswer (discriminator: "interview_answer")
├── STARStory (discriminator: "star_story")
├── Project (discriminator: "project")
└── Metric (discriminator: "metric")

Evidence (links to original source documents)
Skills (extracted from knowledge items)
Metrics (quantitative achievements)
Experience (job positions)
JobPostings (external job data)
Applications (user applications with success tracking)
ApplicationEvidence (many-to-many: applications × knowledge items — tracks which items were used and whether they resulted in an interview)
Keywords (indexed for search)
Categories (topic classifications)
```

### Key Tables

#### knowledge_items
Stores all knowledge items as rows with a `type` discriminator column. Common fields shared across all item types.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID (PK) | Unique identifier |
| type | TEXT | "resume_bullet", "soq_paragraph", etc. |
| title | TEXT | Short title/label |
| content | TEXT | The actual text content |
| category | TEXT | Topic classification (e.g., "Confidential Information") |
| source_doc_id | TEXT (FK) | Link to source document |
| created_at | TIMESTAMP | |
| updated_at | TIMESTAMP | |
| metadata | JSON | Type-specific fields |

#### evidence
| Column | Type | Description |
|--------|------|-------------|
| id | UUID (PK) | |
| title | TEXT | Evidence title (e.g., "Boost Mobile") |
| type | TEXT | "experience", "project", "education" |
| content | TEXT | Full evidence text |
| start_date | TEXT | |
| end_date | TEXT | |
| source_doc_id | TEXT (FK) | |
| created_at | TIMESTAMP | |
| updated_at | TIMESTAMP | |

#### knowledge_item_evidence (junction table)
| Column | Type | Description |
|--------|------|-------------|
| knowledge_item_id | TEXT (FK) | |
| evidence_id | TEXT (FK) | |
| strength | INTEGER | 1-5 or "high"/"medium"/"low" |

#### applications
| Column | Type | Description |
|--------|------|-------------|
| id | UUID (PK) | |
| job_posting_id | TEXT (FK) | |
| applied_at | TIMESTAMP | |
| status | TEXT | "applied", "interview", "offer", "rejected" |
| interview_received | BOOLEAN | |
| offer_received | BOOLEAN | |

#### application_evidence (historical success tracking)
| Column | Type | Description |
|--------|------|-------------|
| application_id | TEXT (FK) | |
| knowledge_item_id | TEXT (FK) | |
| used_in_resume | BOOLEAN | |
| used_in_soq | BOOLEAN | |
| used_in_duty | BOOLEAN | |
| result | TEXT | "interview", "offer", "rejected" |

#### Full-Text Search
SQLite FTS5 is used to create a virtual table indexing all knowledge item content and keywords. This enables fast, ranked search across the entire knowledge base.

### Future Expansion

- PostgreSQL backend for multi-user deployments
- Vector embeddings (pgvector) for semantic search
- Automated backup and sync (opt-in)
- Encrypted storage at rest

### Notes

- All foreign keys enforce referential integrity.
- The `metadata` JSON column on `knowledge_items` stores type-specific fields without requiring separate tables, keeping the schema flexible during early development.
- FTS5 triggers keep the search index in sync with the base table.

---
## 13. Evidence Engine

### Purpose

The Evidence Engine is the subsystem responsible for managing, linking, and surfacing career evidence. It provides the foundation that all Builders and the Matching Engine rely on. Every claim in every output must trace back to evidence managed by this engine.

### Responsibilities

- Store and index evidence (experience, projects, education, metrics)
- Create and maintain links between Knowledge Items and Evidence
- Assign star ratings to evidence based on strength and historical performance
- Provide evidence provenance queries (which resumes/SOQs/applications used this evidence)
- Maintain the evidence-to-knowledge-item graph in SQLite

### Inputs

- Imported documents (via Import Pipeline)
- Manually created evidence (future)
- Historical application results (interview/offer/rejected)

### Outputs

- Evidence records with metadata and star ratings
- Evidence provenance traces (usage history across outputs and applications)
- Searchable evidence index

### Internal Components

| Component | Description |
|-----------|-------------|
| EvidenceRepository | CRUD for evidence records and evidence-knowledge-item links |
| EvidenceScoringService | Calculates star ratings based on strength and historical success |
| ProvenanceService | Tracks and queries which outputs used which evidence |
| EvidenceIndexer | Manages FTS5 index for evidence search |

### Future Expansion

- Automated evidence strength scoring (NLP-based confidence)
- Evidence versioning (track changes over time)
- Evidence conflict detection (flag contradictory claims)

### Notes

- Evidence is never duplicated — knowledge items reference evidence by ID.
- Star ratings are recalculated when application history is updated.

---

## 14. Matching Engine

### Purpose

The Matching Engine is the search and recommendation engine that connects job requirements to existing evidence. It powers the Evidence Explorer, the Builders, and the duty statement generator.

### Responsibilities

- TF-IDF vectorization of all knowledge item content and keywords
- Cosine similarity ranking between query and knowledge items
- Historical success weighting (boosts items that led to interviews/offers)
- Confidence score calculation and threshold filtering
- Keyword expansion (synonyms, stemming) to improve match coverage

### Inputs

- Search query or job posting text
- Knowledge base (SQLite with FTS5)
- Application history (for historical weighting)

### Outputs

- Ranked list of matching Knowledge Items with scores
- Confidence percentage match
- Star rating (1-5) based on relevance + historical performance

### Internal Components

| Component | Description |
|-----------|-------------|
| TfidfVectorizer | Builds TF-IDF matrix from knowledge base content |
| SimilarityCalculator | Computes cosine similarity between query and items |
| HistoricalWeightingService | Adjusts scores based on past application success |
| KeywordExpander | Expands query terms with synonyms and stems |
| MatchResultAssembler | Packages results with scores, provenance, and evidence links |

### Future Expansion

- Embedding-based semantic search (sentence-transformers)
- Cross-language matching for international jobs
- Query intent classification (classify the type of requirement: "analytical", "communication", etc.)

### Notes

- The TF-IDF matrix is rebuilt incrementally when new knowledge items are added.
- Historical weighting uses a simple formula: `final_score = similarity_score * (1 + interview_weight + offer_weight)` where weights are configurable constants (e.g., interview_weight = 0.1, offer_weight = 0.2).
- A minimum score threshold (default 0.3) filters out irrelevant matches.

---

## 15. Resume Builder

### Purpose

The Resume Builder assembles a resume document from knowledge items in the knowledge base. It uses deterministic template-based assembly — given the same knowledge base state and selections, it produces the same output.

### Responsibilities

- Provide resume templates (JSON-based layout definitions)
- Assemble resume sections from selected knowledge items
- Apply formatting rules (bullet style, order, section headers)
- Validate resume completeness (contact info, experience, skills)
- Export to TXT, DOCX formats

### Inputs

- Job posting (optional, for targeted resume)
- User-selected knowledge items (or auto-selected by Matching Engine)
- Resume template
- User preferences (layout, sections, ordering)

### Outputs

- Resume document (TXT, DOCX)
- Traceability report (which knowledge items were used)

### Internal Components

| Component | Description |
|-----------|-------------|
| ResumeTemplateEngine | Loads and applies JSON templates |
| ResumeAssemblyService | Selects and orders knowledge items into sections |
| ResumeFormattingService | Applies formatting rules (bullets, spacing, headers) |
| ResumeExportService | Generates DOCX/TXT output |
| ResumeValidationService | Checks completeness and format compliance |

### Future Expansion

- Visual resume builder UI (drag-drop section reordering)
- ATS-optimized templates (ATS-friendly formatting)
- Resume versioning (track changes over multiple applications)
- One-click multi-format export (PDF + DOCX + plain text)

### Notes

- Templates are JSON files that define section structure, required fields, and formatting rules. This keeps the assembly deterministic and testable.
- The builder never invents content. If a section has no matching evidence, it is omitted (with a warning from the Validation Engine).

---

## 16. SOQ Builder

### Purpose

The SOQ (Statement of Qualifications) Builder answers SOQ questions by finding and assembling relevant evidence from the knowledge base. It provides evidence suggestions ranked by the Matching Engine and allows the user to review and edit before final assembly.

### Responsibilities

- Parse SOQ questions and categorize them (e.g., "analytical experience", "confidential information")
- Search the knowledge base for matching evidence using the Matching Engine
- Present ranked suggestions with confidence scores and star ratings
- Assemble a structured SOQ response from selected evidence
- Validate SOQ completeness (question coverage, keyword presence, length)

### Inputs

- SOQ question text
- Knowledge base (searched via Matching Engine)
- Selected evidence items
- SOQ template

### Outputs

- SOQ response document (DOCX, TXT)
- Evidence traceability report

### Internal Components

| Component | Description |
|-----------|-------------|
| SOQQuestionAnalyzer | Categorizes and extracts keywords from SOQ questions |
| EvidenceSuggestionService | Queries Matching Engine for relevant evidence |
| SOQAssemblyService | Assembles evidence into structured SOQ response |
| SOQExportService | Generates DOCX/TXT output |
| SOQValidationService | Validates completeness and keyword coverage |

### Future Expansion

- Bulk SOQ processing (answer multiple questions at once)
- SOQ response templates per agency/role type
- Automated SOQ length optimization (stay within page limits)

### Notes

- The builder suggests existing SOQ paragraphs from the knowledge base (imported from previous successful submissions) as starting points.
- The user must review and confirm all assembled content before export. No fully-automatic SOQ generation.


---

## 17. Duty Statement Generator

### Purpose

The Duty Statement Generator matches a job posting's duty statement against the user's existing work experience and generates a duty statement response that draws clear parallels. This is particularly important for government job applications where applicants must describe their previous job duties in a way that aligns with the position they are applying for.

### Responsibilities

- Parse a job posting's duty statement to extract key responsibilities and required skills
- Search the knowledge base for matching evidence (experience, projects, skills)
- Generate duty statement paragraphs that mirror the job's language while using verified evidence
- Present evidence suggestions ranked by relevance and historical success
- Validate that all claims are backed by evidence

### Inputs

- Job posting duty statement text (the "target")
- Knowledge base (user's experience, projects, skills, resume bullets)
- Optional: existing duty statement responses (for reuse suggestions)

### Outputs

- Duty statement response document (DOCX, TXT)
- Evidence traceability report

### Internal Components

| Component | Description |
|-----------|-------------|
| DutyStatementParser | Parses job posting duty statements into structured requirements |
| DutyMatchingService | Matches job duties against knowledge base evidence using the Matching Engine |
| DutyResponseBuilder | Assembles duty statement paragraphs from matched evidence |
| DutyExportService | Generates DOCX/TXT output |
| DutyValidationService | Validates that all duties in the response are evidence-backed |

### Future Expansion

- Duty statement templates per agency
- Automated duty statement reuse (import past responses as knowledge items)
- Cross-duty-statement analysis (find gaps between target and existing evidence)

### Notes

- The generator does NOT write new experience. It mirrors the job posting's duty language using existing evidence, creating parallel descriptions of past work.
- Each generated paragraph includes a hidden traceability marker linking to source evidence.
- The user reviews and edits before export.

---

## 14.5. Template Engine

### Purpose

Templates define the structure, formatting, and content layout for all generated documents. They are JSON-based, versionable, and composable. The Template Engine renders structured Knowledge Items into formatted document sections.

### Responsibilities

- Load and validate template definitions (JSON)
- Map knowledge item types to sections
- Apply formatting rules (font, spacing, bullet style)
- Group items by evidence (e.g., bullets under a job)
- Support template versioning and inheritance

### Inputs

- Template definition (JSON file)
- Selected Knowledge Items
- Evidence records (for grouping/metadata)
- User profile (for personal info)
- Builder-specific options (e.g., max_words for SOQ)

### Outputs

- Rendered document structure (sections with formatted content)
- Traceability mapping (item_id to evidence_id)

### Template Types

| Type | Purpose | Example |
|------|---------|---------|
| Resume | Full resume layout | "standard", "ats-friendly", "executive" |
| SOQ | SOQ response structure | "standard" |
| Duty Statement | Duty statement response | "standard" |
| Cover Letter | Future: cover letter layout | "professional", "creative" |

### Versioning

Templates are versioned via a version field in the JSON. Template Engine validates compatibility.

### Future Expansion

- Visual template editor (drag-drop section builder)
- Template marketplace (import/share templates)
- Per-job-posting template profiles

### Notes

- Templates are stored as JSON files in `backend/app/data/templates/`
- Default templates ship with the application
- Users can create custom templates without code changes

---

## 17.5. Document Lifecycle

Every document imported into Career OS passes through a defined lifecycle.

```
Imported (file on disk)
    |
    v
Parsed (text extracted by Parser)
    |
    v
Structured (classified into Knowledge Items + Evidence)
    |
    v
Validated (extraction confidence checked)
    |
    v
Indexed (FTS5 + TF-IDF vector)
    |
    v
Searchable (appears in Evidence Explorer results)
    |
    v
Referenced (linked into Resume / SOQ / Duty Statement)
    |
    v
Archived (source doc retained, items remain active)
```

### Lifecycle States

| State | Operations Available |
|-------|---------------------|
| Imported | Delete, Re-import |
| Parsed | (automatic) |
| Structured | Edit items, Link evidence |
| Validated | Override categories, Fix links |
| Indexed | Search, Build |
| Referenced | View traceability |
| Archived | All above + export history |

### Notes

- Documents can be re-parsed at any time with improved classifiers.
- Knowledge items persist even after source document is archived.

---
## 18. Import Pipeline

### Purpose

The Import Pipeline takes existing career documents (resumes, SOQs, duty statements) from the user's disk and converts them into structured Knowledge Items stored in the knowledge base. It is the primary mechanism for seeding the system with verified evidence.

### Responsibilities

- Accept file uploads (DOCX, PDF, TXT) via UI or file dialog
- Route files to the appropriate parser based on file type
- Extract text content from documents
- Analyze and categorize extracted content into Knowledge Item types
- Assign categories, keywords, and evidence links to each Knowledge Item
- Store all extracted items in SQLite with metadata (source document, confidence, etc.)
- Provide progress feedback to the user during import

### Inputs

- User-uploaded documents (DOCX, PDF, TXT)
- Source document metadata (filename, upload timestamp)

### Outputs

- Knowledge Items stored in SQLite
- Evidence records linked to source documents
- Import log (what was extracted, what was skipped)

### Internal Components

| Component | Description |
|-----------|-------------|
| ImportController | API endpoint handler, file routing |
| DocxParser | Extracts text from DOCX files using python-docx |
| PdfParser | Extracts text from PDF files using pymupdf |
| TxtParser | Reads plain text files |
| ContentClassifier | Categorizes extracted content into Knowledge Item types |
| CategoryExtractor | Assigns topic categories and keywords |
| EvidenceLinker | Links Knowledge Items to source documents and evidence records |

### Import Process Flow

1. User selects file(s) via file dialog or drag-drop
2. File is read and routed to the appropriate parser
3. Parser extracts raw text content
4. ContentClassifier splits text into paragraphs and classifies each as:
   - Resume bullet (numbered list under a job)
   - SOQ paragraph (under a question heading)
   - Experience record (job title + company + dates)
   - Skill (standalone keyword/phrase)
   - Metric (standalone number/percentage)
5. CategoryExtractor assigns categories (e.g., "Confidential Information", "Analysis") and keywords
6. EvidenceLinker creates Evidence records and links Knowledge Items to them
7. All items are stored in SQLite via repositories
8. Progress is reported to the frontend via HTTP streaming or polling

### Future Expansion

- Image OCR for scanned PDFs (pytesseract)
- Email import (parse SOQ responses from email threads)
- Cloud storage integration (Google Drive, OneDrive — opt-in)
- Resume parsing (parse structured resume fields: name, contact, experience sections)

### Notes

- The classifier uses rule-based heuristics (bullet patterns, indentation, headings) for the MVP. NLP-based classification is future work.
- Imported SOQ paragraphs are tagged with a success flag of "Unknown" until the user marks them.
- The import process is synchronous in the MVP. Large imports may be moved to background tasks in the future.

---

## 19. Export Pipeline

### Purpose

The Export Pipeline takes assembled content from any Builder (Resume, SOQ, Duty Statement) and renders it into the selected output format. It handles formatting, page layout, and file saving.

### Responsibilities

- Accept structured content from Builders
- Apply format-specific templates and formatting rules
- Render output in DOCX, PDF, or TXT
- Save the output file to disk (via Electron save dialog) or return as download

### Inputs

- Structured content from a Builder (sections, paragraphs, bullets with metadata)
- Format specification (DOCX, PDF, TXT)
- Optional: custom template

### Outputs

- Exported file on disk
- Traceability report (embedded or companion file)

### Internal Components

| Component | Description |
|-----------|-------------|
| ExportController | Orchestrates export, routes to format-specific exporter |
| DocxExporter | Generates DOCX using python-docx with formatting |
| PdfExporter | Generates PDF (via reportlab or wkhtmltopdf) |
| TxtExporter | Generates plain text with minimal formatting |
| FormatValidator | Validates output against format requirements |
| FileSaver | Electron save dialog to write file to disk |

### Future Expansion

- HTML/CSS export for styled output
- Markdown export for version control
- ZIP export for multi-file packages (resume + SOQ + duty statement)

### Notes

- DOCX export includes hidden traceability metadata (custom XML) linking content to evidence.
- PDF export is lower priority in MVP. TXT is the fallback for quick previews.

---

## 20. Validation Engine

### Purpose

The Validation Engine checks that all generated outputs meet completeness and quality standards before export. It ensures no section is empty, all keywords from the job posting are covered, and all claims are evidence-backed.

### Responsibilities

- Check document completeness (required sections present, not empty)
- Verify keyword coverage (job posting keywords present in output)
- Validate evidence traceability (all claims linked to evidence)
- Check length constraints (resume 1-2 pages, SOQ specific word/paragraph limits)
- Report warnings and errors to the user

### Inputs

- Assembled document content with metadata
- Job posting keywords (for coverage check)
- Validation rules configuration

### Outputs

- Validation report (pass/fail, warnings, errors, suggestions)
- Highlighted issues in the document preview

### Internal Components

| Component | Description |
|-----------|-------------|
| CompletenessValidator | Checks required sections and content presence |
| KeywordCoverageValidator | Verifies job posting keywords are addressed |
| EvidenceTraceabilityValidator | Ensures all claims link to evidence |
| LengthValidator | Checks page/word/paragraph limits |
| ValidationRuleRegistry | Manages validation rules and configuration |

### Future Expansion

- Custom validation rule builder (user-defined rules)
- Automated fix suggestions (suggest evidence to fill gaps)
- ATS compatibility scoring (estimate ATS pass rate)

### Notes

- Validation runs automatically before export. The user can override warnings but not errors.
- Rules are configurable per document type and per job posting.

---
## 21. Local LLM Integration

### Purpose

The Local LLM Integration provides optional AI assistance for grammar polishing, transition improvement, and keyword expansion. It is feature-flagged and never creates new facts. All LLM-suggested changes require user review and approval before being applied.

### Responsibilities

- Connect to a local LLM service (Ollama or llama.cpp)
- Provide grammar correction suggestions (non-factual edits only)
- Provide transition improvement suggestions (smoothing between paragraphs)
- Provide keyword expansion (suggest synonyms for better matching)
- Ensure all LLM interactions are logged and auditable
- Enforce the "never create facts" rule via system prompts

### Inputs

- Text content (from any Builder or Knowledge Item)
- Mode flag: "grammar", "transitions", "keywords"
- Context: job posting keywords (for keyword expansion)

### Outputs

- LLM suggestions (grammar fixes, improved transitions, expanded keywords)
- User must accept/reject each suggestion

### Internal Components

| Component | Description |
|-----------|-------------|
| LLMClient | HTTP client to Ollama/llama.cpp API |
| GrammarService | Requests grammar corrections, filters for non-factual edits |
| TransitionService | Requests transition improvements |
| KeywordExpansionService | Requests keyword suggestions from job posting context |
| LLMSuggestionManager | Manages suggestion lifecycle (request → filter → present → apply) |
| LLMAuditLogger | Logs all LLM interactions for traceability |

### LLM Prompts

The system prompt enforces:
- "You are a grammar and style assistant. You may only suggest changes to spelling, grammar, punctuation, sentence structure, and transitions. You must never add, remove, or alter factual information."
- "If asked to create new content or facts, refuse."

### Future Expansion

- Local embedding model for vector search
- LLM-powered keyword categorization (assign categories to imported knowledge items)
- LLM-powered question classification (classify SOQ questions automatically)
- Fine-tuned model on user's own successful applications

### Notes

- The LLM service is disabled by default. The user must explicitly enable it and configure the Ollama endpoint.
- No LLM interaction happens without explicit user action (clicking "Polish with AI").
- All LLM suggestions are presented as diffs. The original content is never modified until the user approves.

---

## 22. Configuration

### Purpose

Configuration manages all user preferences, system settings, and feature flags.

### Responsibilities

- Store user preferences (LLM endpoint, default export format, templates)
- Manage feature flags (LLM integration on/off)
- Store job posting data for active applications
- Manage import/export paths

### Configuration Sources

| Source | Priority | Description |
|--------|----------|-------------|
| Environment variables | Highest | For deployment-specific settings |
| Config file (`config.toml` or `.env`) | Medium | User-edited settings |
| UI Settings page | Lowest | Overrides config file at runtime |

### Key Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `llm.enabled` | `false` | Enable/disable local LLM integration |
| `llm.endpoint` | `http://localhost:11434` | Ollama API endpoint |
| `export.default_format` | `docx` | Default export format |
| `matching.min_score` | `0.3` | Minimum match score for suggestions |
| `matching.interview_weight` | `0.1` | Weight added per interview |
| `matching.offer_weight` | `0.2` | Weight added per offer |
| `import.auto_categorize` | `true` | Auto-assign categories on import |
| `validation.strict_mode` | `false` | Block export on warnings |

### Future Expansion

- Per-job-posting configuration profiles
- Template marketplace (downloadable templates)
- Keyboard shortcut customization

### Notes

- Configuration is stored in the user's app data directory (the Electron main process resolves it via app.getPath('userData')).
- Environment variables override all other settings for CI/CD and testing.

---

## 23. Logging

### Purpose

Logging provides observability into system operations, errors, and LLM interactions.

### Responsibilities

- Log all API requests and responses (sanitized)
- Log import/extraction operations
- Log matching engine queries and results
- Log LLM interactions (prompts and responses) for audit
- Log validation results
- Support multiple log levels (DEBUG, INFO, WARNING, ERROR)

### Log Format

All logs use structured JSON format for easy parsing:

```json
{"timestamp": "2026-08-01T10:30:00Z", "level": "INFO", "module": "import_service", "message": "Imported 15 knowledge items from resume.docx", "details": {"file": "resume.docx", "items_created": 15}}
```

### Log Storage

- Development: stdout (console)
- Production: File on disk (`logs/career_os.log`), rotated daily
- LLM audit logs: Separate file (`logs/llm_audit.log`)

### Future Expansion

- Log forwarding to external observability tools
- Metrics collection (export to Prometheus)

### Notes

- User data in logs is sanitized (no full content, only references and IDs).
- LLM audit logs are immutable and retained for compliance.

---

## 24. Security

### Purpose

Security ensures that user data is protected at rest and in transit.

### Responsibilities

- Keep all user data local (no cloud sync by default)
- Secure the SQLite database file with file system permissions
- Sanitize all inputs to prevent injection attacks
- Validate and sanitize file uploads (size limits, type checking)
- Ensure LLM interactions do not leak sensitive data

### Data Protection

- SQLite database is stored in the user's app data directory with OS-level permissions
- No data is sent to external services (even LLM suggestions run locally)
- File uploads are validated: max 50MB per file, allowed extensions: .docx, .pdf, .txt

### Future Expansion

- Encryption at rest for the SQLite database
- Encrypted export files
- Secure credential storage for cloud services (if sync is added)

### Notes

- The backend starts with localhost binding only (`127.0.0.1:8000`). No remote access by default.
- The Electron main process enforces contextIsolation, disables nodeIntegration in renderers, and blocks navigation away from the local origins.

---
## 25. Performance

### Purpose

Performance ensures the system feels fast and responsive, even with a large knowledge base.

### Responsibilities

- Optimize database queries (indexes, FTS5, query planning)
- Cache TF-IDF vectors to avoid recomputation
- Lazy-load large documents in the Evidence Explorer
- Provide progress feedback for long-running operations (import, export)
- Keep UI responsive during background operations

### Expected Performance Targets (MVP)

| Operation | Target | Conditions |
|-----------|--------|------------|
| Search 1000 knowledge items | < 500ms | 1000 items, 800KB text total |
| Resume assembly | < 2s | 20 bullets, 5 sections |
| SOQ generation | < 1s | 5 evidence items, 1 question |
| Docx import (10 pages) | < 3s | Single DOCX, ~20 knowledge items |
| Docx export | < 1s | 2-page resume |

### Optimization Strategies

- SQLite FTS5 for full-text search (avoids full table scans)
- TF-IDF vectors cached and incrementally updated (not recomputed on every search)
- Backend uses FastAPI's async for I/O-bound operations (file reads, export)
- Frontend uses React Query for smart caching and background refetching
- Import and export operations run with progress callbacks

### Future Expansion

- Background job queue for heavy operations
- Web Workers for frontend computation (TF-IDF in browser)
- Vectorized similarity search (FAISS or pgvector)

### Notes

- The MVP targets a knowledge base of up to 1000 items. Performance is not critical at this scale.
- TF-IDF computation is the heaviest operation. It is cached and only recomputed when the knowledge base changes.

---

## 26. Future Architecture

### Post-MVP Vision

1. **Phase 1 — Core Completion**: Template marketplace, cover letter builder, interview Q&A builder, STAR story generator
2. **Phase 2 — Intelligence**: Semantic search with embeddings, automated question categorization, NLP-based content classification
3. **Phase 3 — Sync & Share**: Opt-in cloud sync, multi-device support, team/collaborative mode
4. **Phase 4 — Ecosystem**: API for external integrations, plugin system, web-based deployment option

### Architectural Evolution

- **Services**: Backend services may be split into separate processes or containers as the system grows
- **Database**: Migration path from SQLite to PostgreSQL (with pgvector for embeddings) is designed in from the start (SQLModel abstraction)
- **Frontend**: Component library is modular, supporting a future web deployment
- **AI**: LLM integration is designed as a pluggable service, supporting multiple backends (Ollama, llama.cpp, cloud APIs if opted in)

### Long-Term Data Flow

```
┌─────────────────────────────────────────────────────────┐
│  External Sources: Job postings, email notifications    │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│  Ingestion Layer: Import Pipeline, Job Board Scrapers  │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│  Knowledge Base: SQLite / PostgreSQL with FTS5 + Vectors│
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│  Intelligence Layer: Matching Engine, ML Classifiers   │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│  Output Layer: Builders, Generators, Export Pipeline   │
└─────────────────────────────────────────────────────────┘
```

---

## 26.5. Responsibility Matrix

This matrix defines ownership boundaries between components. A boundary violation (e.g., Builders touching the database) is a code smell.

| Module | Owns | Does NOT Own |
|--------|------|-------------|
| **Import Pipeline** | Reading documents, routing to parsers, saving source docs | Knowledge item creation logic, extraction classification |
| **Extraction Service** | Creating Knowledge Items and Evidence from parsed text | File I/O, parsing raw documents, database writes |
| **Knowledge Base** | Persistent storage and indexing of Knowledge Items, Evidence, metrics | Document parsing, content assembly, matching logic |
| **Matching Engine** | Ranking evidence, computing scores, keyword expansion | Writing to the knowledge base, document generation |
| **Builders** (Resume/SOQ/Duty) | Assembling documents from selected evidence | Parsing documents, writing to DB, computing similarity |
| **Validation Engine** | Checking completeness, keyword coverage, traceability | Generating document content, writing to DB |
| **Export Pipeline** | Rendering documents to DOCX/PDF/TXT | Searching knowledge, assembling content |
| **Evidence Explorer** | Search UI, displaying provenance and star ratings | Generating documents, writing to DB |
| **LLM Service** | Grammar/polish suggestions only | Creating or modifying factual content |

---

## 27. Agent Development Guidelines

These guidelines are an operating contract for any AI coding agent working on Career OS. They prevent architectural drift and ensure deterministic behavior is preserved.

### Core Operating Principles

1. **Read the docs first.** Always read `docs/01_Master_Architecture.md` and the relevant section of `docs/02_Implementation_Guide.md` before writing any code.
2. **Complete only the current sprint's scope.** Do not add features, refactor, or "improve" code outside the current sprint's acceptance criteria.
3. **Preserve deterministic behavior.** If a component is specified as deterministic in the architecture, do not change that behavior without explicit instruction.
4. **Never invent facts.** In the codebase, this means: if a feature needs data, create the data pipeline that produces it from evidence. Never hardcode or fabricate career content.
5. **Business logic in backend services.** Never put business logic in the frontend or in API route handlers. Services are the single source of logic.
6. **One responsibility per module.** If a module is doing two things, split it.
7. **Test before merging.** Every feature must have tests. Acceptance criteria must pass.
8. **Keep changes localized.** Modify only the files listed in the current sprint. Touching unrelated files is a red flag.
9. **Follow the architecture patterns.** Use the same patterns, conventions, and abstractions as existing code.
10. **Ask before going off-script.** If the sprint plan doesn't cover a question, ask the user before proceeding.

### Sprint Execution Workflow

1. Read the sprint's section in `docs/03_Sprint_Plan.md` (including Inputs/Outputs)
2. Check the Implementation Guide for relevant technical details
3. Review the sprint's Inputs and Outputs before starting
4. Create/modify only the files listed in the sprint
5. Write or update tests
6. Run the full test suite
7. Verify acceptance criteria
8. Update the changelog

### Code Style

- Backend: PEP 8, type hints with pydantic/pyright, pytest for tests
- Frontend: Prettier formatting, ESLint, TypeScript strict mode, Vitest for tests
- Documentation: Update `docs/` when architecture changes

### Prohibited Actions

- Adding dependencies not specified in the technology stack
- Refactoring code outside the current sprint's scope
- Bypassing the Validation Engine
- Making LLM-generated content factual (no fact-creation prompts)
- Storing or transmitting user data to external services

---

## 28. Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-08-01 | Initial architecture document created |
| 1.1 | 2026-08-01 | Added Career Pipeline diagram, Knowledge Graph diagram, Document Lifecycle, Template Engine subsection, Responsibility Matrix, North Star statement (per GPT audit v1.0) |

---

## Appendix A: API Reference

### API v1 Endpoints

All endpoints are under `http://localhost:8000/api/v1/`.

### Knowledge Items

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/knowledge-items/` | List all knowledge items with pagination |
| GET | `/knowledge-items/{id}` | Get a specific knowledge item |
| POST | `/knowledge-items/` | Create a knowledge item |
| PUT | `/knowledge-items/{id}` | Update a knowledge item |
| DELETE | `/knowledge-items/{id}` | Delete a knowledge item |
| GET | `/knowledge-items/search?q={query}` | Search knowledge items (FTS5) |

### Evidence

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/evidence/` | List all evidence records |
| GET | `/evidence/{id}` | Get evidence with linked knowledge items |
| POST | `/evidence/` | Create an evidence record |

### Import

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/import/docx` | Import a DOCX file |
| POST | `/import/pdf` | Import a PDF file |
| POST | `/import/txt` | Import a TXT file |
| GET | `/import/status/{job_id}` | Check import progress |

### Builders

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/build/resume` | Assemble a resume from selected items |
| POST | `/build/soq` | Answer an SOQ question from evidence |
| POST | `/build/duty-statement` | Generate a duty statement response |
| POST | `/build/suggest` | Get evidence suggestions for a query |

### Search

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/search/` | Full evidence explorer search |
| POST | `/search/match` | Match a job posting to knowledge items |

### Export

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/export/resume` | Export resume (DOCX/PDF/TXT) |
| POST | `/export/soq` | Export SOQ response |
| POST | `/export/duty-statement` | Export duty statement response |

### Validation

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/validate/` | Validate an assembled document |

### LLM (Optional, feature-flagged)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/llm/grammar` | Get grammar suggestions |
| POST | `/llm/transitions` | Get transition suggestions |
| POST | `/llm/keywords` | Get keyword expansion suggestions |

### Applications

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/applications/` | List all applications |
| POST | `/applications/` | Record a new application |
| POST | `/applications/{id}/result` | Update application result (interview, offer, rejected) |
| GET | `/applications/{id}/evidence` | Get evidence used in an application |

---

## Appendix B: Future Roadmap

### Short Term (Post-MVP, Sprints 33-40)

- Cover letter builder
- Interview answer builder (STAR story generator)
- LinkedIn post generator
- Custom validation rule builder
- Template marketplace (import/export templates)
- Resume versioning and history

### Medium Term (Sprints 41-60)

- Semantic search with sentence embeddings (local model)
- NLP-based content classification on import
- Automated SOQ question categorization
- Bulk SOQ processing (answer multiple questions)
- Web-based deployment option (Flask/React build)
- Keyboard shortcuts for Evidence Explorer
- ATS compatibility scoring

### Long Term (Sprints 60+)

- Cloud sync (opt-in, end-to-end encrypted)
- Multi-user / team mode
- Plugin system for builders and exporters
- API for external integrations
- Mobile app (React Native or Flutter)
- Fine-tuned LLM on user's own successful applications
- Automated job application tracker (read-only)
- Integration with job boards (read-only application tracking)

---


