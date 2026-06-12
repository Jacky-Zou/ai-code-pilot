# Resume Guide 💼

AICodePilot is a resume-ready AI engineering project that demonstrates a production-oriented handwritten Agent loop with persistent memory, native tool calling, SSE streaming, RAG retrieval, and a FastAPI + Next.js full-stack integration.

## Draft Project Entry 📝

AICodePilot: LLM Agent based AI codebase understanding and development assistant.

Tech stack: Python, FastAPI, React, Next.js, LLM API, native tool calling (OpenAI function-calling format), RAG with Chroma vector store, SSE streaming, SQLite persistence, pytest.

## Delivered Capabilities ✅

- Handwritten ReAct Agent loop with native tool_calls (no LangChain dependency).
- OpenAI and DeepSeek provider abstraction; falls back to text-protocol for providers without function calling.
- Thread-safe `SessionStore` (TTL + LRU) for multi-turn conversation memory.
- SQLite persistence via SQLModel — conversation and message history survives restarts.
- SSE streaming endpoint (`/api/chat/stream`) with per-step events (thinking, tool_start, tool_end, done, error).
- Safe tool layer: file ops, semantic search (Chroma), log analysis, propose_patch (diff-only, no writes).
- Shell tool gated by `ENABLE_SHELL_TOOL` with explicit command allowlist — not a blacklist.
- RAG with per-project index isolation (`IndexCache` + Chroma collection per project).
- Default embedding mode: **offline local hash** (no API key needed); upgradeable to OpenAI semantic embeddings via `EMBEDDING_PROVIDER=openai`.
- Patch suggestions: `propose_patch` tool generates reviewable unified diffs without modifying any file.
- 248+ tests, ruff + black + mypy enforced, full CI gates.

