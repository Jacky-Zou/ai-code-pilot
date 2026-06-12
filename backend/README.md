# AICodePilot Backend

The backend provides the Agent runtime, safe tool layer, RAG retrieval, model provider abstraction, and FastAPI service used by the AICodePilot workspace.

## Responsibilities

- Resolve OpenAI and DeepSeek providers through a shared factory.
- Run the handwritten Agent planner and executor.
- Execute safe tools for files, search, logs, shell commands, and patch suggestions.
- Build and search a local RAG index for backend-visible project paths.
- Expose HTTP APIs for chat, project indexing, project search, and health checks.

## Module Map

| Path | Purpose |
|---|---|
| `app/agent` | Planner, executor, prompts, schemas, and patch helpers |
| `app/api` | FastAPI routers and request/response schemas |
| `app/core` | Settings, logging, exceptions, and project path mapping |
| `app/llm` | Provider interface, HTTP client, OpenAI provider, DeepSeek provider |
| `app/memory` | Bounded conversation memory |
| `app/rag` | Project scanning, chunking, embeddings, vector store, retriever |
| `app/tools` | Safe tool implementations and registry |
| `tests` | Backend regression tests |

## Setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Create `.env` from the repository root `.env.example` and add real API keys only to `.env`.

## Run

```bash
uvicorn app.main:app --reload
```

Open:

```text
http://localhost:8000/docs
```

## API Endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/health` | Service health |
| `POST` | `/api/chat` | Agent chat request (supports per-request `api_key` / `provider` / `model`) |
| `POST` | `/api/chat/stream` | Streaming agent run as Server-Sent Events |
| `POST` | `/api/providers/models` | Discover the models a provider API key can use |
| `POST` | `/api/projects/index` | Build RAG index and return project summary metadata |
| `POST` | `/api/projects/search` | Search indexed code chunks |
| `GET` | `/api/sessions/{id}/messages` | Fetch persisted conversation history |
| `DELETE` | `/api/sessions/{id}` | Delete a conversation session |

### Bring-your-own-key

The frontend stores provider API keys in the browser and sends them per request. The backend
applies them transiently (never logged or persisted) and falls back to `.env` when absent. See
[../docs/model-discovery.md](../docs/model-discovery.md).

## Validation

```bash
pytest backend/tests
ruff check .
black --check .
mypy backend/app
```

## Security Boundaries

- API keys are loaded from environment variables and are never hardcoded.
- File tools restrict access to the declared project root.
- Binary and oversized files are rejected before reading.
- Shell execution blocks destructive commands and shell control operators.
- Patch generation produces reviewable diffs without mutating files.
