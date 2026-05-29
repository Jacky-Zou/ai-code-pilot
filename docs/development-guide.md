# Development Guide 🧑‍💻

AICodePilot follows phased delivery. Each task must move from `TODO` to `IN_PROGRESS` to `DONE ✅` only after validation passes.

## Workflow Rules ✅

- Keep the Agent core handwritten in the first phase.
- Work on one TodoList item at a time.
- Update docs with every task or phase that changes user-facing behavior.
- Run the requested validation before moving to the next task.
- Use Conventional Commits.
- Keep secrets out of Git.

## Phase Completion Checklist 🧪

Every completed phase must include a from-start-to-finish sanity check:

1. Verify directory structure and required files still match the project plan.
2. Run focused tests for the phase.
3. Run the full backend test suite when backend code is affected.
4. Smoke-test runtime entrypoints such as CLI imports, FastAPI app creation, OpenAPI schema, health checks, and frontend rendering.
5. Review TodoList statuses and related docs for consistency.
6. Commit and push only after validation passes.

## Phase 3 Validation 🌐

Phase 3 specifically verifies:

- `GET /api/health`
- `POST /api/chat`
- `POST /api/projects/index`
- `POST /api/projects/search`
- Unified JSON error responses
- No regression in Agent, tools, providers, or RAG tests

## Phase 4 Frontend Validation 🖥️

Phase 4 verifies the interactive web workspace:

- `npm run typecheck` confirms React and API-client types are valid.
- `npm run lint` checks frontend source quality.
- `npm run build` confirms the Next.js app compiles for production.
- A browser smoke test confirms the dashboard renders at `http://127.0.0.1:3000`.
- The UI flow covers provider/model selection, project indexing, Agent chat, tool call timeline, and code references.

Completed Phase 4 validation includes:

- Full backend regression test with a temporary Chroma vector store path: `86 passed`.
- Frontend `npm run typecheck`.
- Frontend `npm run lint`.
- Frontend `npm run build`.
- HTTP smoke test against a local Next.js server: `STATUS=200`.

## Phase 5 Memory Validation 🧠

The conversation memory task verifies:

- Recent user, assistant, and tool messages are stored in LLM-ready order.
- History is trimmed by complete user turns rather than arbitrary message count.
- Blank messages and invalid memory limits fail clearly.
- `pytest` runs without pytest cache warnings by disabling the cache provider in `pytest.ini`.

## Phase 5 Log Tool Validation 🧾

The log analyzer task verifies:

- Severity counts for `INFO`, `WARNING`, `ERROR`, and related levels.
- Extraction of issue lines and exception names.
- Python traceback frame parsing with file path, line number, and function name.
- Result limiting through `max_issues`.
- Read-only behavior with no filesystem or shell side effects.
