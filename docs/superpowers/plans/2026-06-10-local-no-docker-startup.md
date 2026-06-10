# Local No-Docker Startup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make AICodePilot easy to run and stop locally without Docker Desktop.

**Architecture:** Keep Docker artifacts as optional deployment assets, but make Windows local development the primary path. Use a small PowerShell launcher that opens visible backend and frontend terminal windows instead of hidden background services.

**Tech Stack:** PowerShell, FastAPI/Uvicorn, Next.js, Pydantic settings, Markdown docs.

---

### Task 1: Local Process Scripts

**Files:**
- Create: `scripts/start-local.ps1`

- [x] Add a startup script that checks ports, optionally installs dependencies, opens visible backend and frontend PowerShell windows, and prints URLs.
- [x] Stop behavior is ordinary terminal behavior: press `Ctrl+C` in those windows or close them.

### Task 2: Stable Local Paths

**Files:**
- Modify: `backend/app/core/config.py`
- Modify: `backend/tests/test_config.py`
- Modify: `.env.example`

- [x] Resolve relative `VECTOR_STORE_PATH` values against the repository root so local runs do not depend on the current working directory.
- [x] Update tests for the new path behavior.
- [x] Make the example frontend default project path local-friendly.

### Task 3: Documentation

**Files:**
- Modify: `README.md`
- Modify: `docs/deployment.md`
- Modify: `docs/development-guide.md`

- [x] Document local startup as the default path.
- [x] Keep Docker Compose as optional deployment only.
- [x] Note that runtime logs stay in the visible backend/frontend terminal windows.

### Task 4: Verification

**Commands:**
- `pytest backend/tests/test_config.py backend/tests/test_project_paths.py`
- `powershell -ExecutionPolicy Bypass -File scripts/start-local.ps1`
- `Invoke-WebRequest http://localhost:8000/api/health`
- `Invoke-WebRequest http://localhost:3000`

- [ ] Run focused backend tests.
- [ ] Start the local stack without Docker.
- [ ] Verify both HTTP endpoints respond.
