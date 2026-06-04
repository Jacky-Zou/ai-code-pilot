# AICodePilot TodoList

This board tracks current product and architecture priorities. It intentionally excludes historical phase logs and temporary implementation notes.

Status values: `BACKLOG`, `TODO`, `IN_PROGRESS`, `DONE`, `BLOCKED`.

## 📋 Backlog

| ID | Item | Scope | Validation |
|---|---|---|---|
| BL-01 | Additional model providers | Add backend providers for Qwen, GLM, Claude, Gemini, Moonshot, and other OpenAI-compatible APIs. | Provider factory tests and live-key smoke tests when credentials are available. |
| BL-02 | Repository intelligence | Add dependency graph analysis, call graph summaries, framework detection, and security scan hooks. | Focused parser tests and sample-project reports. |
| BL-03 | Multi-file patch workflow | Extend patch suggestions into reviewable multi-file change plans with diff preview and approval gates. | Patch validation tests and UI review flow. |
| BL-04 | Production authentication | Replace frontend-local account mocks with backend auth, persistent users, sessions, and profile storage. | Auth API tests, session tests, and frontend integration checks. |
| BL-05 | Streaming transport | Add SSE or WebSocket streaming for Agent reasoning state, tool-call progress, and partial responses. | Stream contract tests and browser interaction tests. |

## ⏳ To Do

| ID | Item | Scope | Validation |
|---|---|---|---|
| TD-01 | Complete frontend visual QA | Have the workspace manually reviewed on common desktop widths after the latest UI refactor. | User browser validation and follow-up bug report triage. |
| TD-02 | Add frontend regression tests | Add component or E2E coverage for model selection, workspace import, chat submit, modals, and right-rail panels. | `npm run test` or Playwright test suite once configured. |
| TD-03 | Improve import tree limits | Add explicit caps for very large folders and clearer warning states when browser file enumeration is too large. | Unit tests for summary limits and manual large-folder check. |
| TD-04 | Document release checklist | Convert final release tasks into a compact v1.0 checklist. | README and docs review. |

## 🏃 In Progress

| ID | Item | Scope | Validation |
|---|---|---|---|
| IP-01 | Frontend workspace hardening | Fix Model Provider visibility, Workspace import behavior, chat density, panel boundaries, modal layout, and background consistency. | `npm run typecheck`, `npm run lint`, `npm run build`, and user browser validation. |
| IP-02 | Documentation audit | Keep README, User Guide, Development Guide, and this TodoList pure English and synchronized with current implementation. | Encoding scan and manual consistency review. |

## ✅ Done

| ID | Item | Result | Validation |
|---|---|---|---|
| DN-01 | Mini Agent core | Implemented provider abstraction, tool protocol, safe file/search tools, CLI, and executor flow. | Backend tests passed. |
| DN-02 | RAG retrieval | Implemented scanner, chunker, embeddings, vector store, retriever, and `retrieve_code` tool. | RAG tests passed. |
| DN-03 | FastAPI service | Exposed health, chat, project indexing, and project search APIs. | API tests passed. |
| DN-04 | Advanced tools | Added conversation memory, log analysis, safe shell execution, and patch suggestions. | Advanced tool tests passed. |
| DN-05 | Docker and CI baseline | Added Docker Compose deployment and GitHub Actions quality gates. | Docker smoke checks and CI gates configured. |
