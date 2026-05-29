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

## Current Web Workflow 🖥️

Phase 4 now provides an interactive Next.js workspace:

1. Start the frontend with `npm run dev` in `frontend`.
2. Open `http://127.0.0.1:3000`.
3. Choose OpenAI or DeepSeek and select a model.
4. Enter a project path and index it.
5. Ask codebase questions in the Agent chat panel.
6. Review the latest tool call timeline.
7. Review code references returned by the Agent.

## Example Questions 💬

```text
Where is the Agent execution flow implemented?
Where is configuration loaded?
How is the tool registry implemented?
Which files define the FastAPI routes?
```
