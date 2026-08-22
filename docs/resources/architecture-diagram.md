# Career OS — Architecture Diagram (ASCII)

```
┌─────────────────────────────────────────────────────────────────┐
│                     USER — Electron Desktop Shell               │
│   ┌───────────────────────────────────────────────┐             │
│   │  React 18 + TypeScript + Vite (renderer)      │             │
│   │  Dashboard · Import · Resume · SOQ · Duty     │             │
│   │  Explorer (search/filters/stars/provenance)   │             │
│   └───────────────────┬───────────────────────────┘             │
└────────────────────────┼────────────────────────────────────────┘
                         │ HTTP/REST  http://127.0.0.1:8000/api/v1
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Backend — FastAPI (uvicorn :8000)             │
│                                                                 │
│  API layer: knowledge · evidence · applications · import ·      │
│             build · search · match · export · validate          │
│                          │                                      │
│  Services: ExtractionService · TemplateEngine · ResumeBuilder  │
│            SOQBuilder(+Analyzer) · DutyStatementBuilder         │
│            MatchingService(TF-IDF + HistoricalWeighting)        │
│            ValidationService · ExportService                    │
│                          │                                      │
│  Repositories: KnowledgeItem · Evidence · Application · Doc     │
└──────────┬──────────────────────────────────────────┬───────────┘
           ▼                                          ▼
┌────────────────────────────┐          ┌──────────────────────────┐
│  SQLite knowledge base     │          │  Original documents      │
│  15 tables + FTS5 index    │          │  resumes/ · soqs/        │
│  tfidf_vectors cache       │          │  (gitignored, local)     │
└────────────────────────────┘          └──────────────────────────┘

Pipeline:
  Import ──▶ Parsers ──▶ Extraction ──▶ Knowledge Items + Evidence
                                              │
              ┌───────────────────────────────┤
              ▼                               ▼
      Matching Engine                 Builders (Resume/SOQ/Duty)
   (TF-IDF cosine × history)                   │
              └───────────────┬───────────────┘
                              ▼
                  Validation ──▶ Export (DOCX / TXT)
```

Packaging: `frontend/dist` (Vite bundle, relative asset paths) +
`frontend/electron/main.cjs` are packed by electron-builder into an NSIS
installer; the renderer talks to the local FastAPI server over HTTP.
