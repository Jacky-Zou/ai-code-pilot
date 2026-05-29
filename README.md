# AICodePilot

AICodePilot is an AI coding assistant for codebase understanding and development workflows. It is designed as a hands-on LLM Agent project with tool calling, semantic retrieval, multiple model providers, a FastAPI backend, a React/Next.js frontend, Docker deployment, and complete engineering documentation.

Full title: **AICodePilot: LLM Agent based AI codebase understanding and development assistant**.

## Core Features ✨

- Codebase structure analysis and project file exploration.
- Safe local file reading and text search tools.
- Hand-written Agent execution loop with structured tool calling.
- RAG-based semantic code retrieval with file path and line references.
- Multi-provider LLM abstraction with OpenAI as the default and DeepSeek support.
- FastAPI service layer for Agent and project indexing APIs.
- Web UI for provider selection, project indexing, chat, tool-call timeline, and code references.
- Advanced development tools including log analysis, safe command execution, and patch suggestions.
- Docker and docker-compose deployment.

## Tech Stack 🧰

Backend:

- Python
- FastAPI
- Pydantic and pydantic-settings
- httpx
- pytest
- ruff, black, mypy

AI and retrieval:

- LLM API
- Tool Calling
- Prompt Engineering
- Embedding
- RAG
- Chroma vector database

Frontend:

- React
- Next.js
- Tailwind CSS
- shadcn/ui
- Monaco Editor for future code display

Deployment:

- Docker
- docker-compose
- `.env` based configuration

## Model Providers 🔁

AICodePilot uses OpenAI / ChatGPT by default:

```env
LLM_PROVIDER=openai
LLM_MODEL=gpt-5.2
```

DeepSeek is supported through the same provider abstraction:

```env
LLM_PROVIDER=deepseek
LLM_MODEL=deepseek-v4-pro
```

API requests may override the default provider and model per request.

## Roadmap 🗺️

1. Project initialization.
2. Mini Agent CLI with tool calling.
3. RAG code retrieval.
4. FastAPI backend APIs.
5. Web UI with provider and model selection.
6. Advanced Agent tools and memory.
7. Engineering quality, tests, linting, and typing.
8. Docker deployment.
9. Documentation and resume packaging.

## Quick Start 🚀

The project is being built phase by phase. The final local workflow will be:

```bash
cp .env.example .env
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m app.main
```

Run the FastAPI backend service:

```bash
cd backend
uvicorn app.main:app --reload
```

Then open:

```text
http://localhost:8000/docs
```

The final Docker workflow will be:

```bash
docker compose up --build
```


## Mini Agent CLI 🤖

Phase 1 provides a command-line Mini Agent with:

- OpenAI and DeepSeek provider abstraction.
- Structured JSON tool-calling protocol.
- Safe `list_files`, `read_file`, and `search_text` tools.
- Tool call recording and code reference extraction.

Run the CLI from the backend directory:

```bash
cd backend
python -m app.main --project-path ..
```

Example questions:

```text
List Python files in this project
Read README.md
Search FastAPI in this project
```

## RAG Code Retrieval 🔎

Phase 2 adds a local code retrieval loop:

- `ProjectIndexer` scans safe text/code files.
- `CodeChunker` creates line-based chunks with file and line metadata.
- `OpenAIEmbeddingClient` supports production embeddings.
- `LocalHashEmbeddingClient` supports offline tests and demos.
- `ChromaVectorStore` is the default vector database backend and persists code indexes under `VECTOR_STORE_PATH`.
- `retrieve_code` lets the Agent answer code location questions with references.

Example retrieval-oriented questions:

```text
Where is the Agent execution flow implemented?
Where is configuration loaded?
How is the tool registry implemented?
```

## FastAPI Backend APIs 🚀

Phase 3 exposes the Agent and RAG retrieval flow through FastAPI:

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/health` | Check service status |
| `POST` | `/api/chat` | Ask the Agent a codebase question |
| `POST` | `/api/projects/index` | Index a local project for retrieval |
| `POST` | `/api/projects/search` | Search indexed code chunks |

Example chat request:

```json
{
  "message": "Where is the API router implemented?",
  "project_path": "/path/to/project",
  "provider": "openai",
  "model": "gpt-5.2"
}
```

API requests can override the default provider/model per call. Full endpoint schemas, response examples, and error codes are documented in [API](docs/api.md).

## Web UI Progress 🖥️

Phase 4 currently provides a Next.js workspace with:

- OpenAI / DeepSeek provider and model selection.
- Typed API client for health, chat, project indexing, and project search.
- Agent chat workflow connected to `/api/chat`.
- Project indexing workflow connected to `/api/projects/index`.
- Tool call timeline for latest Agent responses.
- Dedicated code reference panel for paths, line numbers, snippets, and scores.

Run the frontend:

```bash
cd frontend
npm install
npm run dev
```

Open:

```text
http://127.0.0.1:3000
```

## Phase Validation ✅

At the end of each phase, AICodePilot runs a full project sanity check before moving forward:

- Verify the code structure still matches the planned Agent, tools, RAG, API, and docs layout.
- Run focused tests for the current phase and the full backend test suite.
- Validate runtime entrypoints such as CLI import, FastAPI app creation, OpenAPI schema, and health route.
- Update TodoList and related docs after validation passes.
- Commit and push the completed phase with a Conventional Commit message.

Phase 3 validation confirms the FastAPI backend exposes `/api/health`, `/api/chat`, `/api/projects/index`, and `/api/projects/search` without breaking the Mini Agent or RAG layers.

## Documentation 📚

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

## License 📄

This project is released under the MIT License. See [LICENSE](LICENSE).



