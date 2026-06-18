from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

SUPPORTED_LLM_PROVIDERS = {"openai", "deepseek"}
SUPPORTED_EMBEDDING_PROVIDERS = {"openai", "local"}
SUPPORTED_VECTOR_STORE_BACKENDS = {"chroma", "json", "memory"}
SUPPORTED_LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
PROJECT_ROOT = Path(__file__).resolve().parents[3]
ROOT_ENV_FILE = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    """Application settings loaded from environment variables and `.env`."""

    app_name: str = Field(default="AICodePilot", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    llm_provider: str = Field(default="openai", alias="LLM_PROVIDER")
    llm_model: str | None = Field(default="gpt-5.2", alias="LLM_MODEL")

    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_base_url: str = Field(default="https://api.openai.com/v1", alias="OPENAI_BASE_URL")
    openai_model: str = Field(default="gpt-5.2", alias="OPENAI_MODEL")

    deepseek_api_key: str | None = Field(default=None, alias="DEEPSEEK_API_KEY")
    deepseek_base_url: str = Field(default="https://api.deepseek.com", alias="DEEPSEEK_BASE_URL")
    deepseek_model: str = Field(default="deepseek-v4-pro", alias="DEEPSEEK_MODEL")

    embedding_provider: str = Field(default="local", alias="EMBEDDING_PROVIDER")
    embedding_model: str = Field(default="text-embedding-3-small", alias="EMBEDDING_MODEL")

    vector_store_path: Path = Field(default=Path("./data/vector_store"), alias="VECTOR_STORE_PATH")
    vector_store_backend: str = Field(default="chroma", alias="VECTOR_STORE_BACKEND")
    projects_host_root: str | None = Field(default=None, alias="PROJECTS_HOST_ROOT")
    projects_container_root: str | None = Field(default="/workspace", alias="PROJECTS_CONTAINER_ROOT")
    cors_allowed_origins: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000",
        alias="CORS_ALLOWED_ORIGINS",
    )

    # Agent execution controls
    # Maximum tool-call steps per agent run. Higher values allow complex
    # multi-file tasks to complete without hitting the budget, but also increase
    # the blast radius of a misbehaving model. Configurable via AGENT_MAX_STEPS.
    agent_max_steps: int = Field(default=10, ge=3, le=30, alias="AGENT_MAX_STEPS")

    # Shell tool gate. Disabled by default to reduce the attack surface: an
    # LLM-controlled shell command is a significant security risk. Set
    # ENABLE_SHELL_TOOL=true only in trusted local environments.
    enable_shell_tool: bool = Field(default=False, alias="ENABLE_SHELL_TOOL")

    # SQLite persistence. The default path is relative to the project root so
    # the database file lives in data/ alongside vector store artifacts.
    database_url: str = Field(
        default="sqlite:///./data/aicodepilot.db",
        alias="DATABASE_URL",
    )

    model_config = SettingsConfigDict(
        env_file=(ROOT_ENV_FILE, ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    @field_validator("llm_provider", "embedding_provider", "vector_store_backend")
    @classmethod
    def normalize_config_choice(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not normalized:
            raise ValueError("configuration value cannot be empty")
        return normalized

    @field_validator("log_level")
    @classmethod
    def normalize_log_level(cls, value: str) -> str:
        normalized = value.strip().upper()
        if normalized not in SUPPORTED_LOG_LEVELS:
            supported = ", ".join(sorted(SUPPORTED_LOG_LEVELS))
            raise ValueError(f"Unsupported LOG_LEVEL '{value}'. Supported values: {supported}")
        return normalized

    @field_validator("openai_base_url", "deepseek_base_url")
    @classmethod
    def validate_base_url(cls, value: str) -> str:
        normalized = value.strip().rstrip("/")
        if not normalized:
            raise ValueError("base URL cannot be empty")
        if not normalized.startswith(("http://", "https://")):
            raise ValueError("base URL must start with http:// or https://")
        return normalized

    @field_validator("cors_allowed_origins")
    @classmethod
    def validate_cors_allowed_origins(cls, value: str) -> str:
        cls._parse_cors_allowed_origins(value)
        return value

    @property
    def cors_allowed_origin_list(self) -> list[str]:
        return self._parse_cors_allowed_origins(self.cors_allowed_origins)

    @staticmethod
    def _parse_cors_allowed_origins(value: str) -> list[str]:
        origins = [item.strip().rstrip("/") for item in value.split(",")]
        parsed = [origin for origin in origins if origin]
        if not parsed:
            raise ValueError("CORS_ALLOWED_ORIGINS must contain at least one origin")
        for origin in parsed:
            if origin != "*" and not origin.startswith(("http://", "https://")):
                raise ValueError("CORS origins must start with http:// or https://")
        return parsed

    @field_validator("llm_model", mode="before")
    @classmethod
    def normalize_optional_model_override(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalized = value.strip()
        return normalized or None

    @field_validator("openai_model", "deepseek_model", "embedding_model")
    @classmethod
    def validate_required_model_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("model name cannot be empty")
        return normalized

    @field_validator("projects_host_root", "projects_container_root")
    @classmethod
    def normalize_optional_path_string(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().rstrip("\\/")
        return normalized or None

    @model_validator(mode="after")
    def validate_supported_runtime_choices(self) -> "Settings":
        """Fail fast when env vars select a backend the app cannot create.

        Provider factories still keep their own defensive checks, but validating
        here gives users a clearer startup/configuration error and prevents the
        API, Agent, or RAG layers from receiving half-normalized settings.
        """

        self._ensure_supported("LLM_PROVIDER", self.llm_provider, SUPPORTED_LLM_PROVIDERS)
        self._ensure_supported("EMBEDDING_PROVIDER", self.embedding_provider, SUPPORTED_EMBEDDING_PROVIDERS)
        self._ensure_supported("VECTOR_STORE_BACKEND", self.vector_store_backend, SUPPORTED_VECTOR_STORE_BACKENDS)

        if self.llm_model is None:
            self.llm_model = self.default_model_for_provider(self.llm_provider)
        if self.vector_store_path.as_posix().strip() in {"", "."}:
            raise ValueError("VECTOR_STORE_PATH must point to a project data directory")
        if not self.vector_store_path.is_absolute():
            self.vector_store_path = PROJECT_ROOT / self.vector_store_path
        self.database_url = self._normalize_database_url(self.database_url)
        return self

    @staticmethod
    def _normalize_database_url(value: str) -> str:
        if value in {"sqlite://", "sqlite:///:memory:"}:
            return value
        prefix = "sqlite:///"
        if not value.startswith(prefix):
            return value
        db_path = value.removeprefix(prefix)
        if not db_path or db_path.startswith(":memory:"):
            return value
        path = Path(db_path)
        if path.is_absolute():
            return value
        return f"{prefix}{(PROJECT_ROOT / path).as_posix()}"

    def default_model_for_provider(self, provider_name: str | None = None) -> str:
        provider = (provider_name or self.llm_provider).strip().lower()
        if provider == "openai":
            return self.openai_model
        if provider == "deepseek":
            return self.deepseek_model
        raise ValueError(f"Unsupported LLM provider: {provider}")

    def base_url_for_provider(self, provider_name: str) -> str:
        """Return the OpenAI-compatible base URL for a provider.

        Used by the model-discovery endpoint so a single helper drives both the
        ``/models`` catalog call and chat completions for any supported vendor.
        """

        provider = provider_name.strip().lower()
        if provider == "openai":
            return self.openai_base_url
        if provider == "deepseek":
            return self.deepseek_base_url
        raise ValueError(f"Unsupported LLM provider: {provider}")

    def with_provider_credentials(
        self,
        provider_name: str,
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> "Settings":
        """Return a copy with a provider's key/base_url overridden for one request.

        The frontend stores API keys in the browser and sends them per request
        (bring-your-own-key), so credentials must be injected transiently rather
        than mutating the process-wide settings singleton. A blank override is
        ignored, preserving any value already present in the environment.
        """

        provider = provider_name.strip().lower()
        updates: dict[str, str] = {}
        key = (api_key or "").strip()
        url = (base_url or "").strip().rstrip("/")
        if provider == "openai":
            if key:
                updates["openai_api_key"] = key
            if url:
                updates["openai_base_url"] = url
        elif provider == "deepseek":
            if key:
                updates["deepseek_api_key"] = key
            if url:
                updates["deepseek_base_url"] = url
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
        if not updates:
            return self
        return self.model_copy(update=updates)

    @staticmethod
    def _ensure_supported(name: str, value: str, supported_values: set[str]) -> None:
        if value not in supported_values:
            supported = ", ".join(sorted(supported_values))
            raise ValueError(f"Unsupported {name} '{value}'. Supported values: {supported}")


@lru_cache
def get_settings() -> Settings:
    return Settings()
