# AICodePilot Frontend

The frontend is a Next.js workspace for interacting with the AICodePilot Agent. It provides model selection, workspace import, project indexing, chat, tool-call visibility, and code evidence review.

## Responsibilities

- Render the three-column AI code workspace.
- Let users select domestic/global model providers and available models.
- Let users open local folders or code files for browser-side previews.
- Send backend-visible paths to the API for RAG indexing.
- Display Project Summary metadata returned by the backend.
- Render Agent answers, tool-call timeline, and code evidence.

## Module Map

| Path | Purpose |
|---|---|
| `app/page.tsx` | Main page entry |
| `app/globals.css` | Design tokens, layout, component styling |
| `components/ChatWorkspace.tsx` | App shell, workspace import, chat, modals, auth mock |
| `components/ProviderSelector.tsx` | Model Center provider/source/model selection |
| `components/ToolCallTimeline.tsx` | Agent Steps panel |
| `components/CodeReference.tsx` | Code Evidence panel |
| `lib/api.ts` | Typed API client |

## Setup

```bash
cd frontend
npm install
```

## Run

Development mode:

```bash
npm run dev
```

Production-mode local review after UI changes:

```bash
npm run start:fresh
```

Open:

```text
http://127.0.0.1:3000
```

## Workspace Import Rules

Browser imports are for local preview only. They do not grant the backend direct access to arbitrary local paths.

Supported file extensions:

```text
.c .cpp .css .go .html .java .js .json .jsx .md .py .rs .scss .sh .ts .tsx .txt .yaml .yml
```

Unsupported office, binary, executable, or archive formats are blocked before import.

## Validation

```bash
npm run typecheck
npm run lint
npm run build
```

## Current Boundaries

- Account flows are frontend-local mocks.
- Real backend indexing requires a backend-visible path.
- Qwen, GLM, Claude, Gemini, and Moonshot are roadmap providers until backend modules are added.
- True streaming Agent updates require future SSE or WebSocket support.
