import json
from typing import Any

import httpx

from app.core.exceptions import LLMProviderError
from app.llm.schemas import ChatResult, LLMToolCall


def post_chat_completion(
    *,
    base_url: str,
    api_key: str,
    model: str,
    messages: list[dict[str, str]],
    timeout: float = 60.0,
    **kwargs: Any,
) -> dict[str, Any]:
    url = f"{base_url.rstrip('/')}/chat/completions"
    payload: dict[str, Any] = {"model": model, "messages": messages}
    payload.update(kwargs)
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPStatusError as exc:
        status_code = exc.response.status_code
        raise LLMProviderError(f"LLM provider returned HTTP {status_code}: {exc.response.text}") from exc
    except httpx.RequestError as exc:
        raise LLMProviderError(f"LLM provider request failed: {exc}") from exc

    if not isinstance(data, dict):
        raise LLMProviderError("LLM provider returned an invalid response payload")
    return data


def extract_chat_content(data: dict[str, Any]) -> str:
    """Extract plain text content from an OpenAI-compatible chat completion response.

    Kept for backward compatibility with the text-protocol fallback path and
    existing tests. New code should prefer extract_chat_result.
    """

    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise LLMProviderError("LLM provider response does not contain message content") from exc

    if not isinstance(content, str):
        raise LLMProviderError("LLM provider message content is not text")
    return content


def extract_chat_result(data: dict[str, Any]) -> ChatResult:
    """Extract a ChatResult from an OpenAI-compatible chat completion response.

    The OpenAI protocol places tool_calls on the message alongside content.
    When the model invokes tools, content is typically null. When it returns a
    final text answer, tool_calls is absent or empty. Both states are valid
    and this function handles them uniformly.
    """

    try:
        message: dict[str, Any] = data["choices"][0]["message"]
    except (KeyError, IndexError, TypeError) as exc:
        raise LLMProviderError("LLM provider response does not contain a message") from exc

    content: str | None = message.get("content")
    raw_tool_calls: list[dict[str, Any]] = message.get("tool_calls") or []
    tool_calls: list[LLMToolCall] = []

    for raw in raw_tool_calls:
        try:
            func = raw["function"]
            arguments: dict[str, Any] = json.loads(func.get("arguments") or "{}")
            tool_calls.append(LLMToolCall(id=raw["id"], name=func["name"], arguments=arguments))
        except (KeyError, json.JSONDecodeError) as exc:
            raise LLMProviderError(f"Malformed tool_call in LLM response: {raw}") from exc

    if not tool_calls and content is None:
        raise LLMProviderError("LLM provider returned neither content nor tool_calls")

    return ChatResult(content=content, tool_calls=tool_calls)
