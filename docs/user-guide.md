# User Guide

AICodePilot helps developers understand unfamiliar codebases, search project content, ask code questions, inspect tool calls, and review code references.

## Current Backend Workflow

Phase 3 provides a FastAPI backend:

1. Start the backend with `uvicorn app.main:app --reload`.
2. Open `http://localhost:8000/docs`.
3. Check `/api/health`.
4. Index a local project with `/api/projects/index`.
5. Ask codebase questions through `/api/chat`.
6. Search indexed code chunks through `/api/projects/search`.

## Current Web Workflow

Phase 4 provides an interactive Next.js workspace connected to the FastAPI backend:

1. Start the backend from `backend`:

```bash
uvicorn app.main:app --reload
```

2. Start the frontend from `frontend`:

```bash
npm install
npm run dev
```

3. Open `http://127.0.0.1:3000`.
4. Choose OpenAI or DeepSeek and select a model.
5. Enter a backend-visible project path and index it.
6. Ask codebase questions in the Agent chat panel.
7. Review the latest Agent steps.
8. Review code evidence returned by the Agent.

## Project Paths in Docker

When running with Docker, the browser is on Windows but the backend runs inside a Linux container.
The backend cannot read arbitrary Windows paths unless they are mounted into the container.

Set these values in `.env`:

```env
PROJECTS_HOST_ROOT=D:/code/my_projects
PROJECTS_CONTAINER_ROOT=/workspace
NEXT_PUBLIC_DEFAULT_PROJECT_PATH=/workspace
```

Then either enter a host path under `PROJECTS_HOST_ROOT`, such as
`D:/code/my_projects/AI_Projects/AICodePilot`, or enter the mapped container path,
such as `/workspace/AI_Projects/AICodePilot`.

## Frontend Panels

- **Agent Chat**: sends the current question, project path, provider, and model to `/api/chat`.
- **Codebase Index**: submits a backend-visible project path to `/api/projects/index` before retrieval-heavy questions.
- **Provider Selector**: lets each request use OpenAI or DeepSeek without changing backend code.
- **Agent Steps**: shows the latest tools selected by the Agent as readable actions and outcomes.
- **Code Evidence**: lists referenced files, line numbers, snippets, explanations, and retrieval scores.

## Configuration

The frontend reads `NEXT_PUBLIC_API_BASE_URL` when provided:

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

If the variable is not set, the UI calls `http://localhost:8000` by default.

## Recommended Flow

1. Index the project first when asking location or architecture questions.
2. Keep provider/model choices aligned with configured backend API keys.
3. Use Agent steps to confirm whether the Agent searched files, read files, or used RAG retrieval.
4. Use code evidence as navigation hints, then open the referenced file in the editor for detailed review.

## Example Questions

```text
Where is the Agent execution flow implemented?
Where is configuration loaded?
How is the tool registry implemented?
Which files define the FastAPI routes?
```
