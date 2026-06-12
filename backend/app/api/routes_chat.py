import uuid
from collections.abc import Iterator

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlmodel import Session

from app.agent.agent import AICodePilotAgent
from app.agent.executor import AgentExecutor
from app.api.schemas import ChatRequest, ChatResponse
from app.core.logger import get_logger
from app.core.project_paths import normalize_project_path
from app.db.engine import get_session
from app.db.repository import ConversationRepository
from app.memory.session_store import get_session_store

router = APIRouter(prefix="/api", tags=["chat"])
logger = get_logger(__name__)


def get_agent() -> AICodePilotAgent:
    """Provide a stateless Agent dependency for FastAPI dependency_overrides.

    The real /api/chat handler uses a session-aware executor built from the
    SessionStore and does NOT call get_agent() directly. This function exists
    solely so test suites can inject fake agents via
    `app.dependency_overrides[get_agent] = lambda: FakeAgent()`.
    """

    return AICodePilotAgent()


def _build_session_agent(conversation_id: str) -> AICodePilotAgent:
    """Build a memory-aware Agent bound to the given conversation session."""

    memory = get_session_store().get_or_create(conversation_id)
    executor = AgentExecutor(memory=memory)
    return AICodePilotAgent(executor=executor)


@router.post("/chat", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    injected_agent: AICodePilotAgent = Depends(get_agent),
    db: Session = Depends(get_session),
) -> ChatResponse:
    """Run the coding Agent for one user message with multi-turn memory.

    When `get_agent` is overridden by a test dependency, the injected fake is
    used directly (without session memory) so existing test contracts remain
    intact. In normal production execution, a fresh session-aware executor is
    constructed from the SessionStore regardless of the injected dependency,
    because `get_agent` returns a plain AICodePilotAgent with no memory wired.

    The session-aware path is identified by checking whether the injected agent
    is the bare default instance from `get_agent()` (no override). Tests that
    override `get_agent` always supply a class that is NOT `AICodePilotAgent`,
    so we can distinguish the two paths cleanly.
    """

    conversation_id = (request.conversation_id or "").strip() or str(uuid.uuid4())

    # Use the injected fake when the dependency was overridden by a test.
    if not isinstance(injected_agent, AICodePilotAgent):
        agent = injected_agent
    else:
        # Normal path: wire session memory so multi-turn context is preserved.
        agent = _build_session_agent(conversation_id)

    logger.info(
        "Chat request received provider=%s model=%s project_path_present=%s conversation_id=%s",
        request.provider or "default",
        request.model or "default",
        request.project_path is not None,
        conversation_id,
    )

    project_path = normalize_project_path(request.project_path) if request.project_path else None
    response = agent.run(
        message=request.message,
        project_path=project_path,
        provider=request.provider,
        model=request.model,
        api_key=request.api_key,
        base_url=request.base_url,
    )

    logger.info(
        "Chat request completed provider=%s model=%s tool_calls=%s references=%s conversation_id=%s",
        response.provider,
        response.model,
        len(response.tool_calls),
        len(response.references),
        conversation_id,
    )

    # Persist user message and assistant answer to the database
    repo = ConversationRepository(db)
    repo.ensure_conversation(conversation_id, title=request.message[:80])
    repo.append_message(conversation_id, "user", request.message)
    repo.append_message(conversation_id, "assistant", response.answer)

    return ChatResponse(
        answer=response.answer,
        provider=response.provider,
        model=response.model,
        tool_calls=response.tool_calls,
        references=response.references,
        conversation_id=conversation_id,
        patch_suggestions=[s.model_dump() for s in response.patch_suggestions],
    )


@router.post("/chat/stream")
def chat_stream(request: ChatRequest) -> StreamingResponse:
    """Stream agent execution as Server-Sent Events.

    Each agent step is flushed to the client immediately so the UI can render
    progress. The final `done` event carries the complete result and the
    conversation_id for client reuse.

    SSE event protocol:
      event: thinking      data: {"step": <int>}
      event: tool_start    data: {"tool": <str>, "arguments": {...}}
      event: tool_end      data: {"tool": <str>, "error": <str|null>}
      event: answer_delta  data: {"text": <str>}
      event: done          data: {"answer": ..., "references": [...], "tool_calls": [...], "conversation_id": ...}
      event: error         data: {"detail": <str>}
    """

    conversation_id = (request.conversation_id or "").strip() or str(uuid.uuid4())
    agent = _build_session_agent(conversation_id)
    project_path = normalize_project_path(request.project_path) if request.project_path else None

    def event_generator() -> Iterator[str]:
        try:
            for event in agent.run_stream(
                message=request.message,
                project_path=project_path,
                provider=request.provider,
                model=request.model,
                api_key=request.api_key,
                base_url=request.base_url,
            ):
                if event.type == "done":
                    event.data["conversation_id"] = conversation_id
                yield event.to_sse()
        except Exception as exc:  # noqa: BLE001 — HTTP headers already sent, must surface as SSE error frame
            logger.exception("Streaming chat failed conversation_id=%s", conversation_id)
            from app.agent.events import AgentEvent

            yield AgentEvent(type="error", data={"detail": str(exc)}).to_sse()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
