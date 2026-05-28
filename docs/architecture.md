# Architecture 🏗️

AICodePilot uses a frontend/backend separated architecture. The backend exposes Agent and project APIs through FastAPI, while the frontend will provide project indexing, chat, provider selection, tool-call tracing, and code reference views.

## Modules 🧩

- Web Frontend: React / Next.js UI planned for Phase 4.
- FastAPI Backend: HTTP API, request validation, exception handling, and OpenAPI docs.
- Agent Core: prompt construction, action parsing, tool execution, and answer synthesis.
- LLM Provider Layer: OpenAI and DeepSeek adapters behind a common interface.
- Tools Layer: file listing, file reading, text search, and RAG retrieval tools.
- RAG Engine: project scanning, line chunking, embedding, Chroma vector storage, and Top-K retrieval.
- Local Codebase: files and logs selected by the user.

## Current Data Flow 🔄

CLI flow:

```text
User request -> CLI Agent -> provider/model resolution -> LLM action planning
-> Tool Registry -> file/search/RAG tool -> tool result -> LLM summary
-> answer with tool calls and references
```

API flow:

```text
HTTP request -> FastAPI router -> Pydantic validation -> Agent or Retriever service
-> unified response model -> JSON response
```

## Agent Flow 🤖

1. Receive `message`, optional `project_path`, `provider`, and `model`.
2. Resolve provider and model from request or settings.
3. Build a system prompt containing available tool schemas.
4. Ask the LLM for structured JSON.
5. Execute the requested tool through `ToolRegistry`.
6. Send tool output back to the LLM.
7. Return `answer`, `provider`, `model`, `tool_calls`, and `references`.

## RAG Flow 🔎

1. `ProjectIndexer` scans safe text/code files.
2. `CodeChunker` produces line-based chunks.
3. Embedding client converts chunks and queries into vectors.
4. `ChromaVectorStore` stores vectors plus chunk metadata under `VECTOR_STORE_PATH`.
5. `CodeRetriever` searches Top-K relevant chunks.
6. `retrieve_code` exposes retrieval to the Agent.

## FastAPI Flow 🌐

Phase 3 adds these backend endpoints:

- `GET /api/health`
- `POST /api/chat`
- `POST /api/projects/index`
- `POST /api/projects/search`

`backend/app/main.py` creates the FastAPI application, registers unified exception handlers, includes chat/project routers, and keeps the CLI entrypoint available through `python -m app.main`.

## Model Defaults 🔁

The default OpenAI model is `gpt-5.2` because current official OpenAI model documentation does not list a `gpt-5.5` API model. The default DeepSeek model is `deepseek-v4-pro`.

## Phase Validation ✅

Each phase ends with a full sanity check across structure, runtime entrypoints, tests, TodoList state, and documentation. Phase 3 validation must prove that the FastAPI layer did not break the existing handwritten Agent, provider abstraction, safe tools, or RAG retrieval flow.
