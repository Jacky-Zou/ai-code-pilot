from pathlib import Path

from app.tools.rag_tools import RetrieveCodeTool


def test_retrieve_code_tool_returns_code_references(tmp_path: Path) -> None:
    (tmp_path / "agent.py").write_text("class AgentExecutor:\n    def run(self):\n        pass\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("Docker deployment", encoding="utf-8")

    result = RetrieveCodeTool().run(project_path=str(tmp_path), query="AgentExecutor run", top_k=1)

    assert result["indexed_files"] == 2
    assert result["matches"][0]["file_path"] == "agent.py"
    assert result["matches"][0]["start_line"] == 1
    assert "AgentExecutor" in result["matches"][0]["content"]
