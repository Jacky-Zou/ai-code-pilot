# AICodePilot

AICodePilot is an AI coding assistant for codebase understanding, semantic search, log analysis, tool calling, patch suggestions, and developer workflow support.

The project is built as an engineering-grade LLM Agent system rather than a simple chat demo. It includes a handwritten Agent loop, a safe tool layer, RAG retrieval, multi-provider LLM abstraction, FastAPI APIs, a Next.js workspace UI, tests, local no-Docker startup, optional Docker deployment, and documentation.

## Features

- Handwritten Agent loop with native tool calling (OpenAI function-calling protocol), loop detection, and text-protocol fallback.
- Multi-provider LLM layer with OpenAI and DeepSeek support.
- Thread-safe session store with TTL + LRU eviction; SQLite persistence for conversation and message history.
- SSE streaming endpoint with per-step events (thinking, tool_start, tool_end, done, error).
- Safe tools for file listing, project tree inspection, file reading, text search, log analysis, patch suggestions, and optional shell execution.
- RAG pipeline with per-project index isolation, 5-minute TTL cache, and two embedding modes: offline local hash (default) or OpenAI semantic.
- FastAPI backend for health, chat (sync + stream), project indexing, search, and session management.
- Next.js frontend with Model Center, Workspace management, Agent Chat, SSE tool timeline, Code Evidence, and Project Summary.
- No-Docker local startup for backend and frontend, with Docker Compose kept as an optional deployment path.
- CI-ready gates for tests, linting, formatting, and typing.

## Architecture

```text
Frontend Workspace
  -> FastAPI API
  -> Agent Planner / Executor
  -> LLM Provider Factory
  -> Tool Registry
  -> RAG Retriever
  -> Local Codebase
```

Key modules:

| Area | Path | Responsibility |
|---|---|---|
| Agent | `backend/app/agent` | Planner, executor, prompts, schemas, patch helpers |
| Tools | `backend/app/tools` | Safe file/search/log/shell tools and registry |
| LLM | `backend/app/llm` | Provider abstraction, OpenAI, DeepSeek, HTTP client |
| RAG | `backend/app/rag` | Indexer, chunker, embeddings, vector store, retriever |
| API | `backend/app/api` | FastAPI routes and response schemas |
| Frontend | `frontend/components` | Workspace UI, provider selector, timeline, evidence |

## Tech Stack

| Area | Technology |
|---|---|
| Backend | Python, FastAPI, Pydantic, pydantic-settings, httpx, Uvicorn |
| Agent | Custom planner/executor, tool registry, prompt protocol, bounded memory |
| Retrieval | OpenAI embeddings, local hash embeddings for tests, Chroma vector store |
| Frontend | Next.js 15, React 18, TypeScript, Tailwind CSS, lucide-react |
| Markdown | react-markdown, remark-gfm, rehype-highlight |
| Quality | pytest, ruff, black, mypy, ESLint, TypeScript |
| Deployment | Local PowerShell scripts, optional Docker Compose, environment-based configuration |

## Model Providers

Default OpenAI configuration:

```env
LLM_PROVIDER=openai
LLM_MODEL=gpt-5.2
OPENAI_MODEL=gpt-5.2
```

DeepSeek configuration:

```env
LLM_PROVIDER=deepseek
LLM_MODEL=deepseek-v4-pro
DEEPSEEK_MODEL=deepseek-v4-pro
```

Runtime API requests can override provider and model per request. The backend currently supports real calls for `openai` and `deepseek`. Qwen, GLM, Claude, Gemini, and Moonshot remain roadmap providers until backend modules are added.

### Bring-your-own-key (frontend)

The **Model Center** panel lets you enter an API key for each provider directly in the UI. Keys are stored in `localStorage` and sent per request — the backend applies them transiently and never logs or persists them. After saving a key, click **↺** to load the real model list for that key via `POST /api/providers/models`. See [docs/model-discovery.md](docs/model-discovery.md).

## Frontend Workspace

The UI is a three-column AI code workspace:

- **Model Center**: source tabs for domestic/global providers, provider cards with logo marks, and model selection.
- **Workspace**: open folder, open code file, backend-visible path indexing, extension whitelist validation, and tree preview.
- **Agent Chat**: fixed-height chat surface with Markdown rendering, compact bubbles, quick actions, avatars, and multiline input.
- **Agent Steps**: timeline-style request state for thinking, tool calls, and evidence generation.
- **Code Evidence**: bounded evidence cards with paths, line numbers, and highlighted snippets.
- **Project Summary**: import/indexing modal with file count, project size, line count, language composition, tech stack, architecture, structure, and purpose summary.

Browser file access is used for local preview only. Real RAG indexing requires a backend-visible path.

## Getting Started

Copy the environment template:

```bash
cp .env.example .env
```

Add real API keys only to `.env`. The file is ignored by Git.

Start the full local stack without Docker:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start-local.ps1
```

Open:

```text
http://localhost:3000
```

The script opens two visible PowerShell windows: one for the FastAPI backend and one for the Next.js frontend. Stop the app by pressing `Ctrl+C` in those windows or closing them.

When launched from Codex, the script also removes sandbox-only PATH entries before starting Node.js so Next.js can run normally.

If dependencies are missing, run the same command once with `-Install`.

## Manual Local Run

Start the backend:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open the API docs:

```text
http://localhost:8000/docs
```

Start the frontend in a second terminal:

```bash
cd frontend
npm install
npm run dev
```

For production-mode local review after UI changes:

```bash
cd frontend
npm run start:fresh
```

Open:

```text
http://127.0.0.1:3000
```

## Optional Docker

Docker is not required for normal local development. If you still want a containerized demo stack, run:

```bash
docker compose up --build
```

Services:

| Service | URL |
|---|---|
| Backend | `http://localhost:8000` |
| Frontend | `http://localhost:3000` |

For Docker project indexing, mount a host workspace into the backend container:

```env
PROJECTS_HOST_ROOT=D:/code/my_projects
PROJECTS_CONTAINER_ROOT=/workspace
NEXT_PUBLIC_DEFAULT_PROJECT_PATH=/workspace
```

## API Overview

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/health` | Check service status |
| `POST` | `/api/chat` | Synchronous agent run with multi-turn memory |
| `POST` | `/api/chat/stream` | SSE streaming agent run (real-time events) |
| `POST` | `/api/projects/index` | Index a backend-visible project path |
| `POST` | `/api/projects/search` | Search indexed code chunks |
| `GET` | `/api/sessions/{id}/messages` | Retrieve persisted message history |
| `DELETE` | `/api/sessions/{id}` | Delete a session |

Example chat request:

```json
{
  "message": "Where is the Agent execution flow implemented?",
  "project_path": "/workspace/AICodePilot",
  "provider": "deepseek",
  "model": "deepseek-v4-pro"
}
```

## Validation

Backend:

```bash
pytest backend/tests
ruff check .
black --check .
mypy backend/app
```

Frontend:

```bash
cd frontend
npm run typecheck
npm run lint
npm run build
```

## Documentation

- [Architecture](docs/architecture.md)
- [Agent Design](docs/agent-design.md)
- [RAG Design](docs/rag-design.md)
- [API](docs/api.md)
- [Streaming Protocol](docs/streaming.md)
- [Security](docs/security.md)
- [Deployment](docs/deployment.md)
- [User Guide](docs/user-guide.md)
- [Development Guide](docs/development-guide.md)
- [Resume Guide](docs/resume.md)
- [TodoList](docs/todolist.md)

## License

This project is released under the MIT License. See [LICENSE](LICENSE).
