from typing import Any

import pytest
from pydantic import BaseModel

from app.core.exceptions import ToolError
from app.tools.base import BaseTool
from app.tools.file_tools import ListFilesTool, ReadFileTool
from app.tools.registry import ToolRegistry, create_default_registry
from app.tools.search_tools import SearchTextTool
from app.tools.rag_tools import RetrieveCodeTool


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


def test_default_registry_contains_phase_1_tools() -> None:
    registry = create_default_registry()

    assert isinstance(registry.get("list_files"), ListFilesTool)
    assert isinstance(registry.get("read_file"), ReadFileTool)
    assert isinstance(registry.get("search_text"), SearchTextTool)
    assert isinstance(registry.get("retrieve_code"), RetrieveCodeTool)


