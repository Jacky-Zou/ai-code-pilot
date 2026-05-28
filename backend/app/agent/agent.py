from app.agent.executor import AgentExecutor
from app.agent.schemas import AgentRequest, AgentResponse


class AICodePilotAgent:
    def __init__(self, executor: AgentExecutor | None = None) -> None:
        self.executor = executor or AgentExecutor()

    def run(
        self,
        message: str,
        project_path: str | None = None,
        provider: str | None = None,
        model: str | None = None,
    ) -> AgentResponse:
        request = AgentRequest(
            message=message,
            project_path=project_path,
            provider=provider,
            model=model,
        )
        return self.executor.run(request)
