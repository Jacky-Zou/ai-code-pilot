from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

SUPPORTED_LLM_PROVIDERS = {"openai", "deepseek"}
SUPPORTED_EMBEDDING_PROVIDERS = {"openai", "local"}
SUPPORTED_VECTOR_STORE_BACKENDS = {"chroma", "json", "memory"}
SUPPORTED_LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}


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

    embedding_provider: str = Field(default="openai", alias="EMBEDDING_PROVIDER")
    embedding_model: str = Field(default="text-embedding-3-small", alias="EMBEDDING_MODEL")

    vector_store_path: Path = Field(default=Path("./data/vector_store"), alias="VECTOR_STORE_PATH")
    vector_store_backend: str = Field(default="chroma", alias="VECTOR_STORE_BACKEND")

    model_config = SettingsConfigDict(
        env_file=".env",
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
        return self

    def default_model_for_provider(self, provider_name: str | None = None) -> str:
        provider = (provider_name or self.llm_provider).strip().lower()
        if provider == "openai":
            return self.openai_model
        if provider == "deepseek":
            return self.deepseek_model
        raise ValueError(f"Unsupported LLM provider: {provider}")

    @staticmethod
    def _ensure_supported(name: str, value: str, supported_values: set[str]) -> None:
        if value not in supported_values:
            supported = ", ".join(sorted(supported_values))
            raise ValueError(f"Unsupported {name} '{value}'. Supported values: {supported}")


@lru_cache
def get_settings() -> Settings:
    return Settings()


