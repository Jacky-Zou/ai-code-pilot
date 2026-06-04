# AICodePilot

AICodePilot is an AI coding assistant for codebase understanding, semantic search, code questions, log analysis, tool calling, and development workflow support.

The project is intentionally built as an engineering-grade LLM Agent system rather than a simple chat demo. It includes a handwritten Agent execution loop, a safe tool layer, RAG retrieval, multi-provider LLM abstraction, FastAPI APIs, a Next.js workspace UI, tests, Docker deployment, and project documentation.

## 🚀 Features

- Handwritten Agent loop with structured tool planning, tool execution, and final answer synthesis.
- Multi-provider LLM layer with OpenAI as the default provider and DeepSeek support.
- Safe codebase tools for file listing, project tree inspection, file reading, text search, log analysis, command execution, and patch suggestion generation.
- RAG pipeline with project scanning, line-based chunking, embeddings, vector storage, and Top-K code retrieval.
- FastAPI backend with health, chat, project indexing, and project search endpoints.
- Next.js frontend with Model Provider, Workspace management, Agent Chat, Agent Steps, and Code Evidence panels.
- Docker Compose deployment for backend and frontend.
- CI-ready quality gates for tests, linting, formatting, and typing.

## 🧱 Tech Stack

| Area | Technology |
|---|---|
| Backend | Python, FastAPI, Pydantic, pydantic-settings, httpx, Uvicorn |
| Agent | Custom planner/executor, tool registry, prompt protocol, bounded memory |
| Retrieval | OpenAI embeddings, local hash embeddings for tests, Chroma vector store |
| Frontend | Next.js 15, React 18, TypeScript, Tailwind CSS, lucide-react |
| Markdown | react-markdown, remark-gfm, rehype-highlight |
| Quality | pytest, ruff, black, mypy, ESLint, TypeScript |
| Deployment | Docker, docker-compose, environment-based configuration |

## 🧠 Model Providers

Default provider:

```env
LLM_PROVIDER=openai
LLM_MODEL=gpt-5.2
OPENAI_MODEL=gpt-5.2
```

DeepSeek provider:

```env
LLM_PROVIDER=deepseek
LLM_MODEL=deepseek-v4-pro
DEEPSEEK_MODEL=deepseek-v4-pro
```

Runtime API requests can override provider and model per call. The backend currently supports real requests for `openai` and `deepseek`. GLM, Qwen, and Claude are represented in the UI as disabled future integration targets until backend provider modules are implemented.

## 🖥️ Frontend Workspace

The web UI is organized as a professional three-column AI code workspace:

- **Model Provider**: visible provider dropdown, model dropdown, and model capability list.
- **Workspace**: folder import, single code-file import, backend-visible path input, file whitelist validation, workspace tree preview, and indexing action.
- **Agent Chat**: fixed-height central chat surface with compact bubbles, Markdown rendering, highlighted code blocks, quick actions, avatars, and multiline input.
- **Agent Steps**: collapsible timeline for thinking, tool calls, tool outcomes, and request state.
- **Code Evidence**: bounded evidence cards with file paths, line numbers, and highlighted snippets.
- **Project Summary**: import/indexing modal with name, file size, line count, language mix, structure preview, and chunk metrics.

Browser file access is used for frontend previews only. Real backend indexing still requires a backend-visible path.

## ⚙️ Getting Started

Copy the environment template and add real API keys only to `.env`:

```bash
cp .env.example .env
```

Install and start the backend:

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

Install and start the frontend in a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open the web workspace:

```text
http://127.0.0.1:3000
```

The frontend reads `NEXT_PUBLIC_API_BASE_URL` when it is set and otherwise falls back to `http://localhost:8000`.

## 🐳 Docker

Run the full stack from the repository root:

```bash
docker compose up --build
```

The backend runs on `http://localhost:8000`; the frontend runs on `http://localhost:3000`.

### Docker Project Paths

The backend can only inspect paths visible inside its container. Docker Compose mounts `PROJECTS_HOST_ROOT` into `PROJECTS_CONTAINER_ROOT` as read-only workspace storage:

```env
PROJECTS_HOST_ROOT=D:/code/my_projects
PROJECTS_CONTAINER_ROOT=/workspace
NEXT_PUBLIC_DEFAULT_PROJECT_PATH=/workspace
```

With that mapping, a host path such as `D:/code/my_projects/demo-api` can be resolved by the backend to `/workspace/demo-api`. You may also type the container path directly in the Workspace panel.

## 🔌 API Overview

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/health` | Check service status |
| `POST` | `/api/chat` | Ask the Agent a codebase question |
| `POST` | `/api/projects/index` | Index a backend-visible project path |
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

See [API](docs/api.md) for request and response details.

## 🧪 Validation

Backend quality gates:

```bash
pytest backend/tests
ruff check .
black --check .
mypy backend/app
```

Frontend quality gates:

```bash
cd frontend
npm run typecheck
npm run lint
npm run build
```

## 🗺️ Roadmap

Current priorities are tracked in [TodoList](docs/todolist.md). The long-term direction is:

- Harden the streaming Agent UI state model.
- Add real backend authentication and user profiles.
- Implement additional model providers such as Qwen, GLM, Claude, Gemini, and Moonshot.
- Add richer repository intelligence: dependency graphs, test generation, security scanning, and multi-file patch workflows.
- Prepare a polished v1.0 release package.

## 📚 Documentation

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

## 📄 License

This project is released under the MIT License. See [LICENSE](LICENSE).
