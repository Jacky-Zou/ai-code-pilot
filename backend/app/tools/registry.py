from app.core.exceptions import ToolError
from app.tools.base import BaseTool
from app.tools.file_tools import ListFilesTool, ReadFileTool
from app.tools.search_tools import SearchTextTool


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        if tool.name in self._tools:
            raise ToolError(f"Tool is already registered: {tool.name}")
        self._tools[tool.name] = tool

    def get(self, name: str) -> BaseTool:
        try:
            return self._tools[name]
        except KeyError as exc:
            raise ToolError(f"Tool not found: {name}") from exc

    def list_tools(self) -> list[BaseTool]:
        return list(self._tools.values())

    def describe_tools(self) -> list[dict[str, object]]:
        return [tool.schema() for tool in self.list_tools()]


def create_default_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(ListFilesTool())
    registry.register(ReadFileTool())
    registry.register(SearchTextTool())
    return registry
