from fastapi import APIRouter, Depends

from app.agent.agent import AICodePilotAgent
from app.api.schemas import ChatRequest, ChatResponse
from app.core.logger import get_logger
from app.core.project_paths import normalize_project_path

router = APIRouter(prefix="/api", tags=["chat"])
logger = get_logger(__name__)


def get_agent() -> AICodePilotAgent:
    """Provide the Agent dependency used by the chat endpoint."""

    return AICodePilotAgent()


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, agent: AICodePilotAgent = Depends(get_agent)) -> ChatResponse:
    """Run the coding Agent for one user message and return its API shape."""

    logger.info(
        "Chat request received provider=%s model=%s project_path_present=%s",
        request.provider or "default",
        request.model or "default",
        request.project_path is not None,
    )
    project_path = normalize_project_path(request.project_path) if request.project_path else None
    response = agent.run(
        message=request.message,
        project_path=project_path,
        provider=request.provider,
        model=request.model,
    )
    logger.info(
        "Chat request completed provider=%s model=%s tool_calls=%s references=%s",
        response.provider,
        response.model,
        len(response.tool_calls),
        len(response.references),
    )
    return ChatResponse(
        answer=response.answer,
        provider=response.provider,
        model=response.model,
        tool_calls=response.tool_calls,
        references=response.references,
    )
