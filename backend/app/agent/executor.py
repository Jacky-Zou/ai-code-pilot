import json
from typing import Any

from app.agent.planner import parse_agent_action
from app.agent.prompts import build_system_prompt
from app.agent.schemas import AgentAction, AgentRequest, AgentResponse, CodeReference, PatchSuggestion, ToolResult
from app.core.config import Settings, get_settings
from app.core.exceptions import AICodePilotError
from app.core.logger import get_logger
from app.llm.base import BaseLLMProvider
from app.llm.factory import LLMProviderFactory
from app.memory.conversation_memory import ConversationMemory
from app.tools.registry import ToolRegistry, create_default_registry

_PROJECT_PATH_TOOLS = {"list_files", "read_file", "search_text", "retrieve_code", "run_command"}
_MAX_TOOL_STEPS = 5
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
        tool_results: list[ToolResult] = []
        answer = ""
        current_messages = list(messages)

        for step in range(1, _MAX_TOOL_STEPS + 1):
            # Pass a shallow copy so later tool-result messages do not mutate
            # the exact message list already handed to a provider or test fake.
            raw_response = llm.chat(list(current_messages), model=model)
            action = parse_agent_action(raw_response)

            if action.type == "final":
                answer = action.answer or ""
                if answer:
                    break
                if tool_results:
                    current_messages.extend(
                        [
                            {"role": "assistant", "content": raw_response},
                            {
                                "role": "user",
                                "content": (
                                    "Your previous response did not include a final answer. "
                                    "Return only a concise JSON final answer with paths, line numbers, "
                                    "and an explanation based on the tool results. Do not include thinking tags."
                                ),
                            },
                        ]
                    )
                    continue
                break

            tool_result = self._execute_action(action, request)
            tool_results.append(tool_result)
            current_messages.extend(
                [
                    {"role": "assistant", "content": raw_response},
                    {
                        "role": "user",
                        "content": "Tool result:\n" + json.dumps(tool_result.model_dump(), ensure_ascii=False, default=str),
                    },
                ]
            )
            logger.info(
                "Agent tool step completed provider=%s model=%s step=%s tool=%s tool_error=%s",
                provider_name,
                model,
                step,
                tool_result.name,
                bool(tool_result.error),
            )
        else:
            answer = ""

        if not answer:
            answer = self._build_fallback_answer(tool_results)

        self._remember_turn(user_content, answer, tool_results[-1] if tool_results else None)
        logger.info(
            "Agent run completed provider=%s model=%s tool_calls=%s",
            provider_name,
            model,
            len(tool_results),
        )

        return AgentResponse(
            answer=answer,
            provider=provider_name,
            model=model,
            tool_calls=tool_results,
            references=self._extract_references_from_results(tool_results),
            patch_suggestions=self._extract_patch_suggestions_from_results(tool_results),
        )

    def _execute_action(self, action: AgentAction, request: AgentRequest) -> ToolResult:
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
        return tool_result

    def _build_fallback_answer(self, tool_results: list[ToolResult]) -> str:
        if not tool_results:
            return "I could not produce a final answer from the model response."

        lines = ["I executed tools but the model did not return a usable final summary. Relevant results:"]
        for tool_result in tool_results:
            if tool_result.error:
                lines.append(f"- {tool_result.name}: {tool_result.error}")
                continue
            if tool_result.name == "read_file" and isinstance(tool_result.result, dict):
                relative_path = tool_result.result.get("relative_path") or tool_result.result.get("file_path")
                lines.append(f"- Read `{relative_path}`.")
            elif tool_result.name == "list_files" and isinstance(tool_result.result, dict):
                files = [str(item) for item in tool_result.result.get("files", [])]
                agent_files = [file for file in files if "agent" in file.lower()][:8]
                if agent_files:
                    lines.append("- Agent-related files found: " + ", ".join(f"`{file}`" for file in agent_files))
                else:
                    lines.append(f"- Listed {tool_result.result.get('count', len(files))} files.")
            elif tool_result.name == "retrieve_code" and isinstance(tool_result.result, dict):
                matches = tool_result.result.get("matches", [])[:5]
                for match in matches:
                    lines.append(f"- `{match.get('file_path')}` lines {match.get('start_line')}-{match.get('end_line')}")
            else:
                lines.append(f"- Ran `{tool_result.name}` successfully.")
        return "\n".join(lines)

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

    def _extract_references_from_results(self, tool_results: list[ToolResult]) -> list[CodeReference]:
        references: list[CodeReference] = []
        for tool_result in tool_results:
            references.extend(self._extract_references(tool_result))
        return references

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

    def _extract_patch_suggestions_from_results(self, tool_results: list[ToolResult]) -> list[PatchSuggestion]:
        suggestions: list[PatchSuggestion] = []
        for tool_result in tool_results:
            suggestions.extend(self._extract_patch_suggestions(tool_result))
        return suggestions
