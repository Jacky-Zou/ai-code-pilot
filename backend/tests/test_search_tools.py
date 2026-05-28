from pathlib import Path

from app.tools.search_tools import SearchTextTool


def test_search_text_returns_matches_with_line_numbers(tmp_path: Path) -> None:
    (tmp_path / "a.py").write_text("alpha\nFastAPI app\n", encoding="utf-8")
    (tmp_path / "b.py").write_text("FastAPI router\n", encoding="utf-8")

    result = SearchTextTool().run(project_path=str(tmp_path), keyword="FastAPI")

    assert result["count"] == 2
    assert result["matches"][0] == {"file_path": "a.py", "line_number": 2, "line": "FastAPI app"}


def test_search_text_ignores_common_directories(tmp_path: Path) -> None:
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "lib.js").write_text("FastAPI", encoding="utf-8")
    (tmp_path / "src.py").write_text("FastAPI", encoding="utf-8")

    result = SearchTextTool().run(project_path=str(tmp_path), keyword="FastAPI")

    assert result["count"] == 1
    assert result["matches"][0]["file_path"] == "src.py"


def test_search_text_respects_max_results(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("x\nx\nx\n", encoding="utf-8")

    result = SearchTextTool().run(project_path=str(tmp_path), keyword="x", max_results=2)

    assert result["count"] == 2


def test_search_text_skips_binary_files(tmp_path: Path) -> None:
    (tmp_path / "binary.bin").write_bytes(b"abc\x00FastAPI")

    result = SearchTextTool().run(project_path=str(tmp_path), keyword="FastAPI")

    assert result["count"] == 0
