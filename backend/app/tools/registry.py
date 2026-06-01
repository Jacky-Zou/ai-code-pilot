from app.core.exceptions import ToolError
from app.core.logger import get_logger
from app.tools.base import BaseTool
from app.tools.file_tools import FindFilesTool, ListFilesTool, ProjectTreeTool, ReadFileTool
from app.tools.log_tools import AnalyzeLogTool
from app.tools.rag_tools import RetrieveCodeTool
from app.tools.search_tools import SearchTextTool
from app.tools.shell_tools import RunCommandTool

logger = get_logger(__name__)


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        if tool.name in self._tools:
            raise ToolError(f"Tool is already registered: {tool.name}")
        self._tools[tool.name] = tool
        logger.debug("Registered tool=%s", tool.name)

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
    registry.register(ProjectTreeTool())
    registry.register(FindFilesTool())
    registry.register(SearchTextTool())
    registry.register(RetrieveCodeTool())
    registry.register(AnalyzeLogTool())
    registry.register(RunCommandTool())
    logger.info("Default tool registry created tools=%s", [tool.name for tool in registry.list_tools()])
    return registry
