from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError


class AICodePilotError(Exception):
    """Base exception for AICodePilot domain errors."""


class ConfigurationError(AICodePilotError):
    """Raised when required runtime configuration is missing or invalid."""


class UnsupportedProviderError(AICodePilotError):
    """Raised when a requested LLM provider is not supported."""


class LLMProviderError(AICodePilotError):
    """Raised when an LLM provider request fails."""


class ToolError(AICodePilotError):
    """Raised when a tool cannot complete a requested operation."""


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
        status_code=status_code,
        error=domain_error.__class__.__name__,
        detail=str(domain_error),
    )


async def _request_validation_error_handler(request: Request, exc: Exception) -> JSONResponse:
    validation_error = _coerce_validation_error(exc)
    return _error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        error="ValidationError",
        detail=validation_error.errors(),
    )


async def _pydantic_validation_error_handler(request: Request, exc: Exception) -> JSONResponse:
    validation_error = _coerce_validation_error(exc)
    return _error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        error="ValidationError",
        detail=validation_error.errors(),
    )


def _status_code_for_domain_error(exc: AICodePilotError) -> int:
    for error_type, status_code in _DOMAIN_STATUS_CODES.items():
        if isinstance(exc, error_type):
            return status_code
    return status.HTTP_400_BAD_REQUEST


def _error_response(status_code: int, error: str, detail: str | list[dict[str, Any]]) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": error, "detail": detail},
    )


def _coerce_validation_error(exc: Exception) -> RequestValidationError | ValidationError:
    if isinstance(exc, (RequestValidationError, ValidationError)):
        return exc
    raise TypeError(f"Expected validation error, got {type(exc).__name__}")
