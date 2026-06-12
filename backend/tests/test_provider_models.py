"""Tests for the /api/providers/models endpoint and credential override flow."""

import json
from typing import Any

import httpx
import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings
from app.core.exceptions import LLMProviderError
from app.llm.client import list_available_models
from app.main import create_app

# ---------------------------------------------------------------------------
# list_available_models unit tests
# ---------------------------------------------------------------------------


class _FakeModelsResponse:
    def __init__(self, payload: Any, status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code
        self.text = json.dumps(payload)

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            request = httpx.Request("GET", "https://provider.test/models")
            response = httpx.Response(self.status_code, request=request, text=self.text)
            raise httpx.HTTPStatusError("error", request=request, response=response)

    def json(self) -> Any:
        return self._payload


class _FakeGetClient:
    def __init__(self, response: _FakeModelsResponse) -> None:
        self._response = response

    def __enter__(self) -> "_FakeGetClient":
        return self

    def __exit__(self, *_: object) -> None:
        pass

    def get(self, url: str, headers: dict[str, str]) -> _FakeModelsResponse:
        return self._response


def test_list_available_models_returns_sorted_ids(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = {"data": [{"id": "model-b"}, {"id": "model-a"}, {"id": "model-a"}]}
    monkeypatch.setattr(httpx, "Client", lambda timeout: _FakeGetClient(_FakeModelsResponse(payload)))
    result = list_available_models(base_url="https://api.test", api_key="sk-test")
    assert result == ["model-a", "model-b"]  # sorted + deduplicated


def test_list_available_models_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(httpx, "Client", lambda timeout: _FakeGetClient(_FakeModelsResponse({}, status_code=401)))
    with pytest.raises(LLMProviderError, match="401"):
        list_available_models(base_url="https://api.test", api_key="bad-key")


def test_list_available_models_skips_non_string_ids(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = {"data": [{"id": "good"}, {"id": 42}, {"other": "no-id"}]}
    monkeypatch.setattr(httpx, "Client", lambda timeout: _FakeGetClient(_FakeModelsResponse(payload)))
    result = list_available_models(base_url="https://api.test", api_key="sk")
    assert result == ["good"]


# ---------------------------------------------------------------------------
# Settings.with_provider_credentials unit tests
# ---------------------------------------------------------------------------


def test_with_provider_credentials_openai(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "original")
    get_settings.cache_clear()
    settings = get_settings()
    overridden = settings.with_provider_credentials("openai", api_key="new-key")
    assert overridden.openai_api_key == "new-key"
    assert settings.openai_api_key == "original"  # original unchanged


def test_with_provider_credentials_noop_when_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    get_settings.cache_clear()
    settings = get_settings()
    same = settings.with_provider_credentials("deepseek", api_key="", base_url="")
    assert same is settings


def test_with_provider_credentials_unsupported_raises() -> None:
    settings = Settings()
    with pytest.raises(ValueError, match="Unsupported"):
        settings.with_provider_credentials("unknownprovider", api_key="k")


# ---------------------------------------------------------------------------
# POST /api/providers/models integration test
# ---------------------------------------------------------------------------


def test_list_models_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = {"data": [{"id": "deepseek-chat"}, {"id": "deepseek-reasoner"}]}
    monkeypatch.setattr(httpx, "Client", lambda timeout: _FakeGetClient(_FakeModelsResponse(payload)))
    app = create_app()
    with TestClient(app) as client:
        resp = client.post("/api/providers/models", json={"provider": "deepseek", "api_key": "sk-test"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["provider"] == "deepseek"
    assert "deepseek-chat" in data["models"]


def test_list_models_endpoint_unsupported_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    app = create_app()
    with TestClient(app) as client:
        resp = client.post("/api/providers/models", json={"provider": "fakevendor", "api_key": "sk"})
    assert resp.status_code == 422 or resp.status_code == 400


def test_list_models_endpoint_empty_key_rejected() -> None:
    app = create_app()
    with TestClient(app) as client:
        resp = client.post("/api/providers/models", json={"provider": "deepseek", "api_key": ""})
    assert resp.status_code == 422  # Pydantic min_length=1 rejects empty key
