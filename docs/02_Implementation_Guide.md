# Career OS — Implementation Guide

> **Version:** 1.0
> **Status:** Draft — Sprint 0 (Pre-MVP)
> **Audience:** Developers, AI coding agents
> **Related:** See `docs/01_Master_Architecture.md` for architecture overview

This document is the **technical reference** for implementing Career OS. It provides concrete specifications — database schemas, API contracts, service interfaces, and component hierarchies — that map directly to code. Every sprint in `docs/03_Sprint_Plan.md` references sections from this guide.

---

## Table of Contents

1. Database Schema
2. API Endpoints
3. Repositories
4. Services
5. Frontend State Management
6. Pages
7. Components
8. Import Parsers
9. Template Engine
10. Export Engine
11. Validation Rules
12. Matching Algorithm
13. Evidence Scoring
14. Keyword Expansion
15. LLM Service
16. Testing Strategy
---

## 1. Database Schema

All tables use SQLite with SQLModel. Full DDL is specified in Sprint 2 of the Sprint Plan. Key tables: `knowledge_items`, `evidence`, `knowledge_item_evidence`, `source_documents`, `resume_bullets`, `soq_paragraphs`, `skills`, `metrics`, `job_postings`, `applications`, `application_evidence`, `keywords`, `categories`, `tfidf_vectors`.

### SQLModel Models (Python)

```python
class KnowledgeItem(SQLModel, table=True):
    id: str = Field(primary_key=True)  # UUID
    type: str  # "resume_bullet", "soq_paragraph", etc.
    title: str | None
    content: str
    category: str | None
    source_doc_id: str | None = Field(foreign_key="source_documents.id")
    confidence: float | None  # 0.0 - 1.0
    metadata_: dict = Field(default={}, sa_column_kwargs={"name": "metadata"})
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class Evidence(SQLModel, table=True):
    id: str = Field(primary_key=True)
    title: str
    type: str  # "experience", "project", "education"
    content: str
    start_date: str | None
    end_date: str | None
    company: str | None
    role: str | None
    source_doc_id: str | None

class Application(SQLModel, table=True):
    id: str = Field(primary_key=True)
    job_posting_id: str = Field(foreign_key="job_postings.id")
    status: str  # "applied", "interview", "offer", "rejected"
    applied_at: datetime = Field(default_factory=datetime.utcnow)
```
---

## 2. API Endpoints

All endpoints under `http://127.0.0.1:8000/api/v1/`.

### 2.1. Knowledge Items

**GET `/knowledge-items/`** — List with pagination
- Query: `skip=0&limit=50&type=soq_paragraph&category=Confidential`
- Returns: `{"items": [...], "total": 310}`

**GET `/knowledge-items/{id}`** — Get single item
- Returns full KnowledgeItem object

**POST `/knowledge-items/`** — Create item (used by import pipeline)
- Body: `{type, title, content, category, source_doc_id, metadata}`
- Returns: created KnowledgeItem

**POST `/knowledge-items/bulk/`** — Batch create
- Body: `[item1, item2, ...]`

**GET `/knowledge-items/search?q={query}&min_score=0.3`** — FTS5 search
- Returns: ranked results with scores

**PUT `/knowledge-items/{id}`** — Update

**DELETE `/knowledge-items/{id}`** — Delete

### 2.2. Evidence

**GET `/evidence/`** — List all evidence
**GET `/evidence/{id}`** — Get with linked knowledge items
**POST `/evidence/`** — Create evidence record
**POST `/evidence/link`** — Link knowledge item to evidence

### 2.3. Import

**POST `/import/`** — Upload and process document
- Multipart form: `file` (file), `file_type` (optional)
- Returns: `{"job_id": "IMP-001", "status": "processing"}`

**GET `/import/status/{job_id}`** — Check progress
- Returns: `{"status": "completed", "items_created": 15, "items_skipped": 2}`

### 2.4. Builders

**POST `/build/suggest`** — Get evidence suggestions for a query
- Body: `{query, item_types, min_score=0.3, top_k=10}`
- Returns: ranked suggestions with scores, star ratings, evidence links

**POST `/build/resume`** — Assemble resume from selected items
- Body: `{template, selected_item_ids, user_profile}`
- Returns: `{document_id, content, traceability}`

**POST `/build/soq`** — Answer an SOQ question
- Body: `{question, question_category, selected_item_ids, max_words}`
- Returns: `{document_id, content, traceability}`

**POST `/build/duty-statement`** — Generate duty statement response
- Body: `{job_posting_id, selected_item_ids, template}`
- Returns: `{document_id, content, traceability}`

### 2.5. Search

**POST `/search/`** — Full evidence explorer search
- Body: `{query, item_types, categories, min_star_rating, sort_by, limit}`
- Returns: full result set with provenance info

### 2.6. Export

**POST `/export/`** — Export assembled document
- Body: `{document_id, format: "docx"|pdf"|txt", include_traceability: true}`
- Returns: `{file_path, file_size}`

### 2.7. Validation

**POST `/validate/`** — Validate an assembled document
- Body: `{document_id, job_posting_keywords, rules}`
- Returns: `{valid, errors, warnings, score}`

### 2.8. Applications

**GET `/applications/`** — List all applications
**POST `/applications/`** — Create application record
**POST `/applications/{id}/result`** — Update with result + evidence usage

### 2.9. LLM (Optional)

**POST `/llm/grammar`** — Grammar suggestions
**POST `/llm/transitions`** — Transition improvements
**POST `/llm/keywords`** — Keyword expansion

---
## 3. Repositories

### 3.1. KnowledgeItemRepository

File: `backend/app/repositories/knowledge_item.py`

| Method | Signature | Description |
|--------|-----------|-------------|
| create | `(item: KnowledgeItemCreate) -> KnowledgeItem` | Insert |
| get | `(id: str) -> KnowledgeItem` | Fetch by ID |
| get_multi | `(skip, limit, type?, category?) -> list[KnowledgeItem]` | Paginated list |
| search | `(query: str, min_score: float) -> list[MatchResult]` | FTS5 search |
| update | `(id: str, data: dict) -> KnowledgeItem` | Update fields |
| delete | `(id: str) -> None` | Delete |
| get_with_evidence | `(id: str) -> KnowledgeItemWithEvidence` | Item + linked evidence |
| bulk_create | `(items: list[KnowledgeItemCreate]) -> list[KnowledgeItem]` | Batch insert |

### 3.2. EvidenceRepository

File: `backend/app/repositories/evidence.py`

| Method | Signature | Description |
|--------|-----------|-------------|
| create | `(evidence: EvidenceCreate) -> Evidence` | Create |
| get | `(id: str) -> EvidenceWithItems` | Get with linked items |
| get_multi | `(skip, limit) -> list[Evidence]` | Paginated list |
| link_to_item | `(evidence_id, item_id, strength) -> None` | Create link |
| get_success_rate | `(evidence_id: str) -> float` | Historical interview/offer rate |

### 3.3. ApplicationRepository

File: `backend/app/repositories/application.py`

| Method | Signature | Description |
|--------|-----------|-------------|
| create | `(app: ApplicationCreate) -> Application` | Create |
| get | `(id: str) -> Application` | Fetch by ID |
| update_result | `(id, status) -> Application` | Update status |
| record_evidence_usage | `(app_id, item_id, used_in_resume, used_in_soq, result) -> None` | Track usage |
| get_success_weight | `(item_id: str) -> float` | Historical weighting score |

---

## 4. Services

### 4.1. ImportService

File: `backend/app/services/import_service.py`

```python
class ImportService:
    def process_upload(self, file_path: str, file_type: str) -> ProcessingResult
    def process_text(self, text: str, source_doc_id: str, doc_type: str) -> list[KnowledgeItem]
```

Flow: Save doc → Parse text → Classify content → Extract metadata → Create items + evidence → Return summary.

### 4.2. ExtractionService

File: `backend/app/services/extraction_service.py`

```python
class ExtractionService:
    def classify_paragraph(self, text: str) -> ParagraphType
    def extract_resume_bullets(self, lines: list[str]) -> list[BulletData]
    def extract_soq_paragraphs(self, lines: list[str]) -> list[SOQData]
    def extract_skills(self, text: str) -> list[str]
    def extract_metrics(self, text: str) -> list[MetricData]
    def assign_category(self, content: str, ptype: ParagraphType) -> str
    def extract_keywords(self, content: str) -> list[str]
```

### 4.3. MatchingService

File: `backend/app/services/matching_service.py`

```python
class MatchingService:
    def match_query(self, query: str, types: list[str], 
                    min_score: float = 0.3, top_k: int = 10) -> list[MatchResult]
    def get_suggestions(self, query: str, types: list[str]) -> list[Suggestion]
```

Algorithm:
1. Vectorize query (TF-IDF + keyword expansion)
2. Cosine similarity vs all items
3. Apply historical success weighting
4. Filter, sort, return top-k with star ratings

### 4.4. ResumeBuilderService

File: `backend/app/services/resume_builder.py`

```python
class ResumeBuilderService:
    def build_resume(self, item_ids: list[str], user_profile: dict, template: str) -> BuiltDocument
    def auto_build_resume(self, job_posting_id: str, template: str) -> BuiltDocument
```

### 4.5. SOQBuilderService

File: `backend/app/services/soq_builder.py`

```python
class SOQBuilderService:
    def answer_question(self, question: str, item_ids: list[str]) -> BuiltDocument
    def suggest_items(self, question: str) -> list[Suggestion]
```

### 4.6. DutyStatementBuilderService

File: `backend/app/services/duty_statement_builder.py`

```python
class DutyStatementBuilderService:
    def generate_response(self, job_posting_id: str, item_ids: list[str]) -> BuiltDocument
    def parse_duty_statement(self, text: str) -> list[DutyRequirement]
```

### 4.7. ExportService

File: `backend/app/services/export_service.py`

```python
class ExportService:
    def export_to_docx(self, doc: BuiltDocument, include_traceability: bool) -> str
    def export_to_txt(self, doc: BuiltDocument) -> str
    def export_to_pdf(self, doc: BuiltDocument) -> str
```

### 4.8. ValidationService

File: `backend/app/services/validation_service.py`

```python
class ValidationService:
    def validate(self, doc: BuiltDocument, keywords: list[str]) -> ValidationResult
```

### 4.9. LLMService

File: `backend/app/services/llm_service.py`

```python
class LLMService:
    def grammar_suggestions(self, text: str) -> list[Suggestion]
    def transition_suggestions(self, text: str) -> list[Suggestion]
    def keyword_expansion(self, query: str) -> list[str]
```

### 4.10. TfidfService

File: `backend/app/services/tfidf_service.py`

```python
class TfidfService:
    def build_index(self, items: list[KnowledgeItem]) -> None
    def vectorize_query(self, query: str) -> SparseVector
    def similarity(self, item_id: str, query_vec: SparseVector) -> float
```

---
## 5. Frontend State Management

### 5.1. React Contexts

#### KnowledgeBaseContext
File: `frontend/src/contexts/KnowledgeBaseContext.tsx`

```typescript
interface KnowledgeBaseContextType {
  items: KnowledgeItem[];
  evidence: Evidence[];
  isLoading: boolean;
  search: (query: string) => Promise<SearchResult[]>;
  getItem: (id: string) => KnowledgeItem | undefined;
  refresh: () => Promise<void>;
}
```

#### BuilderContext
File: `frontend/src/contexts/BuilderContext.tsx`

```typescript
interface BuilderContextType {
  currentBuilder: 'resume' | 'soq' | 'duty';
  selectedItems: string[];
  addSelectedItem: (id: string) => void;
  removeSelectedItem: (id: string) => void;
  clearSelectedItems: () => void;
  buildAndExport: (format: 'docx' | 'pdf' | 'txt') => Promise<void>;
}
```

#### UIContext
File: `frontend/src/contexts/UIContext.tsx`

```typescript
interface UIContextType {
  theme: 'light' | 'dark';
  sidebarCollapsed: boolean;
  toast: (message: string, type: 'success' | 'warning' | 'error') => void;
}
```

### 5.2. Custom Hooks

| Hook | File | Description |
|------|------|-------------|
| `useKnowledgeItems` | `hooks/useKnowledgeItems.ts` | Fetch and manage knowledge items |
| `useSearch` | `hooks/useSearch.ts` | Search with filters, debounced |
| `useBuilder` | `hooks/useBuilder.ts` | Manage builder state, suggestions |
| `useImport` | `hooks/useImport.ts` | Handle file upload and progress |
| `useMatching` | `hooks/useMatching.ts` | Call matching engine, process results |
| `useExport` | `hooks/useExport.ts` | Export documents to various formats |
| `useLLM` | `hooks/useLLM.ts` | LLM suggestions (optional feature) |

---

## 6. Pages

| Page | File | Purpose |
|------|------|---------|
| `Dashboard` | `pages/Dashboard.tsx` | Overview: KB stats, recent apps, quick actions |
| `KnowledgeExplorer` | `pages/KnowledgeExplorer.tsx` | VS Code-like search: query, filters, results, provenance |
| `ResumeBuilder` | `pages/ResumeBuilder.tsx` | Select evidence, preview, export resume |
| `SOQBuilder` | `pages/SOQBuilder.tsx` | Enter SOQ question, get suggestions, answer, export |
| `DutyStatementBuilder` | `pages/DutyStatementBuilder.tsx` | Input job posting, match evidence, generate response |
| `Settings` | `pages/Settings.tsx` | LLM config, export defaults, import paths |

---

## 7. Components

### 7.1. Reusable Components

| Component | Description |
|-----------|-------------|
| `StarRating` | 1-5 star display (read or interactive) |
| `EvidenceBadge` | Shows evidence source + success history (interview/offer icons) |
| `MatchResult` | Card: content preview, score, stars, evidence links |
| `KnowledgeItemCard` | Full item view: category tag, content, linked evidence |
| `DocumentPreview` | Rendered document preview with traceability markers |
| `TemplateEditor` | JSON template editor with live preview |
| `FileUploader` | Drag-drop + file dialog for imports |
| `ProgressTracker` | Progress bar for import/export operations |
| `SuggestionPanel` | Ranked evidence suggestions with add/remove buttons |
| `ContentEditor` | Editable area with inline traceability markers |

### 7.2. Component Props (Key Examples)

```typescript
interface StarRatingProps {
  rating: number;        // 1-5
  interactive?: boolean;  // if true, user can click to change
  onRatingChange?: (r: number) => void;
}

interface MatchResultProps {
  item: KnowledgeItem;
  score: number;          // 0.0 - 1.0
  starRating: number;     // 1-5
  historicalSuccess?: 'interview' | 'offer' | 'rejected';
  onSelect: (item: KnowledgeItem) => void;
}

interface DocumentPreviewProps {
  document: BuiltDocument;
  showTraceability?: boolean;
  onEdit: (itemId: string) => void;
}
```

---

## 8. Import Parsers

### 8.1. BaseParser Interface

File: `backend/app/parsers/base.py`

```python
class BaseParser(ABC):
    @abstractmethod
    def parse(self, file_path: str) -> ParsedDocument: ...
    @abstractmethod
    def supported_types(self) -> list[str]: ...

class ParsedDocument(BaseModel):
    filename: str
    file_type: str
    paragraphs: list[Paragraph]
    
class Paragraph(BaseModel):
    text: str
    style: str  # "Normal", "Heading 1", "List Bullet", etc.
    is_bullet: bool
    bullet_level: int
    is_heading: bool
    heading_level: int | None
```

### 8.2. DocxParser

File: `backend/app/parsers/docx_parser.py`
Uses `python-docx`. Extracts paragraph text, styling, bullet levels, headings.

### 8.3. PdfParser

File: `backend/app/parsers/pdf_parser.py`
Uses `pymupdf` (fitz). Extracts text with layout preservation.

### 8.4. TxtParser

File: `backend/app/parsers/txt_parser.py`
Simple line-by-line reader. All text is "Normal" style.

### 8.5. Parser Factory

File: `backend/app/parsers/__init__.py`

```python
def get_parser(file_type: str) -> BaseParser
```

---

## 9. Template Engine

### 9.1. Template Format (JSON)

```json
{
  "name": "standard",
  "sections": [
    {"title": "Summary", "type": "profile", "source": "user_profile"},
    {"title": "Experience", "type": "experience", 
     "items": ["resume_bullet"], "group_by": "evidence_id", "show_dates": true},
    {"title": "Skills", "type": "skills", "columns": 2}
  ],
  "formatting": {
    "font": "Calibri", "font_size": 11, "line_spacing": 1.15
  }
}
```

### 9.2. Template Engine Service

File: `backend/app/services/template_engine.py`

```python
class TemplateEngine:
    def render(self, template: dict, items: list[KnowledgeItem], 
               evidence: list[Evidence], user_profile: dict) -> RenderedDocument
    def apply_formatting(self, doc: RenderedDocument, fmt: dict) -> FormattedDocument
```

Rules:
- Sections are rendered in order defined by template
- Grouped items get sub-headers (e.g., job title + dates)
- Empty sections are omitted with a warning

---

## 10. Export Engine

### 10.1. DocxExporter

Uses `python-docx`:
- Heading styles for section headers
- Bullet lists for resume bullets
- Custom XML comments for traceability (visible in Word's "Inspect Document")
- Proper margins, fonts, spacing

### 10.2. TxtExporter
Plain text with `- ` bullets and UPPERCASE section headers.

### 10.3. PdfExporter

Uses `reportlab` for programmatic PDF generation. Limited formatting in MVP.

### 10.4. File Saving

Backend writes to a temp directory, returns file path. Frontend invokes an Electron `dialog.showSaveDialog` (via IPC) to prompt the user.

---

## 11. Validation Rules

### Rule: completeness
- Resume: non-empty contact info, at least 1 experience bullet, at least 3 skills
- SOQ: answer word count >= 50, all questions addressed

### Rule: keyword_coverage
- Job posting keywords found in document content
- Reports missing keywords and coverage percentage

### Rule: evidence_traceability
- All content blocks link to at least one evidence record
- No orphaned content

### Rule: length
- Resume: <= 2 pages (~500-1000 words)
- SOQ: <= 250 words per answer (configurable)
- Duty statement: <= 200 words per duty

### ValidationResult Schema

```python
class ValidationIssue(BaseModel):
    rule: str
    severity: str  # "error" | "warning" 
    message: str
    field: str | None

class ValidationResult(BaseModel):
    valid: bool
    errors: list[ValidationIssue]
    warnings: list[ValidationIssue]
    score: float  # 0.0 - 1.0
```

---
## 12. Matching Algorithm

### 12.1. TF-IDF Implementation

```python
# Backend: backend/app/services/tfidf_service.py
class TfidfVectorizer:
    def fit(self, documents: list[str]) -> None:
        # Build vocabulary, compute IDF
        self.vocab = set of all terms
        self.idf = {term: log(N / df(term)) for term in vocab}
        
    def transform(self, text: str) -> dict[str, float]:
        # TF-IDF vector for one document (sparse dict)
        tf = term_count / total_terms
        return {term: tf * self.idf[term] for term in unique_terms if term in vocab}
        
    def cosine_similarity(self, vec_a: dict, vec_b: dict) -> float:
        dot = sum(vec_a[t] * vec_b.get(t, 0) for t in vec_a)
        norm_a = sqrt(sum(v**2 for v in vec_a.values()))
        norm_b = sqrt(sum(v**2 for v in vec_b.values()))
        return dot / (norm_a * norm_b) if norm_a * norm_b > 0 else 0.0
```

### 12.2. Historical Success Weighting

```python
def weighted_score(base_score: float, item_id: str) -> float:
    weight = repo.get_success_weight(item_id)  # 0.0 to 0.3+
    # weight = alpha * interview_rate + beta * offer_rate
    return base_score * (1 + weight)

# Config: alpha = 0.1, beta = 0.2
```

### 12.3. Keyword Expansion

```python
def expand_query(query: str) -> list[str]:
    terms = tokenize(query)
    expanded = list(terms)
    for term in terms:
        expanded.extend(get_synonyms(term))  # from synonyms.json
        expanded.append(stem(term))          # Porter stemmer
    return unique(expanded)
```

### 12.4. End-to-End Match Flow

1. Tokenize and expand the query
2. Vectorize with cached TF-IDF index
3. Compute cosine similarity vs all knowledge items
4. Apply historical success weighting
5. Filter items below `min_score` (default 0.3)
6. Sort descending by final score
7. Take top-k results
8. Assign star rating (see Section 13.3)
9. Enrich each result with evidence links and provenance

---

## 13. Evidence Scoring

### 13.1. Evidence Strength

```python
def calculate_evidence_strength(evidence_id: str) -> float:
    # Factors: number of linked items, content length, historical success
    item_count = repo.count_linked_items(evidence_id)
    content_len = repo.get_content_length(evidence_id)
    success_rate = repo.get_success_rate(evidence_id)
    
    return 0.4 * normalize(item_count) + 0.3 * normalize(content_len) + 0.3 * success_rate
```

### 13.2. Knowledge Item Match Score

A match score combines:
1. TF-IDF cosine similarity (0.0 - 1.0)
2. Historical success weight (0.0 - 0.3)
3. Evidence strength (0.0 - 1.0, weighted at 20%)

```python
final_score = cosine_sim * (1 + hist_weight) * (0.8 + 0.2 * evidence_strength)
```

### 13.3. Star Rating

| Range | Stars | Meaning |
|-------|-------|---------|
| 0.90+ | 5 | Exact match, proven successful |
| 0.80-0.89 | 4 | Strong match, historically successful |
| 0.70-0.79 | 3 | Good match, some usage |
| 0.60-0.69 | 2 | Relevant but limited evidence |
| 0.50-0.59 | 1 | Weak but potentially relevant |
| < 0.50 | — | Below threshold, hidden by default |

---

## 14. Keyword Expansion

### 14.1. Synonym File

File: `backend/app/data/synonyms.json`

```json
{
  "analytical": ["analysis", "analyze", "research", "reports", "problem solving"],
  "confidential": ["privacy", "records", "customer data", "verification", "documentation"],
  "communication": ["customer service", "interpersonal", "written", "verbal"],
  "leadership": ["supervision", "team management", "mentorship", "guidance"]
}
```

### 14.2. Stemming

Uses the Porter Stemmer algorithm (`nltk` or `pystemmer`).

### 14.3. Category Keywords

Each category has associated keywords defined in `backend/app/data/categories.json`:

```json
{
  "Customer Service": ["customer", "service", "satisfaction", "complaint", "resolution"],
  "Analysis": ["analysis", "data", "report", "excel", "sql", "dashboard"],
  "Confidential Information": ["confidential", "privacy", "sensitive", "records", "compliance"]
}
```

### 14.4. Expansion Process

1. Tokenize query
2. For each token, add synonyms from `synonyms.json`
3. Apply Porter stemming
4. If query matches a category name, add category keywords
5. Return deduplicated expanded term list

---

## 15. LLM Service

### 15.1. LLMConfig

```python
class LLMConfig(BaseModel):
    enabled: bool = False
    endpoint: str = "http://127.0.0.1:11434"
    model: str = "gemma2"
    max_tokens: int = 500
    temperature: float = 0.3
```

### 15.2. System Prompt (Critical)

The system prompt enforces the "never create facts" rule:

```
You are CareerOS Grammar Assistant. You help improve the flow, grammar, and 
readability of career documents ONLY.

STRICT RULES:
1. You may ONLY suggest changes to: spelling, grammar, punctuation, 
   sentence structure, and transitions between paragraphs.
2. You may NEVER add, remove, or alter factual information.
3. You may NEVER invent new content, experiences, or achievements.
4. If asked to create new facts, REFUSE immediately.

Return a JSON object: {"suggestions": [{"original": "...", "replacement": "...", 
"type": "grammar|transition", "reason": "..."}]}
```

### 15.3. Safety Implementation

```python
class LLMService:
    def grammar_suggestions(self, text: str) -> list[Suggestion]:
        response = self._call_llm(text, mode="grammar")
        # Filter: reject if any suggestion changes factual content
        return self._filter_factual_changes(response.suggestions)
    
    def _filter_factual_changes(self, suggestions: list[Suggestion]) -> list[Suggestion]:
        # Heuristic: if suggestion length differs by > 30% and adds new entities, reject
        # Log all filtered suggestions to llm_audit.log
        ...
```

### 15.4. LLM Audit Log

File: `logs/llm_audit.log`

All LLM interactions are logged:
```json
{"timestamp": "2026-08-01T10:30:00Z", "request_id": "REQ-001", 
 "mode": "grammar", "original_length": 150, 
 "suggestions_count": 3, "accepted": 2, "rejected": 1}
```

---

## 16. Testing Strategy

### Backend Tests (pytest)

| Test Module | Focus |
|------------|-------|
| `test_repositories.py` | CRUD, edge cases, FTS5 search |
| `test_services.py` | Matching score accuracy, builder assembly, export |
| `test_parsers.py` | DOCX/PDF/TXT parsing with fixture files |
| `test_builders.py` | Resume/SOQ/Duty assembly + traceability |
| `test_validation.py` | Validation rules, keyword coverage, completeness |
| `test_e2e.py` | Full import → search → build → export flow |

### Frontend Tests (Vitest)

| Test Module | Focus |
|------------|-------|
| `StarRating.test.tsx` | Rendering, click behavior |
| `KnowledgeExplorer.test.tsx` | Search flow, filters, results |
| `ResumeBuilder.test.tsx` | Builder workflow, selection |
| `MatchResult.test.tsx` | Score display, evidence links |

### Test Fixtures

Location: `backend/tests/fixtures/`

| File | Purpose |
|------|---------|
| `sample_resume.docx` | Resume with 5 bullets across 2 jobs |
| `sample_soq.docx` | 2 SOQ questions with detailed answers |
| `sample_duty.txt` | Plain text job posting duty statement |

### E2E Test Flow

1. Import `sample_resume.docx` and `sample_soq.docx`
2. Verify 7+ knowledge items created
3. Search "confidential" → expect 1+ results
4. Build resume from 5 bullets → verify traceability dict has 5 entries
5. Export to DOCX → verify file exists and opens
6. Validate → expect 0 errors, < 3 warnings

---
