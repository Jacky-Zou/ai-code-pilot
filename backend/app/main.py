import argparse
from pathlib import Path

from app.agent.agent import AICodePilotAgent
from app.core.exceptions import AICodePilotError
from app.core.logger import get_logger

logger = get_logger(__name__)


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
