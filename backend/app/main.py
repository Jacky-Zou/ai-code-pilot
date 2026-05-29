import argparse
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.agent.agent import AICodePilotAgent
from app.api.routes_chat import router as chat_router
from app.api.routes_project import router as project_router
from app.api.schemas import HealthResponse
from app.core.config import get_settings
from app.core.exceptions import AICodePilotError, register_exception_handlers
from app.core.logger import get_logger

logger = get_logger(__name__)


def create_app() -> FastAPI:
    """Create the FastAPI service and wire the Phase 3 API routers."""

    application = FastAPI(
        title="AICodePilot",
        description="LLM Agent based AI codebase understanding and development assistant.",
        version="0.1.0",
    )
    settings = get_settings()
    # Browser-based frontend requests include an OPTIONS preflight before POST
    # calls. Without CORS middleware those preflights return 405, and the UI can
    # only surface the browser-level "Failed to fetch" message.
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origin_list,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )
    register_exception_handlers(application)
    application.include_router(chat_router)
    application.include_router(project_router)

    @application.get("/api/health", response_model=HealthResponse, tags=["health"])
    def health() -> HealthResponse:
        return HealthResponse()

    return application


app = create_app()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AICodePilot Mini Agent CLI")
    parser.add_argument(
        "--project-path",
        default=str(Path.cwd()),
        help="Project directory available to Agent tools. Defaults to current working directory.",
    )
    parser.add_argument("--provider", default=None, help="LLM provider, for example openai or deepseek.")
    parser.add_argument("--model", default=None, help="LLM model override.")
    return parser


def run_cli() -> None:
    args = build_parser().parse_args()
    agent = AICodePilotAgent()
    print("AICodePilot Mini Agent CLI")
    print("Type 'exit' or 'quit' to stop.")
    print(f"Project path: {args.project_path}")

    while True:
        try:
            message = input("\nYou> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            return

        if message.lower() in {"exit", "quit"}:
            print("Bye.")
            return
        if not message:
            continue

        try:
            response = agent.run(
                message=message,
                project_path=args.project_path,
                provider=args.provider,
                model=args.model,
            )
        except AICodePilotError as exc:
            logger.error("Agent error: %s", exc)
            print(f"Error: {exc}")
            continue
        except Exception as exc:
            logger.exception("Unexpected error")
            print(f"Unexpected error: {exc}")
            continue

        print(f"\nAICodePilot> {response.answer}")
        if response.tool_calls:
            print("\nTool calls:")
            for tool_call in response.tool_calls:
                status = "error" if tool_call.error else "ok"
                print(f"- {tool_call.name} ({status})")
        if response.references:
            print("\nReferences:")
            for reference in response.references:
                location = reference.file_path
                if reference.line_number is not None:
                    location = f"{location}:{reference.line_number}"
                print(f"- {location}")


if __name__ == "__main__":
    run_cli()
