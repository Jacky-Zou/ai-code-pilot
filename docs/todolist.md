# AICodePilot TodoList

This board tracks current product and architecture priorities. It intentionally excludes historical phase logs and temporary implementation notes.

Status values: `BACKLOG`, `TODO`, `IN_PROGRESS`, `DONE`, `BLOCKED`.

## Backlog

| ID | Item | Scope | Validation |
|---|---|---|---|
| BL-01 | Additional model providers | Add backend providers for Qwen, GLM, Claude, Gemini, Moonshot, and other OpenAI-compatible APIs. | Provider factory tests and live-key smoke tests when credentials are available. |
| BL-02 | Repository intelligence | Add dependency graph analysis, call graph summaries, framework detection, and security scan hooks. | Parser tests and sample-project reports. |
| BL-03 | Multi-file patch workflow | Extend patch suggestions into reviewable multi-file change plans with diff preview and approval gates. | Patch validation tests and UI review flow. |
| BL-04 | Production authentication | Replace frontend-local account mocks with backend auth, persistent users, sessions, and profile storage. | Auth API tests, session tests, and frontend integration checks. |
| BL-05 | Streaming transport | Add SSE or WebSocket streaming for Agent reasoning state, tool-call progress, and partial responses. | Stream contract tests and browser interaction tests. |

## To Do

| ID | Item | Scope | Validation |
|---|---|---|---|
| TD-01 | Frontend regression tests | Add coverage for model selection, workspace import, chat submit, modals, and right-rail panels. | Playwright or component test suite. |
| TD-02 | Import limits | Add explicit caps for very large folders and clearer warning states for browser file enumeration. | Unit tests and manual large-folder check. |
| TD-03 | Documentation consolidation | Keep root, backend, and frontend README files synchronized with implementation. | Markdown review and encoding scan. |
| TD-04 | Release checklist | Convert final release tasks into a compact v1.0 checklist. | README and docs review. |

## In Progress

| ID | Item | Scope | Validation |
|---|---|---|---|
| IP-01 | Frontend workspace hardening | Improve Model Center, Workspace import, summary modal, chat composer, visual alignment, and right-rail boundaries. | `npm run typecheck`, `npm run lint`, `npm run build`, and browser validation. |
| IP-02 | Project structure cleanup | Remove local caches, logs, and generated vector data from the working tree while preserving ignored runtime paths. | Directory audit and `git status`. |
| IP-03 | Documentation audit | Keep Markdown assets pure English, consistent, and synchronized with the actual codebase. | Encoding scan and manual consistency review. |

## Done

| ID | Item | Result | Validation |
|---|---|---|---|
| DN-01 | Mini Agent core | Implemented provider abstraction, tool protocol, safe file/search tools, CLI, and executor flow. | Backend tests passed. |
| DN-02 | RAG retrieval | Implemented scanner, chunker, embeddings, vector store, retriever, and `retrieve_code` tool. | RAG tests passed. |
| DN-03 | FastAPI service | Exposed health, chat, project indexing, and project search APIs. | API tests passed. |
| DN-04 | Advanced tools | Added conversation memory, log analysis, safe shell execution, and patch suggestions. | Advanced tool tests passed. |
| DN-05 | Docker and CI baseline | Added Docker Compose deployment and GitHub Actions quality gates. | Docker smoke checks and CI gates configured. |
