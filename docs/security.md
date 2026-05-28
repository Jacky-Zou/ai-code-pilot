# Security 🔐

AICodePilot operates on local projects, so file access, command execution, model calls, and API key handling must stay explicit and constrained.

## File Access 🗂️

- Validate project paths and file paths.
- Prevent path traversal outside the project root.
- Limit file size.
- Avoid reading binary files.
- Return explicit errors instead of leaking sensitive details.

## API Keys 🗝️

- Store credentials in `.env`.
- Track only `.env.example` with placeholders.
- Never print API keys in logs or docs.
- Let missing keys raise clear configuration errors.

## API Validation 🌐

Phase 3 uses FastAPI and Pydantic to validate request bodies. Domain errors and validation errors are returned with a consistent shape:

```json
{
  "error": "ValidationError",
  "detail": []
}
```

This keeps frontend handling predictable and prevents raw tracebacks from becoming the user-facing API contract.

## Shell Execution 🧯

The shell tool is added later and must block destructive commands, restrict cwd, capture output, and enforce timeouts.

## Phase Checks ✅

Every phase completion includes tests and documentation review to ensure new capabilities do not weaken existing file, provider, RAG, or API safety boundaries.
