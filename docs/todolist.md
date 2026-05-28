# AICodePilot TodoList

Status values: TODO, IN_PROGRESS, DONE ✅, BLOCKED.

## Phase 0: Project Initialization

| ID | Task | Description | Files | Validation | Status |
|---|---|---|---|---|---|
| P0-T01 | Create project structure | Initialize backend, frontend, docs, examples, scripts, and data directories with placeholder files | all project skeleton files | `tree -L 4` or equivalent directory listing shows required structure | DONE ✅ |
| P0-T02 | Create .gitignore | Add Python, Node, env, build, cache, log, and data ignore rules | `.gitignore` | `git status` does not track `.env` or ignored artifacts | DONE ✅ |
| P0-T03 | Create .env.example | Add app, OpenAI, DeepSeek, embedding, and vector store placeholders | `.env.example` | Manual field check confirms all required variables exist | DONE ✅ |
| P0-T04 | Create README first version | Document overview, features, stack, roadmap, providers, quick start placeholder, and license | `README.md` | README renders and required sections exist | DONE ✅ |
| P0-T05 | Create initial docs | Create architecture, agent, RAG, API, security, deployment, user, development, resume docs, and this TodoList | `docs/*.md` | All required docs exist | DONE ✅ |
| P0-T06 | Create backend requirements | Add first backend dependency list | `backend/requirements.txt` | File contains required packages | DONE ✅ |
| P0-T07 | Initialize Git commit | Initialize repository if needed and commit Phase 0 | `.git`, all Phase 0 files | `git log --oneline -1` shows Phase 0 commit | DONE ✅ |

## Phase 1: Mini Agent Core

| ID | Task | Description | Files | Validation | Status |
|---|---|---|---|---|---|
| P1-T01 | Implement config | Load env config with pydantic-settings for app, OpenAI, DeepSeek, embedding, vector store | `backend/app/core/config.py`, `backend/tests/test_config.py` | `pytest backend/tests/test_config.py` | DONE ✅ |
| P1-T02 | Implement logger | Provide shared logger honoring LOG_LEVEL with timestamp, level, module, and message | `backend/app/core/logger.py` | Simple logger smoke run succeeds | DONE ✅ |
| P1-T03 | Implement LLM base schemas | Define provider abstraction and message/response structures | `backend/app/llm/base.py`, `backend/app/llm/schemas.py` | pytest validates abstract interface | DONE ✅ |
| P1-T04 | Implement OpenAI provider | Call OpenAI-compatible chat completions with clear config errors | `backend/app/llm/openai_provider.py` | Missing key returns clear error; optional live call when key exists | DONE ✅ |
| P1-T05 | Implement DeepSeek provider | Call DeepSeek chat API using same provider interface | `backend/app/llm/deepseek_provider.py` | Missing key returns clear error; factory can create provider | DONE ✅ |
| P1-T06 | Implement provider factory | Resolve default/requested provider and reject unsupported names | `backend/app/llm/factory.py`, `backend/tests/test_llm_factory.py` | `pytest backend/tests/test_llm_factory.py` | DONE ✅ |
| P1-T07 | Implement tool base | Define BaseTool with name, description, args_schema, and run | `backend/app/tools/base.py` | pytest | DONE ✅ |
| P1-T08 | Implement file tools | Add safe `list_files` and `read_file` | `backend/app/tools/file_tools.py`, `backend/tests/test_file_tools.py` | `pytest backend/tests/test_file_tools.py` | DONE ✅ |
| P1-T09 | Implement search tool | Add recursive safe text search with ignored directories and limits | `backend/app/tools/search_tools.py`, `backend/tests/test_search_tools.py` | `pytest backend/tests/test_search_tools.py` | DONE ✅ |
| P1-T10 | Implement tool registry | Register, retrieve, and describe tools with clear missing-tool errors | `backend/app/tools/registry.py`, `backend/tests/test_tool_registry.py` | `pytest backend/tests/test_tool_registry.py` | DONE ✅ |
| P1-T11 | Implement agent prompt | Define developer assistant prompt with tool descriptions and JSON action protocol | `backend/app/agent/prompts.py` | Manual prompt review | DONE ✅ |
| P1-T12 | Implement agent schemas | Define request, response, action, call, and result schemas | `backend/app/agent/schemas.py` | pytest schema construction | DONE ✅ |
| P1-T13 | Implement agent executor | Run LLM action planning, execute tools, summarize results | `backend/app/agent/agent.py`, `backend/app/agent/executor.py` | Agent unit tests pass | DONE ✅ |
| P1-T14 | Implement CLI demo | Provide interactive CLI entrypoint | `backend/app/main.py` | `cd backend && python -m app.main` starts | DONE ✅ |
| P1-T15 | Update Phase 1 docs | Document Mini Agent design and README usage | `docs/agent-design.md`, `README.md`, `docs/todolist.md` | Docs updated and Todo statuses accurate | DONE ✅ |
| P1-T16 | Commit Phase 1 | Commit validated Mini Agent implementation | repository | `git log --oneline -1` shows Phase 1 commit | DONE ✅ |

## Phase 2: RAG Code Retrieval

| ID | Task | Description | Files | Validation | Status |
|---|---|---|---|---|---|
| P2-T01 | Implement project scanner | Scan text/code files and ignore irrelevant directories | `backend/app/rag/indexer.py` | Scanner tests pass | DONE ✅ |
| P2-T02 | Implement code chunker | Split files by line ranges with metadata | `backend/app/rag/chunker.py` | Chunker tests pass | DONE ✅ |
| P2-T03 | Implement embedding client | Support default OpenAI embeddings and provider extension | `backend/app/rag/embeddings.py` | Missing key handled clearly; optional live call | DONE ✅ |
| P2-T04 | Implement vector store | Add/search/save/load vector index with chunk metadata | `backend/app/rag/vector_store.py` | Vector store tests pass | DONE ✅ |
| P2-T05 | Implement retriever | Query Top-K code chunks with path, line, score | `backend/app/rag/retriever.py` | Retriever tests pass | DONE ✅ |
| P2-T06 | Connect RAG to Agent | Add `retrieve_code(query, top_k)` tool | `backend/app/tools/*`, `backend/app/agent/*` | Agent can call retrieval tool | DONE ✅ |
| P2-T07 | Update RAG docs | Document RAG design and architecture changes | `docs/rag-design.md`, `docs/architecture.md`, `README.md`, `docs/todolist.md` | Docs updated | DONE ✅ |
| P2-T08 | Commit Phase 2 | Commit validated RAG implementation | repository | `git log --oneline -1` shows Phase 2 commit | DONE ✅ |

## Phase 3: FastAPI Backend Service

| ID | Task | Description | Files | Validation | Status |
|---|---|---|---|---|---|
| P3-T01 | Implement API schemas | Define request/response models for health, chat, index, search | `backend/app/api/schemas.py` | Schema tests pass | DONE ✅ |
| P3-T02 | Implement chat router | Expose `/api/chat` | `backend/app/api/routes_chat.py` | API tests pass | DONE ✅ |
| P3-T03 | Implement project router | Expose `/api/projects/index` and `/api/projects/search` | `backend/app/api/routes_project.py` | API tests pass | DONE ✅ |
| P3-T04 | Implement FastAPI main | Wire routers and health endpoint | `backend/app/main.py` | `uvicorn app.main:app --reload` starts | DONE ✅ |
| P3-T05 | Implement exceptions | Add unified exception classes and handlers | `backend/app/core/exceptions.py` | Error response tests pass | DONE ✅ |
| P3-T06 | Add API tests | Test health, chat, project index, search | `backend/tests/test_api.py` | `pytest backend/tests/test_api.py` | DONE ✅ |
| P3-T07 | Update API docs | Document endpoints and examples | `docs/api.md`, `README.md`, `docs/todolist.md` | Docs updated | DONE ✅ |
| P3-T08 | Commit Phase 3 | Commit validated FastAPI service | repository | `git log --oneline -1` shows Phase 3 commit | DONE ✅ |

## Phase 4: Web Frontend

| ID | Task | Description | Files | Validation | Status |
|---|---|---|---|---|---|
| P4-T01 | Initialize Next.js frontend | Create React/Next/Tailwind project structure | `frontend/*` | Frontend installs/builds | DONE ✅ |
| P4-T02 | Implement API client | Add typed API calls | `frontend/lib/api.ts` | Type check/build passes | DONE ✅ |
| P4-T03 | Implement provider selector | Support OpenAI and DeepSeek provider/model choices | `frontend/components/ProviderSelector.tsx` | UI renders choices | DONE ✅ |
| P4-T04 | Implement chat page | Build agent chat workflow | `frontend/app/*` | Manual browser test | TODO |
| P4-T05 | Implement project index page | Let user index a project path | `frontend/app/*` | Manual browser test | TODO |
| P4-T06 | Implement ToolCallTimeline | Display tool call sequence and results | `frontend/components/ToolCallTimeline.tsx` | Component renders sample data | TODO |
| P4-T07 | Implement CodeReference | Display file paths, lines, snippets, explanations | `frontend/components/CodeReference.tsx` | Component renders sample data | TODO |
| P4-T08 | Update frontend docs | Document frontend usage | `README.md`, `docs/user-guide.md`, `docs/todolist.md` | Docs updated | TODO |
| P4-T09 | Commit Phase 4 | Commit validated web UI | repository | `git log --oneline -1` shows Phase 4 commit | TODO |

## Phase 5: Advanced Agent Capabilities

| ID | Task | Description | Files | Validation | Status |
|---|---|---|---|---|---|
| P5-T01 | Implement conversation memory | Store bounded multi-turn context | `backend/app/memory/conversation_memory.py` | Memory tests pass | TODO |
| P5-T02 | Implement log analyzer | Add `analyze_log(log_text)` tool | `backend/app/tools/*` | Tool tests pass | TODO |
| P5-T03 | Implement safe shell tool | Add restricted `run_command(command, cwd)` | `backend/app/tools/shell_tools.py` | Shell safety tests pass | TODO |
| P5-T04 | Implement patch generation | Generate diff suggestions without auto-editing | `backend/app/agent/*` | Patch output tests pass | TODO |
| P5-T05 | Connect advanced tools | Register memory, log, shell, patch capabilities in Agent | `backend/app/tools/registry.py`, `backend/app/agent/*` | Agent tests pass | TODO |
| P5-T06 | Update security docs | Document advanced tool security model | `docs/security.md`, `docs/agent-design.md`, `README.md`, `docs/todolist.md` | Docs updated | TODO |
| P5-T07 | Commit Phase 5 | Commit validated advanced capabilities | repository | `git log --oneline -1` shows Phase 5 commit | TODO |

## Phase 6: Engineering Quality

| ID | Task | Description | Files | Validation | Status |
|---|---|---|---|---|---|
| P6-T01 | Improve config | Refine settings validation and defaults | `backend/app/core/config.py` | Config tests pass | TODO |
| P6-T02 | Improve logging | Add consistent logger usage across backend | `backend/app/core/logger.py`, backend modules | Logging smoke tests pass | TODO |
| P6-T03 | Improve exceptions | Normalize domain/API errors | `backend/app/core/exceptions.py` | Exception tests pass | TODO |
| P6-T04 | Expand tests | Cover config, factory, tools, registry, chunker, retriever, API | `backend/tests/*` | `pytest` | TODO |
| P6-T05 | Configure ruff | Add lint config | `pyproject.toml` or `ruff.toml` | `ruff check .` | TODO |
| P6-T06 | Configure black | Add format config | `pyproject.toml` | `black --check .` | TODO |
| P6-T07 | Configure mypy | Add typing config | `pyproject.toml` | `mypy backend/app` | TODO |
| P6-T08 | Add GitHub Actions draft | Add CI workflow draft | `.github/workflows/ci.yml` | Workflow file exists | TODO |
| P6-T09 | Commit Phase 6 | Commit quality improvements | repository | `git log --oneline -1` shows Phase 6 commit | TODO |

## Phase 7: Docker Deployment

| ID | Task | Description | Files | Validation | Status |
|---|---|---|---|---|---|
| P7-T01 | Write backend Dockerfile | Containerize FastAPI backend | `backend/Dockerfile` | Backend image builds | TODO |
| P7-T02 | Write frontend Dockerfile | Containerize Next.js frontend | `frontend/Dockerfile` | Frontend image builds | TODO |
| P7-T03 | Write docker-compose | Start backend and frontend together | `docker-compose.yml` | `docker compose up --build` starts services | TODO |
| P7-T04 | Refine env example | Ensure Docker env variables are documented | `.env.example` | Manual field check | TODO |
| P7-T05 | Update deployment docs | Document Docker deployment | `docs/deployment.md`, `README.md`, `docs/todolist.md` | Docs updated | TODO |
| P7-T06 | Commit Phase 7 | Commit Docker deployment | repository | `git log --oneline -1` shows Phase 7 commit | TODO |

## Phase 8: Documentation and Resume Packaging

| ID | Task | Description | Files | Validation | Status |
|---|---|---|---|---|---|
| P8-T01 | Complete README | Add screenshots placeholder, setup, env, API, architecture, roadmap | `README.md` | README complete | TODO |
| P8-T02 | Complete architecture doc | Detail modules, data flow, Agent flow, RAG flow | `docs/architecture.md` | Doc complete | TODO |
| P8-T03 | Complete agent design doc | Detail goals, tool calling, prompt, registry, providers | `docs/agent-design.md` | Doc complete | TODO |
| P8-T04 | Complete RAG design doc | Detail scanning, chunking, embedding, retrieval, context injection | `docs/rag-design.md` | Doc complete | TODO |
| P8-T05 | Complete API doc | Detail endpoints, examples, error codes | `docs/api.md` | Doc complete | TODO |
| P8-T06 | Complete security doc | Detail file, shell, API key, validation, model safety | `docs/security.md` | Doc complete | TODO |
| P8-T07 | Complete resume doc | Add resume-ready project description and technical highlights | `docs/resume.md` | Resume text complete | TODO |
| P8-T08 | Final validation | Run tests, lint, type checks, Docker build | all | `pytest`, `ruff check .`, `black --check .`, `mypy backend/app`, `docker compose up --build` | TODO |
| P8-T09 | Final commit | Commit final documentation | repository | `git log --oneline -1` shows final docs commit | TODO |
| P8-T10 | Tag release | Create v1.0.0 release tag and push | git tag/remote | `git tag --list v1.0.0` | TODO |




































