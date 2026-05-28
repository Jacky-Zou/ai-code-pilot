from fastapi import APIRouter, Depends

from app.agent.agent import AICodePilotAgent
from app.api.schemas import ChatRequest, ChatResponse

router = APIRouter(prefix="/api", tags=["chat"])


def get_agent() -> AICodePilotAgent:
    """Provide the Agent dependency used by the chat endpoint."""

    return AICodePilotAgent()


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, agent: AICodePilotAgent = Depends(get_agent)) -> ChatResponse:
    """Run the coding Agent for one user message and return its API shape."""

    response = agent.run(
        message=request.message,
        project_path=request.project_path,
        provider=request.provider,
        model=request.model,
    )
    return ChatResponse(
        answer=response.answer,
        provider=response.provider,
        model=response.model,
        tool_calls=response.tool_calls,
        references=response.references,
    )
