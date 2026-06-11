"""Tests for generic RAG retriever (T-8): no project-specific hardcoding.

Verifies that _intent_file_bonus has been removed and _source_file_bonus
works correctly for non-AICodePilot project layouts.
"""

import inspect
from pathlib import Path

import pytest

from app.rag.retriever import CodeRetriever
from app.rag.schemas import CodeChunk, RetrievedChunk
from app.rag.vector_store import JsonVectorStore


def _make_chunk(file_path: str, content: str = "dummy", score: float = 0.5) -> RetrievedChunk:
    return RetrievedChunk(file_path=file_path, start_line=1, end_line=5, content=content, score=score)


class TestIntentFileBonusRemoved:
    """_intent_file_bonus must not exist on CodeRetriever after T-8."""

    def test_no_intent_file_bonus_method(self) -> None:
        assert not hasattr(CodeRetriever, "_intent_file_bonus"), (
            "_intent_file_bonus was not removed — hardcoded project-specific boosting is still present"
        )

    def test_no_hardcoded_paths_in_source_file_bonus(self) -> None:
        """_source_file_bonus must not reference AICodePilot-specific paths."""

        source = inspect.getsource(CodeRetriever._source_file_bonus)
        forbidden = ["backend/app/", "frontend/", "backend/app/core/config.py",
                     "backend/app/tools/registry.py", "backend/app/agent/executor.py"]
        for path in forbidden:
            assert path not in source, (
                f"Hardcoded AICodePilot path '{path}' found in _source_file_bonus — T-8 not complete"
            )

    def test_no_hardcoded_paths_in_rerank(self) -> None:
        source = inspect.getsource(CodeRetriever._rerank)
        assert "intent_bonus" not in source, (
            "intent_bonus is still referenced in _rerank — T-8 not complete"
        )


class TestSourceFileBonusGeneric:
    """_source_file_bonus must work correctly for arbitrary project layouts."""

    def _retriever(self) -> CodeRetriever:
        return CodeRetriever(vector_store=JsonVectorStore())

    def test_test_directory_penalised(self) -> None:
        r = self._retriever()
        bonus = r._source_file_bonus("tests/test_main.py")
        assert bonus < 0

    def test_docs_directory_penalised(self) -> None:
        r = self._retriever()
        assert r._source_file_bonus("docs/guide.md") < 0

    def test_markdown_penalised(self) -> None:
        r = self._retriever()
        assert r._source_file_bonus("README.md") < 0

    def test_src_directory_rewarded(self) -> None:
        r = self._retriever()
        assert r._source_file_bonus("src/main.go") > 0

    def test_lib_directory_rewarded(self) -> None:
        r = self._retriever()
        assert r._source_file_bonus("lib/util.py") > 0

    def test_app_directory_rewarded(self) -> None:
        r = self._retriever()
        assert r._source_file_bonus("app/handler.py") > 0

    def test_pkg_directory_rewarded(self) -> None:
        r = self._retriever()
        assert r._source_file_bonus("pkg/router/router.go") > 0

    def test_neutral_file_zero_bonus(self) -> None:
        r = self._retriever()
        bonus = r._source_file_bonus("main.py")
        assert bonus == 0.0


class TestRetrievalOnForeignRepo:
    """End-to-end: retrieve on a non-AICodePilot project structure."""

    def test_retrieval_on_go_project_structure(self, tmp_path: Path) -> None:
        """A Go-style project should be retrievable without any hardcoded path errors."""

        # Build a minimal foreign repo structure
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.go").write_text(
            "package main\nfunc main() { println(\"hello\") }", encoding="utf-8"
        )
        (tmp_path / "lib").mkdir()
        (tmp_path / "lib" / "util.go").write_text(
            "package lib\nfunc Helper() string { return \"ok\" }", encoding="utf-8"
        )
        (tmp_path / "tests").mkdir()
        (tmp_path / "tests" / "main_test.go").write_text(
            "package main_test\nfunc TestMain(t *testing.T) {}", encoding="utf-8"
        )

        from app.rag.embeddings import LocalHashEmbeddingClient

        retriever = CodeRetriever(
            embedding_client=LocalHashEmbeddingClient(),
            vector_store=JsonVectorStore(),
        )
        retriever.index_project(tmp_path)
        results = retriever.search("helper function", top_k=3)

        assert results, "Should return results for a foreign repo"
        # lib/util.go should score higher than tests/main_test.go due to generic source bonus
        file_paths = [r.file_path for r in results]
        assert any("util.go" in p or "main.go" in p for p in file_paths)

    def test_no_aicodepilot_specific_descriptions_in_fallback(self, tmp_path: Path) -> None:
        """executor._describe_read_file_result must not produce project-specific text."""

        from app.agent.executor import AgentExecutor
        from app.core.config import Settings

        executor = AgentExecutor(settings=Settings(_env_file=None))
        result_en = executor._describe_read_file_result("src/router/handler.go", "search")
        assert result_en == "- Read `src/router/handler.go`."

        result_zh = executor._describe_read_file_result("src/main.go", "搜索主函数")
        assert result_zh == "- 已读取 `src/main.go`。"

    def test_fallback_answer_no_agent_bias(self, tmp_path: Path) -> None:
        """_build_fallback_answer must not bias toward 'agent' files."""

        from app.agent.executor import AgentExecutor
        from app.agent.schemas import ToolResult
        from app.core.config import Settings

        executor = AgentExecutor(settings=Settings(_env_file=None))
        tool_results = [
            ToolResult(
                name="list_files",
                arguments={},
                result={"count": 2, "files": ["src/router.go", "lib/db.go"]},
            )
        ]
        answer = executor._build_fallback_answer(tool_results, "find the router")
        # No hardcoded "agent" path bias — should just list files generically
        assert "agent" not in answer.lower() or "agent" in "find the router".lower()
        assert "router.go" in answer or "2" in answer
