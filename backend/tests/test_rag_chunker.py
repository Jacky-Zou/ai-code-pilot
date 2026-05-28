from pathlib import Path

import pytest

from app.rag.chunker import CodeChunker
from app.rag.indexer import ProjectFile


def test_chunker_splits_lines_with_metadata() -> None:
    lines = [f"line {index}" for index in range(1, 8)]

    chunks = CodeChunker(chunk_size_lines=3, overlap_lines=1).chunk_lines(lines, "app.py")

    assert [(chunk.start_line, chunk.end_line) for chunk in chunks] == [(1, 3), (3, 5), (5, 7)]
    assert chunks[0].file_path == "app.py"
    assert chunks[0].content == "line 1\nline 2\nline 3"


def test_chunker_returns_no_chunks_for_empty_file() -> None:
    chunks = CodeChunker().chunk_lines([], "empty.py")

    assert chunks == []


def test_chunker_reads_project_files(tmp_path: Path) -> None:
    file_path = tmp_path / "main.py"
    file_path.write_text("a\nb\nc", encoding="utf-8")
    project_file = ProjectFile(path=file_path, relative_path="main.py", size=file_path.stat().st_size)

    chunks = CodeChunker(chunk_size_lines=2, overlap_lines=0).chunk_project_files([project_file])

    assert [(chunk.file_path, chunk.start_line, chunk.end_line) for chunk in chunks] == [
        ("main.py", 1, 2),
        ("main.py", 3, 3),
    ]


def test_chunker_validates_overlap() -> None:
    with pytest.raises(ValueError, match="smaller"):
        CodeChunker(chunk_size_lines=10, overlap_lines=10)
