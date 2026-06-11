import json
import re
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

_PROJECT_PATH_TOOLS = {
    "list_files",
    "read_file",
    "project_tree",
    "find_files",
    "search_text",
    "retrieve_code",
    "run_command",
}
_MAX_TOOL_STEPS = 5
_PROTOCOL_LEAK_PATTERN = re.compile(
    r"(```\s*json|<tool_calls>|</tool_calls>|<thinking>|</thinking>|\{\s*\"type\"\s*:\s*\"(?:action|final|read_file|list_files|search_text|retrieve_code))",
    re.IGNORECASE | re.DOTALL,
)
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
                if answer and not self._looks_like_protocol_leak(answer):
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

        if not answer and tool_results:
            answer = self._request_final_summary(llm, current_messages, model)

        if not answer:
            answer = self._build_fallback_answer(tool_results, user_content)
        answer = self._clean_final_answer(answer, tool_results, user_content)

        self._remember_turn(request.message, answer)
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

    def _request_final_summary(
        self,
        llm: BaseLLMProvider,
        current_messages: list[dict[str, str]],
        model: str,
    ) -> str:
        """Ask the model for one final synthesis after tool budget is exhausted.

        Some providers keep requesting more files even after the executor has
        gathered enough context. The user should still receive a useful answer,
        so the executor performs one extra no-tools synthesis turn before
        falling back to deterministic local summarization.
        """

        final_messages = [
            {
                "role": "system",
                "content": (
                    "You are AICodePilot finalizer. Tool calling is finished and no more tools "
                    "are available. Write a final user-facing answer only. Match the user's "
                    "language exactly; if the original request is Chinese, answer in Chinese."
                ),
            },
            {"role": "user", "content": self._build_final_summary_context(current_messages)},
        ]
        try:
            raw_response = llm.chat(list(final_messages), model=model)
            action = parse_agent_action(raw_response)
        except Exception as exc:
            logger.warning("Final summary synthesis failed error=%s", exc)
            return ""

        if action.type == "final" and action.answer:
            return action.answer
        logger.warning("Final summary synthesis returned non-final action type=%s tool=%s", action.type, action.tool)
        return ""

    def _build_final_summary_context(self, current_messages: list[dict[str, str]]) -> str:
        """Build a clean finalization prompt without previous tool-call JSON.

        The normal Agent loop stores assistant tool-call payloads in history so
        the next planning step has full context. For final synthesis, those JSON
        payloads can bias weaker provider responses into repeating tool calls.
        This context keeps only the original user request and the observed tool
        results.
        """

        user_request = ""
        tool_result_blocks: list[str] = []
        for message in current_messages:
            if message.get("role") != "user":
                continue
            content = message.get("content", "")
            if content.startswith("Tool result:\n"):
                tool_result_blocks.append(content.removeprefix("Tool result:\n"))
            elif not user_request:
                user_request = content

        return (
            "Original request:\n"
            f"{user_request}\n\n"
            "Tool results:\n" + "\n\n".join(tool_result_blocks) + "\n\nReturn exactly this JSON shape:\n"
            '{"type":"final","answer":"plain Markdown answer"}\n'
            "The answer must match the user's language. If the original request is Chinese, answer in Chinese. "
            "Include useful file paths and only line numbers that are explicitly present in the tool results. "
            "Do not invent approximate line numbers. Do not include tool-call JSON, XML tags, or private thinking."
        )

    def _looks_like_protocol_leak(self, answer: str) -> bool:
        return bool(_PROTOCOL_LEAK_PATTERN.search(answer))

    def _clean_final_answer(self, answer: str, tool_results: list[ToolResult], user_content: str) -> str:
        cleaned = answer.strip()
        if not cleaned or self._looks_like_protocol_leak(cleaned):
            return self._build_fallback_answer(tool_results, user_content)
        if self._contains_cjk(user_content) and not self._contains_cjk(cleaned):
            return self._build_fallback_answer(tool_results, user_content)
        return cleaned

    def _build_fallback_answer(self, tool_results: list[ToolResult], user_content: str = "") -> str:
        if not tool_results:
            if self._contains_cjk(user_content):
                return "模型没有返回可用的最终答案。"
            return "I could not produce a final answer from the model response."

        if self._contains_cjk(user_content):
            lines = ["我已经调用工具检查了项目，但模型没有返回可用的最终总结。基于工具结果，可以确认："]
        else:
            lines = ["I executed tools but the model did not return a usable final summary. Relevant results:"]

        for tool_result in tool_results:
            if tool_result.error:
                lines.append(f"- {tool_result.name}: {tool_result.error}")
                continue
            if tool_result.name == "read_file" and isinstance(tool_result.result, dict):
                relative_path = tool_result.result.get("relative_path") or tool_result.result.get("file_path")
                lines.append(self._describe_read_file_result(str(relative_path), user_content))
            elif tool_result.name == "list_files" and isinstance(tool_result.result, dict):
                files = [str(item) for item in tool_result.result.get("files", [])]
                agent_files = [file for file in files if "agent" in file.lower()][:8]
                if agent_files:
                    prefix = "- 发现与 Agent 相关的文件：" if self._contains_cjk(user_content) else "- Agent-related files found: "
                    lines.append(prefix + ", ".join(f"`{file}`" for file in agent_files))
                else:
                    if self._contains_cjk(user_content):
                        lines.append(f"- 已列出 {tool_result.result.get('count', len(files))} 个文件。")
                    else:
                        lines.append(f"- Listed {tool_result.result.get('count', len(files))} files.")
            elif tool_result.name == "project_tree" and isinstance(tool_result.result, dict):
                entries = [str(item) for item in tool_result.result.get("entries", [])[:20]]
                prefix = "- 项目结构片段：" if self._contains_cjk(user_content) else "- Project tree sample: "
                lines.append(prefix + ", ".join(f"`{entry}`" for entry in entries))
            elif tool_result.name == "find_files" and isinstance(tool_result.result, dict):
                matches = [str(item) for item in tool_result.result.get("matches", [])[:10]]
                prefix = "- 匹配到的文件：" if self._contains_cjk(user_content) else "- Matching files: "
                lines.append(prefix + ", ".join(f"`{match}`" for match in matches))
            elif tool_result.name == "retrieve_code" and isinstance(tool_result.result, dict):
                matches = tool_result.result.get("matches", [])[:5]
                for match in matches:
                    lines.append(f"- `{match.get('file_path')}` lines {match.get('start_line')}-{match.get('end_line')}")
            else:
                if self._contains_cjk(user_content):
                    lines.append(f"- `{tool_result.name}` 执行成功。")
                else:
                    lines.append(f"- Ran `{tool_result.name}` successfully.")
        return "\n".join(lines)

    def _describe_read_file_result(self, relative_path: str, user_content: str) -> str:
        """Return a human fallback sentence for a read file result.

        This keeps the product useful even when a provider refuses to produce
        the final summary after successful tool calls. The descriptions are
        intentionally conservative and tied to stable module responsibilities.
        """

        if not self._contains_cjk(user_content):
            return f"- Read `{relative_path}`."

        normalized_path = relative_path.replace("\\", "/")
        if normalized_path.endswith("backend/app/agent/agent.py") or normalized_path.endswith("agent.py"):
            return "- `backend/app/agent/agent.py` 是 Agent 门面入口，负责把用户输入封装成 `AgentRequest` 并交给执行器。"
        if normalized_path.endswith("backend/app/agent/executor.py") or normalized_path.endswith("executor.py"):
            return "- `backend/app/agent/executor.py` 是核心执行闭环，负责模型调用、工具执行、结果回填和最终答案生成。"
        if normalized_path.endswith("backend/app/agent/planner.py") or normalized_path.endswith("planner.py"):
            return "- `backend/app/agent/planner.py` 负责把模型原始输出解析为结构化 `AgentAction`。"
        if normalized_path.endswith("backend/app/agent/prompts.py") or normalized_path.endswith("prompts.py"):
            return "- `backend/app/agent/prompts.py` 定义系统提示词和工具调用输出约束。"
        if normalized_path.endswith("backend/app/tools/registry.py") or normalized_path.endswith("registry.py"):
            return "- `backend/app/tools/registry.py` 负责注册和查找 Agent 可调用工具。"
        return f"- 已读取 `{relative_path}`。"

    def _contains_cjk(self, content: str) -> bool:
        return any("\u4e00" <= character <= "\u9fff" for character in content)

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

    def _remember_turn(self, original_message: str, assistant_content: str) -> None:
        """Persist only the user's original question and the agent's final answer.

        Tool-call payloads are intentionally excluded from rolling memory: they are
        large, single-turn artifacts, and replaying them into later prompts biases
        weaker providers into repeating tool calls unnecessarily. The final answer
        already encodes whatever information the tools surfaced.

        We store `original_message` (the raw user text) rather than the decorated
        `user_content` that includes the project_path prefix—otherwise multi-turn
        prompts accumulate redundant path prefixes in every memory turn.
        """

        if self.memory is None:
            return
        if not original_message.strip():
            return
        self.memory.add_user_message(original_message)
        if assistant_content.strip():
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
