# Architecture

AICodePilot uses a frontend/backend separated architecture. The backend exposes Agent and project APIs through FastAPI, while the frontend provides project indexing, chat, provider selection, tool-call tracing, and code reference views.

## Modules

- Web Frontend: React / Next.js UI.
- FastAPI Backend: HTTP API, validation, exception handling.
- Agent Core: prompt construction, action parsing, tool execution, answer synthesis.
- LLM Provider Layer: OpenAI and DeepSeek adapters behind a common interface.
- Tools Layer: file listing, file reading, text search, and later advanced developer tools.
- RAG Engine: project scanning, chunking, embedding, vector store, retrieval.
- Local Codebase: files and logs selected by the user.

## Initial Data Flow

User request -> API or CLI -> Agent -> LLM Provider -> Tool Registry -> Tools/RAG -> Agent summary -> response.
