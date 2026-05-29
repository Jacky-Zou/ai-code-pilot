# Security 🔐

AICodePilot operates on local projects, so file access, command execution, model calls, memory, and patch suggestions must stay explicit and constrained. The security model favors read-only analysis, bounded context, and user-reviewed changes.

## File Access 🗂️

File tools protect the local workspace:

- Validate project paths and file paths before use.
- Prevent path traversal outside the declared project root.
- Limit file size before reading content.
- Avoid reading binary files.
- Return explicit domain errors instead of raw tracebacks.

## API Keys 🗝️

Provider credentials must stay out of source control:

- Store credentials in `.env`.
- Track only `.env.example` with placeholders.
- Never print API keys in logs, docs, test output, or model prompts.
- Let missing keys raise clear configuration errors.

## API Validation 🌐

FastAPI and Pydantic validate request bodies. Domain errors and validation errors use a consistent shape:

```json
{
  "error": "ValidationError",
  "detail": []
}
```

This keeps frontend handling predictable and prevents raw tracebacks from becoming the user-facing API contract.

## Conversation Memory 🧠

Conversation memory is bounded and in-process:

- `ConversationMemory` stores only recent user, assistant, and tool messages.
- History is trimmed by complete user turns, not unbounded token growth.
- System prompts are not stored in rolling memory; they are prepended fresh for each request.
- Memory is optional in `AgentExecutor`, so stateless usage remains available.

## Log Analysis 🧾

`analyze_log(log_text)` is read-only:

- It analyzes only the provided text.
- It does not open log files by path.
- It does not execute commands.
- It extracts severity counts, likely exceptions, traceback frames, and recommendations.

## Shell Execution 🛡️

`run_command(command, cwd)` is intentionally restricted:

- Commands run with `shell=False`.
- `cwd` must stay inside `project_path` when a project root is provided.
- Destructive commands such as `rm`, `del`, `format`, `shutdown`, and related aliases are blocked.
- Shell chaining, pipes, redirects, command substitution, and script download/execute patterns are blocked.
- Output is captured as `stdout`, `stderr`, `exit_code`, timeout seconds, and timeout state.
- Windows command parsing preserves executable paths and quoted arguments without invoking a shell.

## Patch Suggestions 🧩

Patch generation is advisory only:

- `generate_patch_suggestion` compares in-memory original and updated text.
- It returns unified diff strings for user review.
- It rejects absolute paths and parent-directory targets.
- It never writes files or applies patches automatically.

## Tool Registry Boundaries 🧰

The default `ToolRegistry` exposes file, search, retrieval, log analysis, and safe shell tools. Agent execution still follows the same protocol:

1. The LLM selects a structured tool action.
2. The executor validates and dispatches through the registry.
3. Tool results are recorded and summarized.
4. Patch suggestions are forwarded but not applied.

## Phase Checks ✅

Every phase completion includes tests and documentation review to ensure new capabilities do not weaken existing file, provider, RAG, API, shell, memory, or patch-suggestion boundaries.
