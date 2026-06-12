# Agent Design 🤖

The implementation intentionally hand-writes the Agent loop instead of depending on LangChain, CrewAI, AutoGen, or another large Agent framework. This keeps the tool-calling mechanism explicit, testable, and easy to explain.

## Goals 🎯

- Make tool calling explicit and explainable.
- Keep the execution loop small enough to discuss in interviews.
- Support multiple LLM providers through one interface.
- Keep codebase and filesystem operations constrained by safety checks.
- Return tool calls and references in a shape that the CLI, API, and UI can reuse.

## Provider Resolution 🔁

Agent requests may pass `provider` and `model`. If they are omitted, `LLM_PROVIDER` and the provider default model from settings are used. OpenAI is the default provider; DeepSeek is supported through the same `BaseLLMProvider` interface.

## Tool Calling — Native Function Calling (Primary Path) 🛠️

The primary execution path uses the OpenAI function-calling protocol (`chat_with_tools`). The model returns a structured `tool_calls` field instead of embedding JSON in the message text. This is more reliable than regex parsing and aligns with how Aider, Cline, and OpenHands operate.

```text
LLM.chat_with_tools(messages, tools) -> ChatResult(content, tool_calls)
AgentExecutor dispatches tool_calls directly — no regex needed
```

Providers that do not implement `chat_with_tools` fall back to the legacy text-protocol parser in `planner.py`.

### Loop Detection

Each step tracks a `(tool_name, frozen_args)` call signature. Identical back-to-back calls are detected and an error result is injected to steer the model toward a final answer.

## Text Protocol (Fallback Path Only)

When a provider raises `NotImplementedError` on `chat_with_tools`, the executor falls back to `_run_text_protocol_loop`. The model must respond with one of two JSON payloads:

```json
{"type":"action","tool":"search_text","arguments":{"keyword":"FastAPI"}}
```

```json
{"type":"final","answer":"clear professional answer"}
```

## Available Tools 📦

- `list_files(project_path)` — lists files under a project root, ignoring dependency/build dirs
- `read_file(file_path, project_path)` — reads UTF-8 text files with size and binary safeguards (max 512 KB)
- `project_tree(project_path)` — directory tree with depth/entry limits
- `find_files(project_path, pattern)` — glob-based file finder
- `search_text(project_path, keyword)` — text search returning file path, line number, matching line
- `retrieve_code(project_path, query, top_k)` — semantic code chunk retrieval (see RAG section)
- `analyze_log(log_text)` — log severity counting, exception extraction, traceback frames
- `run_command(command, cwd)` — restricted shell execution (allowlist only, gated by `ENABLE_SHELL_TOOL`)
- `propose_patch(file_path, updated_content)` — generates unified diff without writing any file

## Execution Flow 🔄

1. Receive user message, optional project path, provider, model.
2. Resolve provider and model from settings or request override.
3. Build messages: system prompt + prior memory turns + current user request.
4. Primary path: call `chat_with_tools` → dispatch `tool_calls` → append results in OpenAI multi-turn format.
5. Fallback path (no tool calling): text protocol via `planner.parse_agent_action`.
6. After budget or final answer, run `_clean_final_answer` and `_build_fallback_answer` if needed.
7. Call `_remember_turn(original_message, answer)` — stores only raw user text + final answer.
8. Return `AgentResponse(answer, provider, model, tool_calls, references, patch_suggestions)`.

## Conversation Memory 🧠

`SessionStore` (thread-safe, TTL + LRU) maps `conversation_id → ConversationMemory`. The HTTP layer is stateless; the session store keeps each conversation's bounded history alive between requests.

Memory stores only the user question and assistant final answer — tool-call payloads are excluded to prevent over-long prompts and avoid biasing the model into repeating previous tool calls.

The in-memory session store is complemented by **SQLite persistence** (`db/`): each user message and assistant answer is also written to `chat_messages` so history survives server restarts.

## SSE Streaming 📡

`AgentExecutor.run_stream()` yields `AgentEvent` objects:

| Event type | Data |
|---|---|
| `thinking` | `{"step": int}` |
| `tool_start` | `{"tool": str, "arguments": {...}}` |
| `tool_end` | `{"tool": str, "error": str\|null}` |
| `answer_delta` | `{"text": str}` — reserved for token streaming |
| `done` | full result + `conversation_id` |
| `error` | `{"detail": str}` |

See [streaming.md](streaming.md) for the full SSE event protocol.

## Patch Suggestions 🧩

`ProposePatchTool` reads the current file, computes a unified diff against `updated_content`, and returns the diff as an advisory `patch_suggestion`. The tool never writes to disk. The executor extracts suggestions from tool results and forwards them in `AgentResponse.patch_suggestions`.

## Log Analysis Tool 🧾

`AnalyzeLogTool` scans raw log text, counts severity levels, extracts exception names, captures Python traceback frames, and returns debugging recommendations. It is read-only and never executes shell commands.

## Safe Shell Tool 🛡️

`RunCommandTool` is gated by `ENABLE_SHELL_TOOL=true` (default `false`). It uses an explicit allowlist — not a blacklist — to reduce the attack surface:

- Allowed: `git:{status,log,diff,show,branch,remote,ls-files}`, `ls`, `cat`, `pwd`, `python/python3:{-m,--version,-V}`, `pytest`, `node:--version`, `npm:{run,test,ci,list}`, `ruff`, `mypy`, `black`
- Blocked by construction: `git push`, `python -c`, `rm`, `curl`, `pip install`, shell pipes/redirects/chaining.

## RAG Embedding Modes 🔍

Two embedding modes are available:

| Mode | Setting | Use case |
|---|---|---|
| **Local hash** (default) | `EMBEDDING_PROVIDER=local` | Offline, no API key needed, deterministic word-hash vectors |
| **OpenAI** | `EMBEDDING_PROVIDER=openai` | Semantic similarity, requires `OPENAI_API_KEY` |

Each project gets its own isolated Chroma collection (`acp_{folder}_{hash[:12]}`). The `IndexCache` skips re-indexing within a 5-minute TTL.

## API Integration 🌐

| Endpoint | Description |
|---|---|
| `POST /api/chat` | Synchronous agent run with multi-turn memory |
| `POST /api/chat/stream` | SSE streaming agent run |
| `GET /api/sessions/{id}/messages` | Retrieve persisted message history |
| `DELETE /api/sessions/{id}` | Delete session from DB and in-memory store |

## CLI Demo 💻

```bash
cd backend
python -m app.main --project-path ..
```

## Validation ✅

Agent validation includes schema tests, provider factory tests, tool tests, executor tests, API route tests, and full backend tests. The primary test suites cover: `test_executor_tool_calling.py`, `test_session_store.py`, `test_db_repository.py`, `test_patch_tools.py`, `test_shell_tools.py`.

