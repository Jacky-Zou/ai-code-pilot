# User Guide

AICodePilot helps developers understand unfamiliar codebases, search project content, ask code questions, inspect Agent steps, and review code evidence.

## Backend Workflow

The FastAPI backend provides:

1. `GET /api/health`
2. `POST /api/chat`
3. `POST /api/projects/index`
4. `POST /api/projects/search`

Start it locally from `backend`:

```bash
uvicorn app.main:app --reload
```

Open API docs at:

```text
http://localhost:8000/docs
```

## Web Workspace

Start the frontend from `frontend`:

```bash
npm install
npm run dev
```

Open:

```text
http://127.0.0.1:3000
```

The UI is organized as a three-column engineering workspace:

- **Left rail**: Model Hub, Codebase Import, and future Agent capability shortcuts.
- **Center**: Agent Chat with Markdown rendering, code highlighting, avatars, and multiline input.
- **Right rail**: Agent Steps and Code Evidence for the latest response.

## Model Hub

The Model Hub has two tabs:

- **Domestic**: DeepSeek V4-Pro is available and selected by default. DeepSeek V4-Flash, GLM-4.6, Qwen3.6 Plus, and Qwen3 Coder Plus are shown as coming-soon options.
- **Global**: GPT-5.2 is available through the OpenAI provider. GPT-4o and Claude options are shown as coming-soon options.

Current backend provider support is limited to OpenAI and DeepSeek. Coming-soon cards are disabled until their backend provider modules are implemented.

## Codebase Import

There are two ways to prepare a project:

1. **Open local folder**: uses browser folder authorization to scan file names, infer a local language mix, and show a Project Summary preview.
2. **Backend-visible path**: sends a path to the backend for real RAG indexing through `/api/projects/index`.

When running with Docker, the browser is on Windows but the backend runs inside a Linux container. Set these values in `.env`:

```env
PROJECTS_HOST_ROOT=D:/code/my_projects
PROJECTS_CONTAINER_ROOT=/workspace
NEXT_PUBLIC_DEFAULT_PROJECT_PATH=/workspace
```

Then either enter a host path under `PROJECTS_HOST_ROOT`, such as:

```text
D:/code/my_projects/AI_Projects/AICodePilot
```

or enter the mapped container path:

```text
/workspace/AI_Projects/AICodePilot
```

After indexing succeeds, the Project Summary modal shows project name, purpose, tech stack, architecture, structure overview, file/chunk counts, and language ratio bars.

## Chat Workflow

1. Sign in using the frontend auth mock. Registration, login, profile settings, password reset, avatar upload, and captcha are implemented on the client side for UI demonstration.
2. Choose a supported model card.
3. Open a folder for preview or enter a backend-visible path.
4. Index the codebase.
5. Ask a question in the central chat panel.
6. Use `Shift + Enter` for line breaks. Press `Enter` to send.
7. Review the Markdown answer, code blocks, collapsible execution summary, Agent Steps, and Code Evidence.

## Theme and Language

The top bar supports:

- Light/dark theme switching, with light mode as the default.
- Simplified Chinese and English UI text switching.

Preferences are stored in browser `localStorage`.

## Recommended Questions

```text
请分析这个项目的 Agent 主流程在哪里？
Where is configuration loaded?
How is the tool registry implemented?
Which files define the FastAPI routes?
Generate tests for the Agent executor.
Analyze this error log and suggest a fix.
```

## Boundaries

- Browser folder access is permission-based and cannot grant the backend direct access to arbitrary local paths.
- Real backend authentication is not implemented yet; the current auth UI is a frontend mock for the product workflow.
- GLM, Qwen, and Claude require backend provider implementations before they can be used for real requests.
