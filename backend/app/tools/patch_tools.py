from typing import Any

from pydantic import BaseModel, Field

from app.agent.patcher import generate_patch_suggestion
from app.core.exceptions import ToolError
from app.tools.base import BaseTool
from app.tools.file_tools import _resolve_file

# Hard cap on updated_content size. Large proposed changes should be broken
# into smaller pieces; this prevents the agent from exhausting API body limits.
_MAX_CONTENT_BYTES = 200_000


class ProposePatchArgs(BaseModel):
    file_path: str = Field(min_length=1)
    updated_content: str = Field(min_length=1, max_length=_MAX_CONTENT_BYTES)
    project_path: str | None = None
    summary: str | None = None


class ProposePatchTool(BaseTool):
    """Generate a unified-diff patch suggestion without modifying any file.

    The agent supplies the full intended new content of an existing file; the
    tool reads the current content, computes a unified diff, and returns it as
    an advisory patch suggestion. It never writes to disk: the user reviews and
    applies changes manually. This keeps the agent in a safe, reviewable role.
    """

    name = "propose_patch"
    description = (
        "Propose a code change to an existing project file as a reviewable unified diff. "
        "Provide the file_path (relative to project root) and the complete updated_content. "
        "Does NOT write or modify any file."
    )
    args_schema = ProposePatchArgs

    def run(self, **kwargs: Any) -> dict[str, Any]:
        args = self.validate_args(kwargs)
        assert isinstance(args, ProposePatchArgs)

        # Reuse the project-root-confined resolver so the agent cannot target
        # files outside the workspace. _resolve_file raises ToolError on escape.
        try:
            root, resolved = _resolve_file(args.file_path, args.project_path)
        except ToolError:
            raise

        try:
            original_content = resolved.read_text(encoding="utf-8")
        except OSError as exc:
            raise ToolError(f"Cannot read file for patching: {exc}") from exc

        relative_path = resolved.relative_to(root).as_posix()
        suggestion = generate_patch_suggestion(
            file_path=relative_path,
            original_content=original_content,
            updated_content=args.updated_content,
            summary=args.summary,
        )

        return {
            "file_path": relative_path,
            "summary": suggestion.summary,
            # Key name matches AgentExecutor._extract_patch_suggestions expectation.
            "patch_suggestions": [suggestion.model_dump()],
        }
