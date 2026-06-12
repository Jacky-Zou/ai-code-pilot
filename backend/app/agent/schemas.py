from typing import Any, Literal

from pydantic import BaseModel, Field


class AgentRequest(BaseModel):
    message: str = Field(min_length=1)
    project_path: str | None = None
    provider: str | None = None
    model: str | None = None
    # Bring-your-own-key: the browser sends the provider credential per request.
    # Held only for the duration of the run; never logged or persisted.
    api_key: str | None = None
    base_url: str | None = None


class ToolCall(BaseModel):
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class ToolResult(BaseModel):
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    result: Any = None
    error: str | None = None


class AgentAction(BaseModel):
    type: Literal["action", "final"]
    tool: str | None = None
    arguments: dict[str, Any] = Field(default_factory=dict)
    answer: str | None = None


class CodeReference(BaseModel):
    file_path: str
    line_number: int | None = None
    snippet: str | None = None
    score: float | None = None


class PatchSuggestion(BaseModel):
    file_path: str
    diff: str = Field(min_length=1)
    summary: str | None = None


class AgentResponse(BaseModel):
    answer: str
    provider: str
    model: str
    tool_calls: list[ToolResult] = Field(default_factory=list)
    references: list[CodeReference] = Field(default_factory=list)
    patch_suggestions: list[PatchSuggestion] = Field(default_factory=list)
