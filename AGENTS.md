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
