# Deployment

AICodePilot supports three deployment modes: backend-only development, frontend/backend local development, and Docker Compose for a complete demo stack.

## Prerequisites

- Python 3.10+
- Node.js 20+
- Docker Desktop with Docker Compose v2
- A local `.env` copied from `.env.example`

Keep real API keys only in `.env`. The repository tracks `.env.example` with placeholders and ignores `.env` through `.gitignore`.

## Local Backend

```bash
cp .env.example .env
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open the API docs at:

```text
http://localhost:8000/docs
```

The health endpoint is:

```text
http://localhost:8000/api/health
```

## Local Frontend

Start the Next.js frontend in a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open:

```text
http://localhost:3000
```

The frontend reads `NEXT_PUBLIC_API_BASE_URL`. If it is not set, it falls back to `http://localhost:8000`.

For production-mode local review after frontend code changes, rebuild before starting:

```bash
cd frontend
npm run start:fresh
```

`npm run start` serves the existing `.next` production build. If the old process is still running, stop it before reviewing a new build.

## Docker Compose

From the repository root:

```bash
cp .env.example .env
docker compose up --build
```

Services:

| Service | URL | Purpose |
|---|---|---|
| backend | `http://localhost:8000` | FastAPI Agent and RAG API |
| frontend | `http://localhost:3000` | Next.js Web UI |

### Inspecting Local Projects from Docker

The backend container can only inspect files that are mounted into it. Configure a read-only
workspace mount in `.env` before starting Compose:

```env
PROJECTS_HOST_ROOT=D:/code/my_projects
PROJECTS_CONTAINER_ROOT=/workspace
NEXT_PUBLIC_DEFAULT_PROJECT_PATH=/workspace
```

Compose mounts `PROJECTS_HOST_ROOT` at `PROJECTS_CONTAINER_ROOT`. The backend also accepts a
host path under that root and maps it to the container path automatically. For example,
`D:/code/my_projects/AI_Projects/AICodePilot` maps to `/workspace/AI_Projects/AICodePilot`.

Stop the stack with:

```bash
docker compose down
```

## Docker Image Mirrors

The Dockerfiles use conventional default base images:

- `python:3.10-slim`
- `node:20-alpine`

If Docker Hub is slow or unreachable, override the build images before running Compose:

```powershell
$env:PYTHON_IMAGE="mirror.gcr.io/library/python:3.10-slim"
$env:NODE_IMAGE="mirror.gcr.io/library/node:20-alpine"
docker compose up --build
```

On bash-compatible shells:

```bash
PYTHON_IMAGE=mirror.gcr.io/library/python:3.10-slim \
NODE_IMAGE=mirror.gcr.io/library/node:20-alpine \
docker compose up --build
```

## Data Persistence

Compose mounts the repository `data/` directory into the backend container at `/app/data`. The backend sets:

```env
VECTOR_STORE_PATH=/app/data/vector_store
```

Generated vector-store data remains local and is ignored by Git.

## Security Notes

- Do not commit `.env` or real API keys.
- `docker compose config` may render environment values from `.env`; avoid sharing its raw output.
- API keys are injected into the backend through optional `.env` loading, not hardcoded in Dockerfiles.
- File, shell, and RAG tools still enforce the project safety checks implemented in the backend.

## Validation

The Phase 7 Docker validation used:

```powershell
$env:PYTHON_IMAGE="mirror.gcr.io/library/python:3.10-slim"
$env:NODE_IMAGE="mirror.gcr.io/library/node:20-alpine"
docker compose up --build -d
```

Then verified:

```text
GET http://localhost:8000/api/health -> 200
GET http://localhost:3000 -> 200
```

Finally cleaned up with:

```bash
docker compose down
```
