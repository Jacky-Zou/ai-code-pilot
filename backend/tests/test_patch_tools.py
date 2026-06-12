"""Tests for ProposePatchTool (T-9): diff generation, path safety, registry.

Covers:
- Tool generates valid unified diff with +/- lines
- file_path in result is project-relative (not absolute)
- Path traversal / absolute path attempts are rejected
- patch_suggestions key matches AgentExecutor expectation
- executor integration: AgentResponse.patch_suggestions populated
"""

from pathlib import Path

import pytest

from app.tools.patch_tools import ProposePatchTool
from app.core.exceptions import ToolError


class TestProposePatchTool:
    def test_generates_diff_with_plus_and_minus_lines(self, tmp_path: Path) -> None:
        original = "line one\nline two\nline three\n"
        updated = "line one\nline TWO modified\nline three\n"
        target = tmp_path / "src.py"
        target.write_text(original, encoding="utf-8")

        tool = ProposePatchTool()
        result = tool.run(
            file_path="src.py",
            updated_content=updated,
            project_path=str(tmp_path),
        )

        assert "patch_suggestions" in result
        suggestions = result["patch_suggestions"]
        assert len(suggestions) == 1
        diff = suggestions[0]["diff"]
        assert any(line.startswith("-") for line in diff.splitlines()), "Diff must contain removed lines"
        assert any(line.startswith("+") for line in diff.splitlines()), "Diff must contain added lines"

    def test_file_path_in_result_is_relative(self, tmp_path: Path) -> None:
        (tmp_path / "app.py").write_text("x = 1\n", encoding="utf-8")

        tool = ProposePatchTool()
        result = tool.run(
            file_path="app.py",
            updated_content="x = 2\n",
            project_path=str(tmp_path),
        )

        assert result["file_path"] == "app.py"
        assert not Path(result["file_path"]).is_absolute()

    def test_summary_propagated_to_patch_suggestion(self, tmp_path: Path) -> None:
        (tmp_path / "config.py").write_text("DEBUG = False\n", encoding="utf-8")

        tool = ProposePatchTool()
        result = tool.run(
            file_path="config.py",
            updated_content="DEBUG = True\n",
            project_path=str(tmp_path),
            summary="Enable debug mode for development",
        )

        assert result["summary"] == "Enable debug mode for development"
        assert result["patch_suggestions"][0]["summary"] == "Enable debug mode for development"

    def test_path_traversal_rejected(self, tmp_path: Path) -> None:
        tool = ProposePatchTool()
        with pytest.raises(ToolError):
            tool.run(
                file_path="../outside.py",
                updated_content="malicious\n",
                project_path=str(tmp_path),
            )

    def test_nonexistent_file_raises_tool_error(self, tmp_path: Path) -> None:
        tool = ProposePatchTool()
        with pytest.raises(ToolError):
            tool.run(
                file_path="does_not_exist.py",
                updated_content="new content\n",
                project_path=str(tmp_path),
            )

    def test_nested_path_stays_relative(self, tmp_path: Path) -> None:
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "util.py").write_text("def helper(): pass\n", encoding="utf-8")

        tool = ProposePatchTool()
        result = tool.run(
            file_path="src/util.py",
            updated_content="def helper(): return 42\n",
            project_path=str(tmp_path),
        )

        assert result["file_path"] == "src/util.py"
        diff = result["patch_suggestions"][0]["diff"]
        assert "-def helper(): pass" in diff
        assert "+def helper(): return 42" in diff

    def test_patch_suggestions_key_matches_executor_expectation(self, tmp_path: Path) -> None:
        """The result dict must contain 'patch_suggestions' for AgentExecutor._extract_patch_suggestions."""

        (tmp_path / "main.py").write_text("a = 1\n", encoding="utf-8")
        tool = ProposePatchTool()
        result = tool.run(file_path="main.py", updated_content="a = 2\n", project_path=str(tmp_path))

        assert "patch_suggestions" in result
        assert isinstance(result["patch_suggestions"], list)
        assert len(result["patch_suggestions"]) == 1
        # Each suggestion must have the PatchSuggestion fields
        s = result["patch_suggestions"][0]
        assert "file_path" in s
        assert "diff" in s


class TestProposePatchToolInRegistry:
    def test_propose_patch_registered_by_default(self) -> None:
        from app.tools.registry import create_default_registry

        registry = create_default_registry()
        tool = registry.get("propose_patch")
        assert tool.name == "propose_patch"

    def test_propose_patch_in_project_path_tools(self) -> None:
        from app.agent.executor import _PROJECT_PATH_TOOLS

        assert "propose_patch" in _PROJECT_PATH_TOOLS


class TestExecutorPatchSuggestionsIntegration:
    def test_executor_populates_patch_suggestions(self, tmp_path: Path) -> None:
        """executor must surface patch_suggestions from tool results in AgentResponse."""

        from app.agent.executor import AgentExecutor
        from app.agent.schemas import AgentRequest
        from app.core.config import Settings
        from app.llm.base import BaseLLMProvider
        from app.llm.schemas import ChatResult, LLMToolCall

        (tmp_path / "target.py").write_text("x = 1\n", encoding="utf-8")

        class PatchProvider(BaseLLMProvider):
            provider_name = "openai"
            _calls = 0

            def chat(self, messages, model=None, **kwargs):
                return '{"type":"final","answer":"Patch proposed."}'

            def chat_with_tools(self, messages, tools, model=None) -> ChatResult:
                self._calls += 1
                if self._calls == 1:
                    return ChatResult(
                        content=None,
                        tool_calls=[
                            LLMToolCall(
                                id="c1",
                                name="propose_patch",
                                arguments={
                                    "file_path": "target.py",
                                    "updated_content": "x = 99\n",
                                    "summary": "Update x",
                                },
                            )
                        ],
                    )
                return ChatResult(content="Patch proposed.", tool_calls=[])

        executor = AgentExecutor(
            llm_provider=PatchProvider(),
            settings=Settings(_env_file=None),
        )
        response = executor.run(AgentRequest(message="change x to 99", project_path=str(tmp_path)))

        assert response.patch_suggestions, "patch_suggestions must not be empty"
        assert response.patch_suggestions[0].file_path == "target.py"
        diff = response.patch_suggestions[0].diff
        assert "-x = 1" in diff
        assert "+x = 99" in diff
