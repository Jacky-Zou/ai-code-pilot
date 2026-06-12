from typing import Any

import pytest
from pydantic import BaseModel

from app.core.exceptions import ToolError
from app.tools.base import BaseTool
from app.tools.file_tools import FindFilesTool, ListFilesTool, ProjectTreeTool, ReadFileTool
from app.tools.log_tools import AnalyzeLogTool
from app.tools.rag_tools import RetrieveCodeTool
from app.tools.registry import ToolRegistry, create_default_registry
from app.tools.search_tools import SearchTextTool
from app.tools.shell_tools import RunCommandTool


class Args(BaseModel):
    value: str


class SampleTool(BaseTool):
    name = "sample"
    description = "Sample tool"
    args_schema = Args

    def run(self, **kwargs: Any) -> str:
        return str(kwargs["value"])


def test_registry_registers_and_gets_tool() -> None:
    registry = ToolRegistry()
    tool = SampleTool()

    registry.register(tool)

    assert registry.get("sample") is tool


def test_registry_rejects_duplicate_tool() -> None:
    registry = ToolRegistry()
    registry.register(SampleTool())

    with pytest.raises(ToolError, match="already registered"):
        registry.register(SampleTool())


def test_registry_rejects_missing_tool() -> None:
    registry = ToolRegistry()

    with pytest.raises(ToolError, match="Tool not found"):
        registry.get("missing")


def test_registry_describes_tools() -> None:
    registry = ToolRegistry()
    registry.register(SampleTool())

    descriptions = registry.describe_tools()

    assert descriptions[0]["name"] == "sample"


def test_default_registry_contains_agent_tools() -> None:
    registry = create_default_registry()

    assert isinstance(registry.get("list_files"), ListFilesTool)
    assert isinstance(registry.get("read_file"), ReadFileTool)
    assert isinstance(registry.get("project_tree"), ProjectTreeTool)
    assert isinstance(registry.get("find_files"), FindFilesTool)
    assert isinstance(registry.get("search_text"), SearchTextTool)
    assert isinstance(registry.get("retrieve_code"), RetrieveCodeTool)
    assert isinstance(registry.get("analyze_log"), AnalyzeLogTool)
    # run_command is gated by ENABLE_SHELL_TOOL (default False); not in default registry.
    # Verify it is absent rather than present.
    with pytest.raises(ToolError, match="Tool not found"):
        registry.get("run_command")


def test_default_registry_contains_propose_patch() -> None:
    """propose_patch must be registered by default (T-9)."""

    from app.tools.patch_tools import ProposePatchTool

    registry = create_default_registry()
    assert isinstance(registry.get("propose_patch"), ProposePatchTool)


def test_shell_tool_registered_when_enabled(monkeypatch) -> None:
    """run_command is registered when ENABLE_SHELL_TOOL=true."""

    monkeypatch.setenv("ENABLE_SHELL_TOOL", "true")
    # Force settings to reload with new env
    import app.core.config as cfg_module

    cfg_module.get_settings.cache_clear()

    registry = create_default_registry()
    assert isinstance(registry.get("run_command"), RunCommandTool)

    # Restore
    cfg_module.get_settings.cache_clear()
