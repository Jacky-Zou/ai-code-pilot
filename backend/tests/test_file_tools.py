from pathlib import Path

import pytest

from app.core.exceptions import ToolError
from app.tools.file_tools import ListFilesTool, ReadFileTool


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
