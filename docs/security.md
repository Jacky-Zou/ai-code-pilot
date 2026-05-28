# Security

AICodePilot operates on local projects, so file and command safety are core requirements.

## File Access

- Validate project paths and file paths.
- Prevent path traversal outside the project root.
- Limit file size.
- Avoid reading binary files.
- Return explicit errors instead of leaking sensitive details.

## API Keys

- Store credentials in `.env`.
- Track only `.env.example` with placeholders.
- Never print API keys in logs or docs.

## Shell Execution

The shell tool is added later and must block destructive commands, restrict cwd, capture output, and enforce timeouts.
