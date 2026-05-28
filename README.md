# AICodePilot

AICodePilot is an AI coding assistant for codebase understanding and development workflows. It is designed as a hands-on LLM Agent project with tool calling, semantic retrieval, multiple model providers, a FastAPI backend, a React/Next.js frontend, Docker deployment, and complete engineering documentation.

Full title: **AICodePilot: LLM Agent based AI codebase understanding and development assistant**.

## Core Features

- Codebase structure analysis and project file exploration.
- Safe local file reading and text search tools.
- Hand-written Agent execution loop with structured tool calling.
- RAG-based semantic code retrieval with file path and line references.
- Multi-provider LLM abstraction with OpenAI as the default and DeepSeek support.
- FastAPI service layer for Agent and project indexing APIs.
- Web UI for provider selection, project indexing, chat, tool-call timeline, and code references.
- Advanced development tools including log analysis, safe command execution, and patch suggestions.
- Docker and docker-compose deployment.

## Tech Stack

Backend:

- Python
- FastAPI
- Pydantic and pydantic-settings
- httpx
- pytest
- ruff, black, mypy

AI and retrieval:

- LLM API
- Tool Calling
- Prompt Engineering
- Embedding
- RAG
- FAISS or Chroma

Frontend:

- React
- Next.js
- Tailwind CSS
- shadcn/ui
- Monaco Editor for future code display

Deployment:

- Docker
- docker-compose
- `.env` based configuration

## Model Providers

AICodePilot uses OpenAI / ChatGPT by default:

```env
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
```

DeepSeek is supported through the same provider abstraction:

```env
LLM_PROVIDER=deepseek
LLM_MODEL=deepseek-chat
```

API requests may override the default provider and model per request.

## Roadmap

1. Project initialization.
2. Mini Agent CLI with tool calling.
3. RAG code retrieval.
4. FastAPI backend APIs.
5. Web UI with provider and model selection.
6. Advanced Agent tools and memory.
7. Engineering quality, tests, linting, and typing.
8. Docker deployment.
9. Documentation and resume packaging.

## Quick Start

The project is being built phase by phase. The final local workflow will be:

```bash
cp .env.example .env
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m app.main
```

The final Docker workflow will be:

```bash
docker compose up --build
```

## Documentation

- [Architecture](docs/architecture.md)
- [Agent Design](docs/agent-design.md)
- [RAG Design](docs/rag-design.md)
- [API](docs/api.md)
- [Security](docs/security.md)
- [Deployment](docs/deployment.md)
- [User Guide](docs/user-guide.md)
- [Development Guide](docs/development-guide.md)
- [Resume Guide](docs/resume.md)
- [TodoList](docs/todolist.md)

## License

This project is released under the MIT License. See [LICENSE](LICENSE).
