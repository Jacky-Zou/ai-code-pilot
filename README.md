# AICodePilot

AICodePilot is an AI coding assistant for codebase understanding, semantic search, log analysis, tool calling, patch suggestions, and developer workflow support.

The project is built as an engineering-grade LLM Agent system rather than a simple chat demo. It includes a handwritten Agent loop, a safe tool layer, RAG retrieval, multi-provider LLM abstraction, FastAPI APIs, a Next.js workspace UI, tests, Docker deployment, and documentation.

## Features

- Handwritten Agent loop with structured planning, tool execution, and final answer synthesis.
- Multi-provider LLM layer with OpenAI and DeepSeek support.
- Safe tools for file listing, project tree inspection, file reading, text search, log analysis, command execution, and patch suggestions.
- RAG pipeline with project scanning, line-based chunking, embeddings, vector storage, and Top-K retrieval.
- FastAPI backend for health, chat, project indexing, and project search.
- Next.js frontend with Model Center, Workspace management, Agent Chat, Agent Steps, Code Evidence, and Project Summary.
- Docker Compose deployment for backend and frontend.
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
| Deployment | Docker, docker-compose, environment-based configuration |

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

## Docker

Run the full stack:

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
| `POST` | `/api/chat` | Ask the Agent a codebase question |
| `POST` | `/api/projects/index` | Index a backend-visible project path and return project summary metadata |
| `POST` | `/api/projects/search` | Search indexed code chunks |

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
- [Security](docs/security.md)
- [Deployment](docs/deployment.md)
- [User Guide](docs/user-guide.md)
- [Development Guide](docs/development-guide.md)
- [Resume Guide](docs/resume.md)
- [TodoList](docs/todolist.md)

## License

This project is released under the MIT License. See [LICENSE](LICENSE).
