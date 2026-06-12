import json
import re
from collections.abc import Iterator
from typing import Any

from app.agent.planner import parse_agent_action
from app.agent.prompts import build_system_prompt, build_system_prompt_for_tool_calling
from app.agent.schemas import AgentAction, AgentRequest, AgentResponse, CodeReference, PatchSuggestion, ToolResult
from app.core.config import Settings, get_settings
from app.core.exceptions import AICodePilotError
from app.core.logger import get_logger
from app.llm.base import BaseLLMProvider
from app.llm.factory import LLMProviderFactory
from app.llm.schemas import ChatResult, LLMToolCall
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
    "propose_patch",
}
# Fallback constant used when settings.agent_max_steps is unavailable.
_MAX_TOOL_STEPS = 10
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

    def _resolve_request_settings(self, request: AgentRequest, provider_name: str) -> Settings:
        """Apply any per-request API key / base_url onto a settings copy.

        The frontend sends bring-your-own-key credentials in the request body.
        These must override the process-wide settings transiently — never mutate
        the shared singleton — so concurrent requests with different keys stay
        isolated. When the request carries no credential, the base settings (env
        / .env) are returned unchanged.
        """

        if not request.api_key and not request.base_url:
            return self.settings
        return self.settings.with_provider_credentials(
            provider_name,
            api_key=request.api_key,
            base_url=request.base_url,
        )

    def run(self, request: AgentRequest) -> AgentResponse:
        provider_name = (request.provider or self.settings.llm_provider).strip().lower()
        run_settings = self._resolve_request_settings(request, provider_name)
        model = request.model or run_settings.default_model_for_provider(provider_name)
        llm = self.llm_provider or LLMProviderFactory.create(provider_name, settings=run_settings)

        tools_schema = self.registry.describe_tools()
        user_content = self._build_user_content(request)
        max_steps = getattr(self.settings, "agent_max_steps", _MAX_TOOL_STEPS)

        logger.info(
            "Agent run started provider=%s model=%s project_path_present=%s memory_enabled=%s max_steps=%s",
            provider_name,
            model,
            bool(request.project_path),
            self.memory is not None,
            max_steps,
        )

        tool_results: list[ToolResult] = []
        answer = ""

        # --- Primary path: native tool calling (OpenAI function-calling protocol) ---
        # Falls back to the text protocol if the provider raises NotImplementedError.
        try:
            system_prompt = build_system_prompt_for_tool_calling()
            messages = self._build_messages(system_prompt, user_content)
            answer, tool_results = self._run_tool_calling_loop(
                llm=llm,
                messages=messages,
                tools_schema=tools_schema,
                request=request,
                model=model,
                max_steps=max_steps,
            )
        except NotImplementedError:
            logger.warning(
                "Provider %s does not support tool calling, falling back to text protocol",
                provider_name,
            )
            system_prompt = build_system_prompt(tools_schema)
            messages = self._build_messages(system_prompt, user_content)
            answer, tool_results = self._run_text_protocol_loop(
                llm=llm,
                messages=messages,
                request=request,
                model=model,
                max_steps=max_steps,
            )

        answer = self._clean_final_answer(answer, tool_results, user_content)
        if not answer:
            answer = self._build_fallback_answer(tool_results, user_content)

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

    def run_stream(self, request: AgentRequest) -> Iterator[Any]:
        """Stream agent execution as AgentEvent objects (T-6).

        Yields events for each significant step:
          thinking    — emitted at the start of each LLM call step
          tool_start  — emitted before a tool is executed
          tool_end    — emitted after a tool completes (with error field)
          done        — final event with complete answer + metadata
          error       — emitted if an unrecoverable exception occurs

        The implementation re-uses the same setup as run() but drives the tool
        calling loop inline so it can yield events between steps. Falls back to
        a single done event when the provider does not support tool calling.
        """

        from app.agent.events import AgentEvent

        provider_name = (request.provider or self.settings.llm_provider).strip().lower()
        run_settings = self._resolve_request_settings(request, provider_name)
        model = request.model or run_settings.default_model_for_provider(provider_name)
        llm = self.llm_provider or LLMProviderFactory.create(provider_name, settings=run_settings)

        tools_schema = self.registry.describe_tools()
        user_content = self._build_user_content(request)
        max_steps = getattr(self.settings, "agent_max_steps", _MAX_TOOL_STEPS)

        tool_results: list[ToolResult] = []
        answer = ""

        try:
            system_prompt = build_system_prompt_for_tool_calling()
            messages = self._build_messages(system_prompt, user_content)

            last_call_signature: tuple[str, str] | None = None

            for step in range(1, max_steps + 1):
                yield AgentEvent(type="thinking", data={"step": step})

                result: ChatResult = llm.chat_with_tools(list(messages), tools=tools_schema, model=model)

                if result.is_final:
                    answer = result.content or ""
                    break

                assistant_msg: dict[str, Any] = {
                    "role": "assistant",
                    "content": result.content,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.name,
                                "arguments": json.dumps(tc.arguments, ensure_ascii=False),
                            },
                        }
                        for tc in result.tool_calls
                    ],
                }
                messages.append(assistant_msg)

                for tc in result.tool_calls:
                    call_sig = (tc.name, json.dumps(tc.arguments, sort_keys=True))
                    if call_sig == last_call_signature:
                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tc.id,
                                "content": "Error: identical tool call detected. Please provide a final answer.",
                            }
                        )
                        logger.warning("Stream: loop detected tool=%s step=%s", tc.name, step)
                        continue
                    last_call_signature = call_sig

                    yield AgentEvent(type="tool_start", data={"tool": tc.name, "arguments": tc.arguments})
                    tool_result = self._execute_native_tool_call(tc, request)
                    tool_results.append(tool_result)
                    yield AgentEvent(
                        type="tool_end",
                        data={"tool": tc.name, "error": tool_result.error},
                    )

                    result_content = json.dumps(tool_result.model_dump(), ensure_ascii=False, default=str)
                    messages.append({"role": "tool", "tool_call_id": tc.id, "content": result_content})

            else:
                # Budget exhausted
                answer = self._request_final_summary(llm, messages, model)

        except NotImplementedError:
            # Provider does not support tool calling — run synchronously and emit done
            logger.warning("Stream: provider %s has no tool calling, falling back", provider_name)
            system_prompt = build_system_prompt(tools_schema)
            messages = self._build_messages(system_prompt, user_content)
            answer, tool_results = self._run_text_protocol_loop(
                llm=llm, messages=messages, request=request, model=model, max_steps=max_steps
            )

        answer = self._clean_final_answer(answer, tool_results, user_content)
        if not answer:
            answer = self._build_fallback_answer(tool_results, user_content)

        self._remember_turn(request.message, answer)

        references = self._extract_references_from_results(tool_results)
        patch_suggestions = self._extract_patch_suggestions_from_results(tool_results)

        yield AgentEvent(
            type="done",
            data={
                "answer": answer,
                "provider": provider_name,
                "model": model,
                "tool_calls": [tc.model_dump() for tc in tool_results],
                "references": [r.model_dump() for r in references],
                "patch_suggestions": [p.model_dump() for p in patch_suggestions],
            },
        )

    # ------------------------------------------------------------------
    # Tool-calling loop (primary path: OpenAI function-calling protocol)
    # ------------------------------------------------------------------

    def _run_tool_calling_loop(
        self,
        llm: BaseLLMProvider,
        messages: list[dict[str, Any]],
        tools_schema: list[dict[str, Any]],
        request: AgentRequest,
        model: str,
        max_steps: int,
    ) -> tuple[str, list[ToolResult]]:
        """Execute the ReAct loop using native tool_calls from the provider.

        Each iteration the model returns either tool_calls to execute or a final
        content string. We stop on final content, on hitting max_steps, or when
        the model produces an identical back-to-back call (loop detection). Tool
        results are appended using the OpenAI multi-turn format (role=tool +
        tool_call_id) so the model can correlate each result to its request.
        """

        tool_results: list[ToolResult] = []
        # Track (tool_name, frozen_args) to detect identical consecutive calls.
        last_call_signature: tuple[str, str] | None = None

        for step in range(1, max_steps + 1):
            result: ChatResult = llm.chat_with_tools(list(messages), tools=tools_schema, model=model)

            if result.is_final:
                return result.content or "", tool_results

            # Append the assistant message with its tool_calls so the model can
            # correlate result messages back to each call id on the next turn.
            assistant_msg: dict[str, Any] = {
                "role": "assistant",
                "content": result.content,  # may be None per OpenAI spec
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.name,
                            "arguments": json.dumps(tc.arguments, ensure_ascii=False),
                        },
                    }
                    for tc in result.tool_calls
                ],
            }
            messages.append(assistant_msg)

            for tc in result.tool_calls:
                call_sig = (tc.name, json.dumps(tc.arguments, sort_keys=True))
                if call_sig == last_call_signature:
                    # Identical back-to-back call: the model is stuck in a loop.
                    # Inject an error result to steer it toward a final answer.
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "content": (
                                "Error: identical tool call detected. "
                                "Please provide a final answer based on the results gathered so far."
                            ),
                        }
                    )
                    logger.warning("Loop detected tool=%s step=%s", tc.name, step)
                    continue
                last_call_signature = call_sig

                tool_result = self._execute_native_tool_call(tc, request)
                tool_results.append(tool_result)
                result_content = json.dumps(tool_result.model_dump(), ensure_ascii=False, default=str)
                messages.append({"role": "tool", "tool_call_id": tc.id, "content": result_content})
                logger.info("Tool step=%s tool=%s error=%s", step, tool_result.name, bool(tool_result.error))

        # Budget exhausted without a final answer; ask the model to synthesize.
        return self._request_final_summary(llm, messages, model), tool_results

    def _execute_native_tool_call(self, tc: LLMToolCall, request: AgentRequest) -> ToolResult:
        """Execute a single native tool call and return its ToolResult."""

        arguments = dict(tc.arguments)
        if request.project_path and tc.name in _PROJECT_PATH_TOOLS and "project_path" not in arguments:
            arguments["project_path"] = request.project_path
        logger.info("Tool selected name=%s arg_keys=%s", tc.name, sorted(arguments))
        tool = self.registry.get(tc.name)
        result = ToolResult(name=tc.name, arguments=arguments)
        try:
            result.result = tool.run(**arguments)
        except Exception as exc:
            result.error = str(exc)
            logger.warning("Tool failed name=%s error=%s", tc.name, exc)
        else:
            logger.info("Tool execution completed tool=%s", tc.name)
        return result

    # ------------------------------------------------------------------
    # Text-protocol loop (fallback: regex planner, for providers without
    # native function calling support)
    # ------------------------------------------------------------------

    def _run_text_protocol_loop(
        self,
        llm: BaseLLMProvider,
        messages: list[dict[str, Any]],
        request: AgentRequest,
        model: str,
        max_steps: int,
    ) -> tuple[str, list[ToolResult]]:
        """Execute the legacy text-protocol loop using the regex planner.

        This path is the fallback for providers that do not implement
        chat_with_tools. It is kept intact so AICodePilot remains usable with
        any OpenAI-compatible endpoint that lacks function-calling support.
        """

        tool_results: list[ToolResult] = []
        answer = ""
        current_messages = list(messages)

        for step in range(1, max_steps + 1):
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
                "Agent tool step completed step=%s tool=%s tool_error=%s",
                step,
                tool_result.name,
                bool(tool_result.error),
            )
        else:
            answer = ""

        if not answer and tool_results:
            answer = self._request_final_summary(llm, current_messages, model)

        return answer, tool_results

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

    # ------------------------------------------------------------------
    # Shared helpers
    # ------------------------------------------------------------------

    def _request_final_summary(
        self,
        llm: BaseLLMProvider,
        current_messages: list[dict[str, Any]],
        model: str,
    ) -> str:
        """Ask the model for one final synthesis after tool budget is exhausted."""

        final_messages: list[dict[str, Any]] = [
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
        logger.warning(
            "Final summary synthesis returned non-final action type=%s tool=%s",
            action.type,
            action.tool,
        )
        return ""

    def _build_final_summary_context(self, current_messages: list[dict[str, Any]]) -> str:
        user_request = ""
        tool_result_blocks: list[str] = []
        for message in current_messages:
            if message.get("role") not in {"user", "tool"}:
                continue
            content = str(message.get("content") or "")
            if message.get("role") == "tool":
                tool_result_blocks.append(content)
            elif content.startswith("Tool result:\n"):
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
        """Generic fallback description for a read file result.

        Intentionally project-agnostic: hardcoding descriptions for specific files
        only helped on this repository and produced misleading output on any other
        codebase. The file path gives the user a neutral, accurate signal.
        """

        if self._contains_cjk(user_content):
            return f"- 已读取 `{relative_path}`。"
        return f"- Read `{relative_path}`."

    def _contains_cjk(self, content: str) -> bool:
        return any("一" <= character <= "鿿" for character in content)

    def _build_messages(self, system_prompt: str, user_content: str) -> list[dict[str, Any]]:
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
                suggestions.append(PatchSuggestion.model_validate(item))
        return suggestions

    def _extract_patch_suggestions_from_results(self, tool_results: list[ToolResult]) -> list[PatchSuggestion]:
        suggestions: list[PatchSuggestion] = []
        for tool_result in tool_results:
            suggestions.extend(self._extract_patch_suggestions(tool_result))
        return suggestions
