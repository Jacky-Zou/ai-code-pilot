"""Tests for IndexCache and RAG tool caching behavior.

Covers T-5 requirements:
- is_fresh / mark_indexed / invalidate
- project_key derivation is stable and filesystem-safe
- Concurrent access safety
- RetrieveCodeTool: first call triggers index_project, cache-hit skips it
- per-project isolation: different paths produce different keys
"""

import threading
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.rag.index_cache import IndexCache, get_index_cache, project_key

# ---------------------------------------------------------------------------
# IndexCache unit tests
# ---------------------------------------------------------------------------


class TestIndexCache:
    def test_fresh_after_mark_indexed(self) -> None:
        cache = IndexCache(ttl_seconds=60)
        cache.mark_indexed("proj-a")
        assert cache.is_fresh("proj-a")

    def test_not_fresh_before_mark(self) -> None:
        cache = IndexCache(ttl_seconds=60)
        assert not cache.is_fresh("proj-unknown")

    def test_expired_after_ttl(self) -> None:
        cache = IndexCache(ttl_seconds=0.02)
        cache.mark_indexed("proj-b")
        assert cache.is_fresh("proj-b")
        time.sleep(0.05)
        assert not cache.is_fresh("proj-b")

    def test_invalidate_clears_entry(self) -> None:
        cache = IndexCache(ttl_seconds=60)
        cache.mark_indexed("proj-c")
        assert cache.is_fresh("proj-c")
        cache.invalidate("proj-c")
        assert not cache.is_fresh("proj-c")

    def test_invalidate_nonexistent_is_noop(self) -> None:
        cache = IndexCache(ttl_seconds=60)
        cache.invalidate("no-such-key")  # must not raise

    def test_raises_on_nonpositive_ttl(self) -> None:
        with pytest.raises(ValueError, match="must be positive"):
            IndexCache(ttl_seconds=0)

    def test_concurrent_mark_and_is_fresh(self) -> None:
        """Multiple threads marking and checking different keys must not corrupt state."""

        cache = IndexCache(ttl_seconds=60)
        errors: list[Exception] = []

        def worker(key: str) -> None:
            try:
                cache.mark_indexed(key)
                assert cache.is_fresh(key)
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=worker, args=(f"proj-{i}",)) for i in range(50)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"Concurrent access raised: {errors}"


class TestProjectKey:
    def test_same_path_same_key(self, tmp_path: Path) -> None:
        k1 = project_key(str(tmp_path))
        k2 = project_key(str(tmp_path))
        assert k1 == k2

    def test_different_paths_different_keys(self, tmp_path: Path) -> None:
        dir_a = tmp_path / "project_a"
        dir_b = tmp_path / "project_b"
        dir_a.mkdir()
        dir_b.mkdir()
        assert project_key(str(dir_a)) != project_key(str(dir_b))

    def test_key_starts_with_acp_prefix(self, tmp_path: Path) -> None:
        key = project_key(str(tmp_path))
        assert key.startswith("acp_")

    def test_key_has_no_spaces(self, tmp_path: Path) -> None:
        spaced = tmp_path / "my project"
        spaced.mkdir()
        key = project_key(str(spaced))
        assert " " not in key

    def test_key_length_is_reasonable(self, tmp_path: Path) -> None:
        key = project_key(str(tmp_path))
        # Chroma collection names have a 64-char limit recommendation
        assert len(key) <= 64


class TestGetIndexCacheSingleton:
    def test_returns_same_instance(self) -> None:
        c1 = get_index_cache()
        c2 = get_index_cache()
        assert c1 is c2


# ---------------------------------------------------------------------------
# RetrieveCodeTool cache integration tests
# ---------------------------------------------------------------------------


class TestRetrieveCodeToolCache:
    """Verify that RetrieveCodeTool only calls index_project when the cache is stale."""

    def _make_mock_retriever(self) -> MagicMock:
        retriever = MagicMock()
        retriever.index_project.return_value = {"indexed_files": 3, "chunks": 10}
        retriever.search.return_value = []
        return retriever

    def test_first_call_triggers_index_project(self, tmp_path: Path) -> None:
        (tmp_path / "f.py").write_text("# code\n", encoding="utf-8")
        mock_retriever = self._make_mock_retriever()

        # Use a fresh cache with very long TTL so only the first call indexes
        fresh_cache = IndexCache(ttl_seconds=3600)

        with (
            patch("app.tools.rag_tools.CodeRetriever", return_value=mock_retriever),
            patch("app.tools.rag_tools.get_index_cache", return_value=fresh_cache),
        ):
            from app.tools.rag_tools import RetrieveCodeTool

            tool = RetrieveCodeTool()
            result = tool.run(project_path=str(tmp_path), query="test")

        mock_retriever.index_project.assert_called_once()
        assert result["cache_hit"] is False
        assert result["indexed_files"] == 3

    def test_second_call_within_ttl_skips_index_project(self, tmp_path: Path) -> None:
        (tmp_path / "f.py").write_text("# code\n", encoding="utf-8")
        mock_retriever = self._make_mock_retriever()
        shared_cache = IndexCache(ttl_seconds=3600)

        with (
            patch("app.tools.rag_tools.CodeRetriever", return_value=mock_retriever),
            patch("app.tools.rag_tools.get_index_cache", return_value=shared_cache),
        ):
            from app.tools.rag_tools import RetrieveCodeTool

            tool = RetrieveCodeTool()
            tool.run(project_path=str(tmp_path), query="first")
            result2 = tool.run(project_path=str(tmp_path), query="second")

        # index_project called exactly once (the second call hit cache)
        assert mock_retriever.index_project.call_count == 1
        assert result2["cache_hit"] is True

    def test_expired_ttl_triggers_reindex(self, tmp_path: Path) -> None:
        (tmp_path / "f.py").write_text("# code\n", encoding="utf-8")
        mock_retriever = self._make_mock_retriever()
        expiring_cache = IndexCache(ttl_seconds=0.02)  # 20 ms TTL

        with (
            patch("app.tools.rag_tools.CodeRetriever", return_value=mock_retriever),
            patch("app.tools.rag_tools.get_index_cache", return_value=expiring_cache),
        ):
            from app.tools.rag_tools import RetrieveCodeTool

            tool = RetrieveCodeTool()
            tool.run(project_path=str(tmp_path), query="first")
            time.sleep(0.05)  # let TTL expire
            result2 = tool.run(project_path=str(tmp_path), query="second")

        assert mock_retriever.index_project.call_count == 2
        assert result2["cache_hit"] is False

    def test_different_projects_have_separate_caches(self, tmp_path: Path) -> None:
        dir_a = tmp_path / "proj_a"
        dir_b = tmp_path / "proj_b"
        dir_a.mkdir()
        dir_b.mkdir()
        (dir_a / "a.py").write_text("# a\n", encoding="utf-8")
        (dir_b / "b.py").write_text("# b\n", encoding="utf-8")

        mock_retriever = self._make_mock_retriever()
        shared_cache = IndexCache(ttl_seconds=3600)

        with (
            patch("app.tools.rag_tools.CodeRetriever", return_value=mock_retriever),
            patch("app.tools.rag_tools.get_index_cache", return_value=shared_cache),
        ):
            from app.tools.rag_tools import RetrieveCodeTool

            tool = RetrieveCodeTool()
            tool.run(project_path=str(dir_a), query="query")
            tool.run(project_path=str(dir_b), query="query")

        # Both projects are new → both should be indexed
        assert mock_retriever.index_project.call_count == 2
