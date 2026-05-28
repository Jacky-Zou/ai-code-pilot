# Architecture

AICodePilot uses a frontend/backend separated architecture. The backend exposes Agent and project APIs through FastAPI, while the frontend provides project indexing, chat, provider selection, tool-call tracing, and code reference views.

## Modules

- Web Frontend: React / Next.js UI.
- FastAPI Backend: HTTP API, validation, exception handling.
- Agent Core: prompt construction, action parsing, tool execution, answer synthesis.
- LLM Provider Layer: OpenAI and DeepSeek adapters behind a common interface.
- Tools Layer: file listing, file reading, text search, and RAG retrieval tools.
- RAG Engine: project scanning, line chunking, embedding, vector storage, and Top-K retrieval.
- Local Codebase: files and logs selected by the user.

## Current Data Flow

User request -> CLI Agent -> provider/model resolution -> LLM action planning -> Tool Registry -> file/search/RAG tool -> tool result -> LLM summary -> answer with tool calls and references.

## Agent Flow

1. Receive `message`, optional `project_path`, `provider`, and `model`.
2. Resolve provider and model from request or settings.
3. Build a system prompt containing available tool schemas.
4. Ask the LLM for structured JSON.
5. Execute the requested tool through `ToolRegistry`.
6. Send tool output back to the LLM.
7. Return `answer`, `provider`, `model`, `tool_calls`, and `references`.

## RAG Flow

1. `ProjectIndexer` scans safe text/code files.
2. `CodeChunker` produces line-based chunks.
3. Embedding client converts chunks and queries into vectors.
4. `VectorStore` stores vectors plus chunk metadata.
5. `CodeRetriever` searches Top-K relevant chunks.
6. `retrieve_code` exposes retrieval to the Agent.

## Model Defaults

The default OpenAI model is `gpt-5.2` because current official OpenAI model documentation does not list a `gpt-5.5` API model. The default DeepSeek model is `deepseek-v4-pro`.
