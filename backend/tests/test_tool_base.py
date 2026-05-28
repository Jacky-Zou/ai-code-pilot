from typing import Any

import pytest
from pydantic import BaseModel

from app.tools.base import BaseTool


class EchoArgs(BaseModel):
    text: str


class EchoTool(BaseTool):
    name = "echo"
    description = "Echo text"
    args_schema = EchoArgs

    def run(self, **kwargs: Any) -> str:
        args = self.validate_args(kwargs)
        return args.text


def test_base_tool_is_abstract() -> None:
    with pytest.raises(TypeError):
        BaseTool()  # type: ignore[abstract]


def test_tool_validates_args() -> None:
    tool = EchoTool()

    assert tool.run(text="hello") == "hello"


def test_tool_schema_contains_metadata() -> None:
    schema = EchoTool().schema()

    assert schema["name"] == "echo"
    assert schema["description"] == "Echo text"
    assert "parameters" in schema
