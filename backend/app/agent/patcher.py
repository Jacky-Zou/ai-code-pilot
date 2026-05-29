from difflib import unified_diff
from pathlib import Path

from app.agent.schemas import PatchSuggestion
from app.core.exceptions import AICodePilotError


def generate_patch_suggestion(
    file_path: str,
    original_content: str,
    updated_content: str,
    summary: str | None = None,
    context_lines: int = 3,
) -> PatchSuggestion:
    """Create a unified diff suggestion without modifying files.

    This helper is deliberately pure: it receives text, returns a diff string,
    and never opens or writes the target file. The Agent can therefore propose
    changes safely while the user stays in control of applying any patch.
    """

    normalized_path = _normalize_patch_path(file_path)
    if original_content == updated_content:
        raise AICodePilotError("Cannot generate patch suggestion without content changes")
    if context_lines < 0:
        raise AICodePilotError("context_lines must be greater than or equal to 0")

    diff_lines = unified_diff(
        _split_for_diff(original_content),
        _split_for_diff(updated_content),
        fromfile=f"a/{normalized_path}",
        tofile=f"b/{normalized_path}",
        lineterm="",
        n=context_lines,
    )
    diff = "\n".join(diff_lines)
    if not diff:
        raise AICodePilotError("Patch generation produced an empty diff")

    return PatchSuggestion(file_path=normalized_path, diff=diff, summary=summary)


def generate_multi_file_patch_suggestions(
    changes: list[dict[str, str]],
    context_lines: int = 3,
) -> list[PatchSuggestion]:
    suggestions: list[PatchSuggestion] = []
    for change in changes:
        suggestions.append(
            generate_patch_suggestion(
                file_path=change["file_path"],
                original_content=change["original_content"],
                updated_content=change["updated_content"],
                summary=change.get("summary"),
                context_lines=context_lines,
            )
        )
    return suggestions


def _split_for_diff(content: str) -> list[str]:
    # splitlines() keeps the diff stable across Windows and POSIX line endings.
    # The returned patch is a suggestion artifact, not a byte-for-byte file
    # rewrite, so normalized line separators are easier to inspect and test.
    return content.splitlines()


def _normalize_patch_path(file_path: str) -> str:
    cleaned = file_path.strip()
    if not cleaned:
        raise AICodePilotError("file_path cannot be empty")
    path = Path(cleaned)
    if path.is_absolute():
        raise AICodePilotError("Patch suggestions must use project-relative file paths")
    if ".." in path.parts:
        raise AICodePilotError("Patch suggestions cannot target parent directories")
    return path.as_posix()
