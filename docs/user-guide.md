# User Guide

AICodePilot helps developers inspect unfamiliar projects, ask codebase questions, search implementation details, review Agent tool calls, and inspect code evidence.

## Start The App

Start the backend:

```bash
cd backend
uvicorn app.main:app --reload
```

Start the frontend:

```bash
cd frontend
npm install
npm run dev
```

For production-mode local review after UI changes:

```bash
cd frontend
npm run start:fresh
```

Open:

```text
http://127.0.0.1:3000
```

## Workspace Layout

The interface uses a three-column engineering workspace:

- **Left rail**: Model Center and Workspace management.
- **Center**: Agent Chat with quick actions, Markdown answers, code blocks, and the message composer.
- **Right rail**: Agent Steps and Code Evidence for the latest response.

Each panel has bounded scrolling so long messages, tool results, paths, and snippets stay inside their own surfaces.

## Model Center

The Model Center supports:

- Domestic and global provider source tabs.
- Provider cards with logo marks and provider descriptions.
- Model selection for the selected provider.
- Disabled roadmap providers for Qwen, GLM, Claude, Gemini, and Moonshot.

Available real backend providers:

| Provider | Model | Status |
|---|---|---|
| DeepSeek | `deepseek-v4-pro` | Available |
| OpenAI | `gpt-5.2` | Available |

## Workspace Management

The Workspace panel supports three workflows:

1. **Open folder**: select a local project folder in the browser, validate extensions, build a tree preview, and show a local Project Summary modal.
2. **Open file**: select a single supported code file, validate its extension, and show file size and line count in the Project Summary modal.
3. **Index workspace**: send a backend-visible path to `/api/projects/index` so the backend can build the RAG index and return project summary metadata.

Supported file extensions:

```text
.c .cpp .css .go .html .java .js .json .jsx .md .py .rs .scss .sh .ts .tsx .txt .yaml .yml
```

Unsupported files such as `.doc`, `.docx`, `.pdf`, `.exe`, archives, and binary files are blocked before import.

## Project Summary

The Project Summary modal is designed to confirm that import or indexing succeeded and to orient the user before chatting with the Agent.

It displays:

- Project or file name.
- Backend-visible path when available.
- File count.
- Project size.
- Code line count.
- RAG chunk count.
- Programming language composition and percentages.
- Technology stack.
- High-level architecture.
- Top-level structure.
- A concise project purpose summary.

For browser folder/file import, metadata is computed in the browser. For backend path indexing, metadata is returned by the FastAPI project index endpoint.

## Docker Path Rules

When running with Docker, the browser runs on the host machine while the backend runs inside a Linux container. Browser folder import can preview local metadata, but backend indexing requires a path visible to the backend container.

Use these environment variables:

```env
PROJECTS_HOST_ROOT=D:/code/my_projects
PROJECTS_CONTAINER_ROOT=/workspace
NEXT_PUBLIC_DEFAULT_PROJECT_PATH=/workspace
```

Then enter either a host path under `PROJECTS_HOST_ROOT` or the mapped container path under `/workspace`.

## Chat Workflow

1. Select a supported provider and model.
2. Open a project folder or code file if you want a local preview.
3. Enter a backend-visible project path.
4. Click **Index workspace**.
5. Ask a codebase question in Agent Chat.
6. Use `Shift + Enter` for line breaks and `Enter` to send.
7. Review the final answer, Agent Steps, and Code Evidence.

Recommended questions:

```text
Where is the Agent execution flow implemented?
Where is configuration loaded?
How is the tool registry implemented?
Which files define the FastAPI routes?
Analyze this error log and suggest a fix.
Generate tests for the Agent executor.
```

## Agent Steps

The right-side Agent Steps panel shows the latest request state:

- Waiting state when no request is active.
- Thinking state while the request is running.
- Tool-call entries after the backend returns executed tools.
- Outcome summaries such as match counts, returned chunks, or errors.

The current backend returns results after completion. True token-level streaming remains a roadmap item.

## Code Evidence

The Code Evidence panel shows:

- File path.
- Line number when available.
- Highlighted code snippet.
- Copy action for each snippet.

## Account UI

The current login, registration, profile, captcha, avatar upload, password reset, and session flows are frontend-local product mocks. They validate the product workflow but are not production authentication.

## Theme

The UI supports light and dark themes. Light mode is the default. Theme preference is stored in browser `localStorage`.

## Current Boundaries

- Browser file import cannot grant backend access to arbitrary local files.
- Real backend authentication is not implemented yet.
- Qwen, GLM, Claude, Gemini, Moonshot, and other providers require backend provider modules before real model calls.
- Streaming Agent step updates require backend SSE or WebSocket support.
