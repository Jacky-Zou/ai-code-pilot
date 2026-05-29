import json
from typing import Any

from app.agent.planner import parse_agent_action
from app.agent.prompts import build_system_prompt
from app.agent.schemas import AgentRequest, AgentResponse, CodeReference, PatchSuggestion, ToolResult
from app.core.config import Settings, get_settings
from app.core.exceptions import AICodePilotError
from app.core.logger import get_logger
from app.llm.base import BaseLLMProvider
from app.llm.factory import LLMProviderFactory
from app.memory.conversation_memory import ConversationMemory
from app.tools.registry import ToolRegistry, create_default_registry

_PROJECT_PATH_TOOLS = {"list_files", "read_file", "search_text", "retrieve_code", "run_command"}
logger = get_logger(__name__)


class AgentExecutor:
    def __init__(
        self,
        registry: ToolRegistry | None = None,
        llm_provider: BaseLLMProvider | None = None,
        memory: ConversationMemory | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.registry = registry or create_default_registry()
        self.llm_provider = llm_provider
        self.memory = memory
        self.settings = settings or get_settings()

    def run(self, request: AgentRequest) -> AgentResponse:
        provider_name = (request.provider or self.settings.llm_provider).strip().lower()
        model = request.model or self.settings.default_model_for_provider(provider_name)
        llm = self.llm_provider or LLMProviderFactory.create(provider_name, settings=self.settings)
        system_prompt = build_system_prompt(self.registry.describe_tools())
        user_content = self._build_user_content(request)
        messages = self._build_messages(system_prompt, user_content)

        logger.info(
            "Agent run started provider=%s model=%s project_path_present=%s memory_enabled=%s",
            provider_name,
            model,
            bool(request.project_path),
            self.memory is not None,
        )
        first_response = llm.chat(messages, model=model)
        action = parse_agent_action(first_response)

        if action.type == "final":
            self._remember_turn(user_content, action.answer or "")
            logger.info("Agent run completed without tool provider=%s model=%s", provider_name, model)
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

        logger.info("Agent selected tool=%s argument_keys=%s", action.tool, sorted(arguments))
        tool = self.registry.get(action.tool)
        tool_result = ToolResult(name=action.tool, arguments=arguments)
        try:
            tool_result.result = tool.run(**arguments)
        except Exception as exc:
            tool_result.error = str(exc)
            logger.warning("Tool execution failed tool=%s error=%s", action.tool, exc)
        else:
            logger.info("Tool execution completed tool=%s", action.tool)

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
        self._remember_turn(user_content, answer or "", tool_result)
        logger.info(
            "Agent run completed with tool provider=%s model=%s tool=%s tool_error=%s",
            provider_name,
            model,
            action.tool,
            bool(tool_result.error),
        )

        return AgentResponse(
            answer=answer or "",
            provider=provider_name,
            model=model,
            tool_calls=[tool_result],
            references=self._extract_references(tool_result),
            patch_suggestions=self._extract_patch_suggestions(tool_result),
        )

    def _build_messages(self, system_prompt: str, user_content: str) -> list[dict[str, str]]:
        if self.memory is None:
            return [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ]

        # Memory history is appended after the fresh system prompt so tool
        # descriptions and safety rules are always current. The new user
        # request is added last and persisted only after the Agent responds.
        messages = self.memory.to_llm_messages(system_message=system_prompt)
        messages.append({"role": "user", "content": user_content})
        return messages

    def _remember_turn(self, user_content: str, assistant_content: str, tool_result: ToolResult | None = None) -> None:
        if self.memory is None:
            return
        self.memory.add_user_message(user_content)
        if tool_result is not None:
            self.memory.add_tool_message(json.dumps(tool_result.model_dump(), ensure_ascii=False, default=str))
        self.memory.add_assistant_message(assistant_content)

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

    def _extract_patch_suggestions(self, tool_result: ToolResult) -> list[PatchSuggestion]:
        if tool_result.error or not isinstance(tool_result.result, dict):
            return []

        raw_suggestions = tool_result.result.get("patch_suggestions", [])
        suggestions: list[PatchSuggestion] = []
        for item in raw_suggestions:
            if isinstance(item, PatchSuggestion):
                suggestions.append(item)
            elif isinstance(item, dict):
                # Patch suggestions remain advisory data. The executor only
                # validates and forwards them; it never applies the diff.
                suggestions.append(PatchSuggestion.model_validate(item))
        return suggestions
