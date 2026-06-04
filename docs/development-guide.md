# Development Guide

AICodePilot is developed as an engineering-grade AI Agent project. Each change should preserve the core product goal: help developers understand, search, debug, and improve codebases through LLM Agent workflows.

## 🧭 Development Principles

- Keep the Agent core understandable and framework-light.
- Prefer existing project patterns over new abstractions.
- Keep file access, shell execution, and API-key handling inside documented safety boundaries.
- Update documentation when user-facing behavior, architecture, setup, or validation changes.
- Commit only after relevant validation passes.
- Do not commit secrets, local cache folders, generated build artifacts, or private environment files.

## 🧱 Repository Layout

```text
backend/
  app/
    agent/      Agent planner, executor, prompts, schemas, and patch helpers
    api/        FastAPI routes and API schemas
    core/       configuration, logging, exceptions, and project path mapping
    llm/        provider abstraction, HTTP client, OpenAI, and DeepSeek providers
    memory/     bounded conversation memory
    rag/        scanning, chunking, embedding, vector store, and retrieval
    tools/      safe tool implementations and registry
  tests/        backend regression tests
frontend/
  app/          Next.js app shell and global styles
  components/   workspace, provider selector, timeline, and evidence components
  lib/          API client and shared frontend utilities
docs/           architecture, API, deployment, security, and product docs
```

## ⚙️ Backend Workflow

Install dependencies:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Run the API:

```bash
uvicorn app.main:app --reload
```

Run backend tests:

```bash
pytest backend/tests
```

Run quality gates from the repository root:

```bash
ruff check .
black --check .
mypy backend/app
```

## 🖥️ Frontend Workflow

Install dependencies:

```bash
cd frontend
npm install
```

Run development server:

```bash
npm run dev
```

Run frontend validation:

```bash
npm run typecheck
npm run lint
npm run build
```

The frontend should remain synchronized with the backend API contract in `frontend/lib/api.ts`.

## 🧪 Validation Policy

Use the narrowest meaningful validation first, then run broader gates before committing.

| Change Type | Required Validation |
|---|---|
| Backend Agent, tools, RAG, API, config | Focused pytest file plus `pytest backend/tests` |
| Python style or typing | `ruff check .`, `black --check .`, `mypy backend/app` |
| Frontend components or styles | `npm run typecheck`, `npm run lint`, `npm run build` |
| Docker or environment changes | `docker compose up --build` when practical |
| Documentation only | Encoding scan and manual consistency review |

## 🔐 Security Rules

- API keys belong in `.env`, never in source, logs, README examples, or committed screenshots.
- File tools must remain constrained to the declared project root.
- Binary and oversized file reads must be rejected clearly.
- Shell execution must use allowlisted behavior, `shell=False`, timeout control, and destructive-command blocking.
- Patch generation must produce reviewable diffs without modifying files automatically.

## 🧠 Agent Boundaries

The Agent should never return internal tool protocol JSON as the final user answer. Tool actions are implementation details that belong in `tool_calls` and the UI timeline. Final answers should be professional, readable, and grounded in references when available.

When improving Agent behavior:

- Keep the planner output parser strict.
- Keep the final-answer synthesis prompt separate from the tool-selection prompt.
- Add regression tests for any prompt protocol or parsing behavior.
- Verify that malformed model output fails gracefully.

## 📁 Workspace Import Boundaries

Frontend folder and file import uses browser APIs for local previews. It does not grant the backend direct access to arbitrary local paths.

Real indexing uses `/api/projects/index` and requires a backend-visible path. In Docker, use `PROJECTS_HOST_ROOT` and `PROJECTS_CONTAINER_ROOT` to mount projects into the backend container.

Supported frontend import extensions are maintained in `frontend/components/ChatWorkspace.tsx`. Unsupported binary or office document formats must be blocked before import and explained to the user.

## 🧾 Documentation Rules

- Documentation must be pure English.
- Keep titles concise and hierarchical.
- Prefer short paragraphs, tables, and bullet lists over phase logs.
- Keep the TodoList as a current roadmap board, not a historical journal.
- Scan for CJK text and mojibake before committing documentation updates.

Suggested scan:

```bash
rg -n -P "\p{Han}|[\x{FFFD}\x{9983}\x{9281}\x{9514}\x{6D93}\x{6D60}]" README.md docs frontend/components frontend/app -S
```

## ✅ Commit Checklist

Before committing:

1. Review `git diff`.
2. Run the relevant validation commands.
3. Confirm generated artifacts are ignored.
4. Update docs when behavior changed.
5. Use a Conventional Commit message.

Example:

```bash
git commit -m "fix: harden frontend workspace import and docs"
```
