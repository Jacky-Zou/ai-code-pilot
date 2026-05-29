from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from pydantic import ValidationError


class AICodePilotError(Exception):
    """Base exception for AICodePilot domain errors."""

    error_code = "AICODEPILOT_ERROR"


class ConfigurationError(AICodePilotError):
    """Raised when required runtime configuration is missing or invalid."""

    error_code = "CONFIGURATION_ERROR"


class UnsupportedProviderError(AICodePilotError):
    """Raised when a requested LLM provider is not supported."""

    error_code = "UNSUPPORTED_PROVIDER"


class LLMProviderError(AICodePilotError):
    """Raised when an LLM provider request fails."""

    error_code = "LLM_PROVIDER_ERROR"


class ToolError(AICodePilotError):
    """Raised when a tool cannot complete a requested operation."""

    error_code = "TOOL_ERROR"


_DOMAIN_STATUS_CODES: dict[type[AICodePilotError], int] = {
    ConfigurationError: status.HTTP_500_INTERNAL_SERVER_ERROR,
    UnsupportedProviderError: status.HTTP_400_BAD_REQUEST,
    LLMProviderError: status.HTTP_502_BAD_GATEWAY,
    ToolError: status.HTTP_400_BAD_REQUEST,
    AICodePilotError: status.HTTP_400_BAD_REQUEST,
}


def register_exception_handlers(app: FastAPI) -> None:
    """Register consistent JSON error responses for the FastAPI service."""

    app.add_exception_handler(AICodePilotError, _domain_error_handler)
    app.add_exception_handler(RequestValidationError, _request_validation_error_handler)
    app.add_exception_handler(ValidationError, _pydantic_validation_error_handler)


async def _domain_error_handler(request: Request, exc: Exception) -> JSONResponse:
    domain_error = exc if isinstance(exc, AICodePilotError) else AICodePilotError(str(exc))
    status_code = _status_code_for_domain_error(domain_error)
    return _error_response(
        request=request,
        status_code=status_code,
        error=domain_error.__class__.__name__,
        code=domain_error.error_code,
        detail=str(domain_error),
    )


async def _request_validation_error_handler(request: Request, exc: Exception) -> JSONResponse:
    validation_error = _coerce_validation_error(exc)
    return _error_response(
        request=request,
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        error="ValidationError",
        code="VALIDATION_ERROR",
        detail=_safe_validation_errors(validation_error),
    )


async def _pydantic_validation_error_handler(request: Request, exc: Exception) -> JSONResponse:
    validation_error = _coerce_validation_error(exc)
    return _error_response(
        request=request,
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        error="ValidationError",
        code="VALIDATION_ERROR",
        detail=_safe_validation_errors(validation_error),
    )


def _status_code_for_domain_error(exc: AICodePilotError) -> int:
    for error_type, status_code in _DOMAIN_STATUS_CODES.items():
        if isinstance(exc, error_type):
            return status_code
    return status.HTTP_400_BAD_REQUEST


def _error_response(
    request: Request,
    status_code: int,
    error: str,
    code: str,
    detail: str | list[dict[str, Any]],
) -> JSONResponse:
    """Build the public error payload shared by all API handlers.

    `error` keeps the human-readable class-style name used by earlier API
    responses. `code` gives clients a stable machine-readable value, while
    `request_id` lets logs and responses be correlated when a caller sends
    `X-Request-ID`.
    """

    payload: dict[str, Any] = {
        "error": error,
        "code": code,
        "detail": detail,
    }
    request_id = request.headers.get("X-Request-ID")
    if request_id:
        payload["request_id"] = request_id

    return JSONResponse(
        status_code=status_code,
        content=payload,
    )


def _coerce_validation_error(exc: Exception) -> RequestValidationError | ValidationError:
    if isinstance(exc, (RequestValidationError, ValidationError)):
        return exc
    raise TypeError(f"Expected validation error, got {type(exc).__name__}")


def _safe_validation_errors(exc: RequestValidationError | ValidationError) -> list[dict[str, Any]]:
    """Return Pydantic validation errors in JSON-safe form.

    Some validation inputs can contain objects such as `Path` or exception
    instances. FastAPI's encoder normalizes those values before they reach the
    response body, keeping the unified error handler from failing while handling
    a validation failure.
    """

    return jsonable_encoder(exc.errors())
