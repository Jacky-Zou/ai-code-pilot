# Development Guide 🧑‍💻

AICodePilot follows phased delivery. Each task must move from `TODO` to `IN_PROGRESS` to `DONE` only after validation passes.

## Workflow Rules ✅

- Keep the Agent core handwritten in the first phase.
- Work on one TodoList item at a time.
- Update docs with every phase.
- Run the requested validation before moving to the next task.
- Use Conventional Commits.
- Keep secrets out of Git.

## Phase Completion Checklist 🧪

Every completed phase must include a from-start-to-finish sanity check:

1. Verify directory structure and required files still match the project plan.
2. Run focused tests for the phase.
3. Run the full backend test suite when backend code is affected.
4. Smoke-test runtime entrypoints such as CLI imports, FastAPI app creation, OpenAPI schema, and health checks.
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
