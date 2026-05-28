from typing import Any

import httpx

from app.core.exceptions import LLMProviderError


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
    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise LLMProviderError("LLM provider response does not contain message content") from exc

    if not isinstance(content, str):
        raise LLMProviderError("LLM provider message content is not text")
    return content
