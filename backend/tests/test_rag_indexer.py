from pathlib import Path

import pytest

from app.core.exceptions import ToolError
from app.rag.indexer import ProjectIndexer


def test_project_indexer_scans_text_code_files(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text("print('hi')", encoding="utf-8")
    (tmp_path / "README.md").write_text("docs", encoding="utf-8")
    (tmp_path / "image.png").write_bytes(b"\x89PNG\x00")

    files = ProjectIndexer().scan_files(tmp_path)

    assert sorted(file.relative_path for file in files) == ["README.md", "app.py"]


def test_project_indexer_ignores_dependency_directories(tmp_path: Path) -> None:
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "lib.js").write_text("ignored", encoding="utf-8")
    (tmp_path / "src.ts").write_text("const value = 1", encoding="utf-8")

    files = ProjectIndexer().scan_files(tmp_path)

    assert [file.relative_path for file in files] == ["src.ts"]


def test_project_indexer_skips_large_files(tmp_path: Path) -> None:
    (tmp_path / "big.py").write_text("x" * 20, encoding="utf-8")

    files = ProjectIndexer(max_file_bytes=10).scan_files(tmp_path)

    assert files == []


def test_project_indexer_rejects_missing_project(tmp_path: Path) -> None:
    with pytest.raises(ToolError, match="does not exist"):
        ProjectIndexer().scan_files(tmp_path / "missing")
