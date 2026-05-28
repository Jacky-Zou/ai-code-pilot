# User Guide 🧭

AICodePilot helps developers understand unfamiliar codebases, search project content, ask code questions, inspect tool calls, and review code references.

## Current Backend Workflow 🌐

Phase 3 provides a FastAPI backend:

1. Start the backend with `uvicorn app.main:app --reload`.
2. Open `http://localhost:8000/docs`.
3. Check `/api/health`.
4. Index a local project with `/api/projects/index`.
5. Ask codebase questions through `/api/chat`.
6. Search indexed code chunks through `/api/projects/search`.

## Planned Web Workflow 🖥️

1. Select model provider and model.
2. Enter a project path.
3. Index the project.
4. Ask codebase questions.
5. Review tool calls and referenced code snippets.

## Example Questions 💬

```text
Where is the Agent execution flow implemented?
Where is configuration loaded?
How is the tool registry implemented?
Which files define the FastAPI routes?
```
