# Deployment 🚀

AICodePilot supports local backend and frontend execution today. Full Docker deployment is completed in Phase 7.

## Local Backend 🌐

1. Copy `.env.example` to `.env`.
2. Install backend dependencies.
3. Start the FastAPI backend.

```bash
cd backend
uvicorn app.main:app --reload
```

Open:

```text
http://localhost:8000/docs
```

## Local Frontend 🖥️

Start the Next.js frontend in a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open:

```text
http://127.0.0.1:3000
```

The frontend calls `NEXT_PUBLIC_API_BASE_URL` when it is configured. Without that variable, it uses `http://localhost:8000`.

The Phase 4 UI connects to the FastAPI service for chat, project indexing, provider selection, tool-call tracing, and code references.

## Planned Docker Deployment 🐳

```bash
docker compose up --build
```

Docker files are completed in Phase 7.

## Validation ✅

Deployment validation grows by phase:

- Phase 3: FastAPI app creation, OpenAPI schema, health route, and backend tests.
- Phase 4: frontend install, typecheck, lint, production build, and browser workflow.
- Phase 7: `docker compose up --build` starts backend and frontend together.
