from typing import Any

import httpx
import pytest

from app.core.exceptions import LLMProviderError
from app.llm.client import extract_chat_content, post_chat_completion


class FakeHTTPResponse:
    def __init__(self, payload: Any, status_code: int = 200, text: str = "ok") -> None:
        self._payload = payload
        self.status_code = status_code
        self.text = text

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            request = httpx.Request("POST", "https://provider.test/chat/completions")
            response = httpx.Response(self.status_code, request=request, text=self.text)
            raise httpx.HTTPStatusError("provider error", request=request, response=response)

    def json(self) -> Any:
        return self._payload


class FakeHTTPClient:
    calls: list[dict[str, Any]] = []
    response: FakeHTTPResponse = FakeHTTPResponse({"choices": [{"message": {"content": "ok"}}]})
    request_error: httpx.RequestError | None = None

    def __init__(self, timeout: float) -> None:
        self.timeout = timeout

    def __enter__(self) -> "FakeHTTPClient":
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        return None

    def post(self, url: str, headers: dict[str, str], json: dict[str, Any]) -> FakeHTTPResponse:
        self.calls.append({"url": url, "headers": headers, "json": json, "timeout": self.timeout})
        if self.request_error is not None:
            raise self.request_error
        return self.response


@pytest.fixture(autouse=True)
def reset_fake_http_client() -> None:
    FakeHTTPClient.calls = []
    FakeHTTPClient.response = FakeHTTPResponse({"choices": [{"message": {"content": "ok"}}]})
    FakeHTTPClient.request_error = None


def test_post_chat_completion_sends_openai_compatible_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(httpx, "Client", FakeHTTPClient)

    data = post_chat_completion(
        base_url="https://provider.test/v1/",
        api_key="secret",
        model="demo-model",
        messages=[{"role": "user", "content": "hello"}],
        temperature=0.2,
    )

    assert data["choices"][0]["message"]["content"] == "ok"
    call = FakeHTTPClient.calls[0]
    assert call["url"] == "https://provider.test/v1/chat/completions"
    assert call["headers"]["Authorization"] == "Bearer secret"
    assert call["json"]["model"] == "demo-model"
    assert call["json"]["temperature"] == 0.2


def test_post_chat_completion_wraps_http_status_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(httpx, "Client", FakeHTTPClient)
    FakeHTTPClient.response = FakeHTTPResponse(payload={"error": "bad"}, status_code=429, text="rate limited")

    with pytest.raises(LLMProviderError, match="HTTP 429"):
        post_chat_completion(
            base_url="https://provider.test/v1",
            api_key="secret",
            model="demo-model",
            messages=[],
        )


def test_post_chat_completion_rejects_non_object_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(httpx, "Client", FakeHTTPClient)
    FakeHTTPClient.response = FakeHTTPResponse(payload=["not", "an", "object"])

    with pytest.raises(LLMProviderError, match="invalid response payload"):
        post_chat_completion(
            base_url="https://provider.test/v1",
            api_key="secret",
            model="demo-model",
            messages=[],
        )


def test_extract_chat_content_requires_text_content() -> None:
    with pytest.raises(LLMProviderError, match="message content is not text"):
        extract_chat_content({"choices": [{"message": {"content": [{"type": "text"}]}}]})


def test_extract_chat_content_requires_expected_shape() -> None:
    with pytest.raises(LLMProviderError, match="does not contain message content"):
        extract_chat_content({"choices": []})
