# Deployment 🚢

AICodePilot supports local backend execution today and will support full Docker deployment after Phase 7.

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

## Planned Frontend 🖥️

The Next.js frontend is planned for Phase 4. It will connect to the FastAPI service for chat, project indexing, provider selection, tool-call tracing, and code references.

## Planned Docker Deployment 🐳

```bash
docker compose up --build
```

Docker files are completed in Phase 7.

## Validation ✅

Deployment validation grows by phase:

- Phase 3: FastAPI app creation, OpenAPI schema, health route, and backend tests.
- Phase 4: frontend install/build and browser workflow.
- Phase 7: `docker compose up --build` starts backend and frontend together.
