from app.agent.agent import AICodePilotAgent
from app.agent.schemas import AgentRequest, AgentResponse


class FakeExecutor:
    def __init__(self) -> None:
        self.requests: list[AgentRequest] = []

    def run(self, request: AgentRequest) -> AgentResponse:
        self.requests.append(request)
        return AgentResponse(answer="ok", provider=request.provider or "openai", model=request.model or "gpt-5.2")


def test_agent_facade_builds_request_for_executor() -> None:
    executor = FakeExecutor()
    agent = AICodePilotAgent(executor=executor)  # type: ignore[arg-type]

    response = agent.run(
        message="Where is config loaded?",
        project_path="/tmp/project",
        provider="deepseek",
        model="deepseek-v4-pro",
    )

    assert response.answer == "ok"
    assert executor.requests == [
        AgentRequest(
            message="Where is config loaded?",
            project_path="/tmp/project",
            provider="deepseek",
            model="deepseek-v4-pro",
        )
    ]
