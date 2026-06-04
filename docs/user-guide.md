# User Guide

AICodePilot helps developers inspect unfamiliar projects, ask codebase questions, search implementation details, review Agent tool calls, and inspect the code evidence used in each answer.

## 🚀 Start The App

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

Open the web workspace:

```text
http://127.0.0.1:3000
```

## 🧭 Workspace Layout

The interface uses a three-column engineering workspace:

- **Left rail**: Model Provider and Workspace management.
- **Center**: Agent Chat with quick actions, Markdown answers, code blocks, and the message composer.
- **Right rail**: Agent Steps and Code Evidence for the latest response.

Each panel has bounded scrolling so long messages, tool results, paths, and snippets stay inside their own surfaces.

## 🧠 Model Provider

The Model Provider panel is always visible in the left rail. It contains:

- Provider dropdown.
- Model dropdown.
- Capability cards for the selected provider.

Available real backend providers:

| Provider | Model | Status |
|---|---|---|
| DeepSeek | `deepseek-v4-pro` | Available |
| OpenAI | `gpt-5.2` | Available |

Planned providers such as GLM, Qwen, and Claude are shown as disabled future integration targets.

## 📁 Workspace Management

The Workspace panel supports three related workflows:

1. **Open folder**: select a local project folder in the browser, validate file extensions, build a tree preview, and show a local import summary.
2. **Open file**: select a single supported code file, validate its extension, and show file size and line count in the summary modal.
3. **Index codebase**: send a backend-visible path to `/api/projects/index` so the backend can build the RAG index.

Supported file extensions include:

```text
.c .cpp .css .go .html .java .js .json .jsx .md .py .rs .scss .sh .ts .tsx .txt .yaml .yml
```

Unsupported files such as `.doc`, `.docx`, `.pdf`, and `.exe` are blocked before import. The UI shows a modal explaining that the selected format is not supported.

## 🐳 Docker Path Rules

When running with Docker, the browser runs on the host machine while the backend runs inside a Linux container. Browser folder import can preview local metadata, but backend indexing requires a path visible to the backend container.

Use these environment variables to mount host projects into the backend:

```env
PROJECTS_HOST_ROOT=D:/code/my_projects
PROJECTS_CONTAINER_ROOT=/workspace
NEXT_PUBLIC_DEFAULT_PROJECT_PATH=/workspace
```

Then enter either:

```text
D:/code/my_projects/AI_Projects/AICodePilot
```

or:

```text
/workspace/AI_Projects/AICodePilot
```

## 💬 Chat Workflow

1. Select a supported provider and model.
2. Open a project folder or code file if you want a frontend preview.
3. Enter a backend-visible project path.
4. Click **Index codebase**.
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

## 🧩 Quick Actions

When the chat is empty, quick action cards appear in the conversation area. They replace the previous standalone capability entry panel and keep suggested workflows close to the chat context.

Current quick action categories:

- Architecture analysis.
- Bug investigation.
- Test generation.
- Documentation drafting.

## 🔎 Agent Steps

The right-side Agent Steps panel shows a collapsible timeline for the latest request:

- Thinking state while a request is running.
- Tool call entries such as `search_text`, `read_file`, `project_tree`, or `retrieve_code`.
- Tool outcomes such as match counts, returned chunks, or errors.

The current backend returns request results after completion. The UI mirrors active request state and final tool calls, while true token-level streaming remains a future enhancement.

## 📌 Code Evidence

The Code Evidence panel shows the concrete files and snippets used by the Agent answer:

- File path.
- Line number when available.
- Highlighted code snippet.
- Copy action for each snippet.

Evidence cards are intentionally compact and bounded to keep long file paths and code lines from breaking the layout.

## 👤 Account UI

The current login, registration, profile, captcha, avatar upload, password reset, and session flows are frontend-local product mocks. They are useful for validating the application experience, but they are not a production authentication system yet.

## 🌗 Theme

The UI supports light and dark themes. Light mode is the default. Theme preference is stored in browser `localStorage`.

## ⚠️ Current Boundaries

- Browser file import cannot grant backend access to arbitrary local files.
- Real backend authentication is not implemented yet.
- GLM, Qwen, Claude, Gemini, Moonshot, and other providers need backend provider modules before they can send real model requests.
- Streaming Agent step updates are represented by request state today and require backend SSE or WebSocket support for true real-time updates.
