import pytest

from app.agent.patcher import generate_multi_file_patch_suggestions, generate_patch_suggestion
from app.core.exceptions import AICodePilotError


def test_generate_patch_suggestion_returns_unified_diff() -> None:
    suggestion = generate_patch_suggestion(
        file_path="backend/app/example.py",
        original_content="def hello():\n    return 'old'\n",
        updated_content="def hello():\n    return 'new'\n",
        summary="Update return value",
    )

    assert suggestion.file_path == "backend/app/example.py"
    assert suggestion.summary == "Update return value"
    assert "--- a/backend/app/example.py" in suggestion.diff
    assert "+++ b/backend/app/example.py" in suggestion.diff
    assert "-    return 'old'" in suggestion.diff
    assert "+    return 'new'" in suggestion.diff


def test_generate_patch_suggestion_rejects_noop_change() -> None:
    with pytest.raises(AICodePilotError, match="without content changes"):
        generate_patch_suggestion("README.md", "same\n", "same\n")


def test_generate_patch_suggestion_rejects_unsafe_paths() -> None:
    with pytest.raises(AICodePilotError, match="project-relative"):
        generate_patch_suggestion("C:/tmp/file.py", "old", "new")

    with pytest.raises(AICodePilotError, match="parent directories"):
        generate_patch_suggestion("../file.py", "old", "new")


def test_generate_multi_file_patch_suggestions() -> None:
    suggestions = generate_multi_file_patch_suggestions(
        [
            {
                "file_path": "a.py",
                "original_content": "x = 1\n",
                "updated_content": "x = 2\n",
                "summary": "Update x",
            },
            {
                "file_path": "b.py",
                "original_content": "y = 1\n",
                "updated_content": "y = 2\n",
            },
        ],
        context_lines=1,
    )

    assert [item.file_path for item in suggestions] == ["a.py", "b.py"]
    assert suggestions[0].summary == "Update x"
    assert "+x = 2" in suggestions[0].diff
    assert "+y = 2" in suggestions[1].diff
