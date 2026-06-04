# AICodePilot API

Phase 3 exposes the Agent and RAG retrieval capabilities through a FastAPI service. The service is intentionally small for now: one health endpoint, one Agent chat endpoint, and two project retrieval endpoints.

## Quick Start 🚀

Start the backend from the `backend` directory:

```bash
cd backend
uvicorn app.main:app --reload
```

Open the interactive API documentation:

```text
http://localhost:8000/docs
```

The OpenAPI schema is available at:

```text
http://localhost:8000/openapi.json
```

## Endpoint Summary 📌

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/health` | Check whether the backend service is running |
| `POST` | `/api/chat` | Ask the Agent a codebase question |
| `POST` | `/api/projects/index` | Build or refresh the RAG index for a local project |
| `POST` | `/api/projects/search` | Search the current project index for relevant code chunks |

## Health Check

```http
GET /api/health
```

Response:

```json
{
  "status": "ok",
  "service": "AICodePilot"
}
```

## Agent Chat 🤖

```http
POST /api/chat
Content-Type: application/json
```

Request:

```json
{
  "message": "Where is the API router implemented?",
  "project_path": "/path/to/project",
  "provider": "openai",
  "model": "gpt-5.2"
}
```

Fields:

| Field | Required | Description |
|---|---|---|
| `message` | Yes | User question or development task. Must not be empty. |
| `project_path` | No | Local project path available to Agent tools. |
| `provider` | No | LLM provider override, such as `openai` or `deepseek`. |
| `model` | No | Model override for the selected provider. |

Provider selection follows the project rules:

1. Request `provider` overrides `.env` `LLM_PROVIDER`.
2. Missing request `provider` falls back to `.env`.
3. Request `model` overrides the provider default model.
4. Missing request `model` falls back to the provider default.

Response:

```json
{
  "answer": "The API router is implemented in backend/app/api/routes_chat.py.",
  "provider": "openai",
  "model": "gpt-5.2",
  "tool_calls": [
    {
      "name": "search_text",
      "arguments": {
        "keyword": "router"
      },
      "result": {
        "matches": 1
      },
      "error": null
    }
  ],
  "references": [
    {
      "file_path": "backend/app/api/routes_chat.py",
      "line_number": 1,
      "snippet": "router = APIRouter",
      "score": null
    }
  ]
}
```

## Project Index

```http
POST /api/projects/index
Content-Type: application/json
```

Request:

```json
{
  "project_path": "/path/to/project"
}
```

Response:

```json
{
  "status": "success",
  "indexed_files": 32,
  "chunks": 128,
  "project_name": "AICodePilot",
  "project_path": "/workspace/AICodePilot",
  "size_bytes": 420000,
  "line_count": 12500,
  "languages": [
    {
      "label": "Python",
      "files": 42,
      "percent": 53
    },
    {
      "label": "TypeScript",
      "files": 18,
      "percent": 23
    }
  ],
  "tech_stack": ["Python", "FastAPI", "React", "Next.js", "RAG", "LLM Agent"],
  "architecture": ["Backend service layer", "Frontend workspace application", "Agent planner/executor core"],
  "structure": ["backend/ (40 files)", "frontend/ (24 files)", "docs/ (9 files)"],
  "summary": "AICodePilot contains 32 indexed source/documentation files and 128 retrieval chunks.",
  "likely_purpose": "This project appears to be organized for codebase analysis, development assistance, API services, and documentation workflows."
}
```

Notes:

- `project_path` must be a non-empty string.
- The backend scans safe text/code files and ignores irrelevant directories.
- Chunks are stored in the configured vector store path.
- Project summary metadata is deterministic and does not require an additional LLM call.

## Project Search

```http
POST /api/projects/search
Content-Type: application/json
```

Request:

```json
{
  "query": "FastAPI router wiring",
  "top_k": 5
}
```

Fields:

| Field | Required | Description |
|---|---|---|
| `query` | Yes | Semantic search query. Must not be empty. |
| `top_k` | No | Number of chunks to return. Defaults to `5`; allowed range is `1` to `20`. |

Response:

```json
{
  "results": [
    {
      "file_path": "backend/app/main.py",
      "start_line": 8,
      "end_line": 20,
      "content": "app = create_app()",
      "score": 0.88
    }
  ]
}
```

## Error Responses ⚠️

All Phase 3 API errors use a consistent JSON shape:

```json
{
  "error": "ValidationError",
  "code": "VALIDATION_ERROR",
  "detail": []
}
```

When callers send `X-Request-ID`, the same value is included in the error
response as `request_id` so logs and API responses can be correlated.

Common status codes:

| Status | Error | When it happens |
|---|---|---|
| `400` | `UnsupportedProviderError` | Request selects an unsupported LLM provider |
| `400` | `ToolError` | A file, search, or retrieval tool rejects the request |
| `400` | `AICodePilotError` | Generic domain error |
| `422` | `ValidationError` | Request body fails Pydantic validation |
| `500` | `ConfigurationError` | Required backend configuration is missing or invalid |
| `502` | `LLMProviderError` | Upstream LLM provider call fails |

Validation error example:

```json
{
  "error": "ValidationError",
  "code": "VALIDATION_ERROR",
  "detail": [
    {
      "type": "string_too_short",
      "loc": ["body", "message"],
      "msg": "String should have at least 1 character",
      "input": "",
      "ctx": {
        "min_length": 1
      }
    }
  ]
}
```

Provider error example with request correlation:

```json
{
  "error": "LLMProviderError",
  "code": "LLM_PROVIDER_ERROR",
  "detail": "LLM provider returned HTTP 500",
  "request_id": "req-123"
}
```

## Testing 🧪

Run the API integration tests:

```bash
python -m pytest backend/tests/test_api.py
```

Run the full backend test suite with an isolated Chroma path:

```powershell
$env:VECTOR_STORE_PATH='C:\Users\zouhuancan\AppData\Local\Temp\aicodepilot_pytest_vector_store'
python -m pytest backend/tests
```
