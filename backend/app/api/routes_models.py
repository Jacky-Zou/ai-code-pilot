from fastapi import APIRouter

from app.api.schemas import ListModelsRequest, ListModelsResponse
from app.core.config import SUPPORTED_LLM_PROVIDERS, get_settings
from app.core.exceptions import UnsupportedProviderError
from app.core.logger import get_logger
from app.llm.client import list_available_models

router = APIRouter(prefix="/api/providers", tags=["providers"])
logger = get_logger(__name__)


@router.post("/models", response_model=ListModelsResponse)
def list_models(request: ListModelsRequest) -> ListModelsResponse:
    """Return the models a provider API key can actually use.

    Acts as a thin server-side proxy to the provider's OpenAI-compatible
    ``GET /models`` endpoint. The browser holds the key (bring-your-own-key)
    and sends it here so the UI can present a real, key-specific model list
    instead of a hardcoded guess. The key authenticates the upstream call only
    and is never logged or persisted.
    """

    provider = request.provider.strip().lower()
    if provider not in SUPPORTED_LLM_PROVIDERS:
        supported = ", ".join(sorted(SUPPORTED_LLM_PROVIDERS))
        raise UnsupportedProviderError(f"Unsupported LLM provider '{provider}'. Supported: {supported}")

    settings = get_settings()
    base_url = (request.base_url or "").strip().rstrip("/") or settings.base_url_for_provider(provider)
    # Deliberately log only the provider, never the key or full URL credentials.
    logger.info("Listing models provider=%s", provider)
    models = list_available_models(base_url=base_url, api_key=request.api_key)
    return ListModelsResponse(provider=provider, models=models)
