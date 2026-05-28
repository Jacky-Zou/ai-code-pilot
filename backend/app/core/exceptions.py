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
