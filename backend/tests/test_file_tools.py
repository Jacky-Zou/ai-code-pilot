from pathlib import Path

import pytest

from app.core.exceptions import ToolError
from app.tools.file_tools import FindFilesTool, ListFilesTool, ProjectTreeTool, ReadFileTool


def test_list_files_returns_relative_paths(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text("print('hi')", encoding="utf-8")
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "ignored.js").write_text("ignored", encoding="utf-8")

    result = ListFilesTool().run(project_path=str(tmp_path))

    assert result["count"] == 1
    assert result["files"] == ["app.py"]


def test_list_files_requires_directory(tmp_path: Path) -> None:
    file_path = tmp_path / "file.txt"
    file_path.write_text("x", encoding="utf-8")

    with pytest.raises(ToolError, match="not a directory"):
        ListFilesTool().run(project_path=str(file_path))


def test_list_files_prunes_ignored_directories(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("print('hi')", encoding="utf-8")
    (tmp_path / ".next").mkdir()
    (tmp_path / ".next" / "bundle.js").write_text("ignored", encoding="utf-8")

    result = ListFilesTool().run(project_path=str(tmp_path))

    assert result["files"] == ["src/app.py"]
    assert result["truncated"] is False


def test_read_file_reads_text_inside_project(tmp_path: Path) -> None:
    file_path = tmp_path / "README.md"
    file_path.write_text("hello", encoding="utf-8")

    result = ReadFileTool().run(project_path=str(tmp_path), file_path="README.md")

    assert result["relative_path"] == "README.md"
    assert result["content"] == "hello"


def test_read_file_blocks_path_outside_project(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    outside = tmp_path / "secret.txt"
    outside.write_text("secret", encoding="utf-8")

    with pytest.raises(ToolError, match="outside"):
        ReadFileTool().run(project_path=str(project), file_path=str(outside))


def test_read_file_blocks_large_file(tmp_path: Path) -> None:
    file_path = tmp_path / "big.txt"
    file_path.write_text("abcd", encoding="utf-8")

    with pytest.raises(ToolError, match="too large"):
        ReadFileTool().run(project_path=str(tmp_path), file_path="big.txt", max_bytes=2)


def test_read_file_blocks_binary(tmp_path: Path) -> None:
    file_path = tmp_path / "image.bin"
    file_path.write_bytes(b"abc\x00def")

    with pytest.raises(ToolError, match="binary"):
        ReadFileTool().run(project_path=str(tmp_path), file_path="image.bin")


def test_project_tree_returns_compact_structure(tmp_path: Path) -> None:
    (tmp_path / "backend" / "app").mkdir(parents=True)
    (tmp_path / "backend" / "app" / "main.py").write_text("app", encoding="utf-8")

    result = ProjectTreeTool().run(project_path=str(tmp_path), max_depth=3)

    assert "backend/" in result["entries"]
    assert "  app/" in result["entries"]
    assert "    main.py" in result["entries"]


def test_find_files_matches_by_name(tmp_path: Path) -> None:
    (tmp_path / "agent").mkdir()
    (tmp_path / "agent" / "executor.py").write_text("class AgentExecutor: pass", encoding="utf-8")
    (tmp_path / "README.md").write_text("docs", encoding="utf-8")

    result = FindFilesTool().run(project_path=str(tmp_path), pattern="executor")

    assert result["matches"] == ["agent/executor.py"]
