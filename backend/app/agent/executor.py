import json
from typing import Any

from app.agent.planner import parse_agent_action
from app.agent.prompts import build_system_prompt
from app.agent.schemas import AgentRequest, AgentResponse, CodeReference, ToolResult
from app.core.config import Settings, get_settings
from app.core.exceptions import AICodePilotError
from app.llm.base import BaseLLMProvider
from app.llm.factory import LLMProviderFactory
from app.tools.registry import ToolRegistry, create_default_registry

_PROJECT_PATH_TOOLS = {"list_files", "read_file", "search_text", "retrieve_code"}


class AgentExecutor:
    def __init__(
        self,
        registry: ToolRegistry | None = None,
        llm_provider: BaseLLMProvider | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.registry = registry or create_default_registry()
        self.llm_provider = llm_provider
        self.settings = settings or get_settings()

    def run(self, request: AgentRequest) -> AgentResponse:
        provider_name = (request.provider or self.settings.llm_provider).strip().lower()
        model = request.model or self.settings.default_model_for_provider(provider_name)
        llm = self.llm_provider or LLMProviderFactory.create(provider_name, settings=self.settings)
        system_prompt = build_system_prompt(self.registry.describe_tools())
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": self._build_user_content(request)},
        ]

        first_response = llm.chat(messages, model=model)
        action = parse_agent_action(first_response)

        if action.type == "final":
            return AgentResponse(
                answer=action.answer or "",
                provider=provider_name,
                model=model,
                tool_calls=[],
                references=[],
            )

        if not action.tool:
            raise AICodePilotError("Agent action is missing tool name")

        arguments = dict(action.arguments)
        if request.project_path and action.tool in _PROJECT_PATH_TOOLS and "project_path" not in arguments:
            arguments["project_path"] = request.project_path

        tool = self.registry.get(action.tool)
        tool_result = ToolResult(name=action.tool, arguments=arguments)
        try:
            tool_result.result = tool.run(**arguments)
        except Exception as exc:
            tool_result.error = str(exc)

        summary_messages = [
            *messages,
            {"role": "assistant", "content": first_response},
            {
                "role": "user",
                "content": "Tool result:\n" + json.dumps(tool_result.model_dump(), ensure_ascii=False, default=str),
            },
        ]
        final_response = llm.chat(summary_messages, model=model)
        final_action = parse_agent_action(final_response)
        answer = final_action.answer if final_action.type == "final" else final_response

        return AgentResponse(
            answer=answer or "",
            provider=provider_name,
            model=model,
            tool_calls=[tool_result],
            references=self._extract_references(tool_result),
        )

    def _build_user_content(self, request: AgentRequest) -> str:
        if request.project_path:
            return f"Project path: {request.project_path}\nUser request: {request.message}"
        return request.message

    def _extract_references(self, tool_result: ToolResult) -> list[CodeReference]:
        if tool_result.error or not isinstance(tool_result.result, dict):
            return []

        result: dict[str, Any] = tool_result.result
        if tool_result.name == "search_text":
            return [
                CodeReference(
                    file_path=str(match["file_path"]),
                    line_number=int(match["line_number"]),
                    snippet=str(match["line"]),
                )
                for match in result.get("matches", [])
            ]
        if tool_result.name == "retrieve_code":
            return [
                CodeReference(
                    file_path=str(match["file_path"]),
                    line_number=int(match["start_line"]),
                    snippet=str(match["content"]),
                    score=float(match["score"]),
                )
                for match in result.get("matches", [])
            ]
        if tool_result.name == "read_file":
            return [
                CodeReference(
                    file_path=str(result.get("relative_path") or result.get("file_path")),
                    snippet=str(result.get("content", ""))[:500],
                )
            ]
        return []

