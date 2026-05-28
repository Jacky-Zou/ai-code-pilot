# Agent Design 🤖

The first implementation intentionally hand-writes the Agent loop instead of depending on LangChain, CrewAI, AutoGen, or another large Agent framework. This keeps the tool-calling mechanism explicit, testable, and easy to explain.

## Goals 🎯

- Make tool calling explicit and explainable.
- Keep the execution loop small enough to discuss in interviews.
- Support multiple LLM providers through one interface.
- Keep codebase and filesystem operations constrained by safety checks.
- Return tool calls and references in a shape that the CLI, API, and future UI can reuse.

## Provider Resolution 🔁

Agent requests may pass `provider` and `model`. If they are omitted, `LLM_PROVIDER` and the provider default model from settings are used. OpenAI is the default provider and DeepSeek is supported by the same `BaseLLMProvider` interface.

## Tool Calling Protocol 🛠️

The LLM must respond with one of two JSON payloads:

```json
{"type":"action","tool":"search_text","arguments":{"keyword":"FastAPI"}}
```

```json
{"type":"final","answer":"clear professional answer"}
```

The executor parses the JSON, dispatches tool actions through `ToolRegistry`, records the result, and asks the LLM for a final summary.

## Available Tools 📦

- `list_files(project_path)`: lists files under a project root while ignoring dependency/build directories.
- `read_file(file_path, project_path)`: reads UTF-8 text files inside the project root with size and binary safeguards.
- `search_text(project_path, keyword)`: recursively searches text files and returns file paths, line numbers, and matching lines.
- `retrieve_code(project_path, query, top_k)`: retrieves semantic code chunks with path, line range, content, and score.

## Execution Flow 🔄

1. Receive user task and optional project path/provider/model.
2. Resolve provider and model.
3. Build system prompt with available tool descriptions.
4. Ask the LLM for either a final answer or structured JSON action.
5. Parse action and dispatch to Tool Registry.
6. Execute tool and record result.
7. Send tool result back to LLM for final answer.
8. Return answer, provider, model, tool calls, and references.

## API Integration 🌐

Phase 3 exposes the same Agent through `POST /api/chat`. The API layer does not bypass the Agent loop; it validates the request, passes through `message`, `project_path`, `provider`, and `model`, then returns `answer`, `tool_calls`, and `references`.

## CLI Demo 💻

```bash
cd backend
python -m app.main --project-path ..
```

The CLI starts an interactive loop. Without a configured API key, provider calls return a clear configuration error instead of attempting an unauthenticated request.

## Validation ✅

Agent validation includes schema tests, provider factory tests, tool tests, executor tests, API route tests, and full backend tests at phase completion. This guards against turning the project into a generic chatbot and keeps the focus on codebase understanding and development workflows.
