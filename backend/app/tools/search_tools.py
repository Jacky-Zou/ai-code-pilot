from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from app.core.exceptions import ToolError
from app.tools.base import BaseTool
from app.tools.file_tools import _looks_binary, _resolve_existing_dir, iter_project_paths


class SearchTextArgs(BaseModel):
    project_path: str
    keyword: str = Field(min_length=1)
    max_results: int = Field(default=50, ge=1, le=500)


class SearchTextTool(BaseTool):
    name = "search_text"
    description = "Search text files recursively under a project path and return matching file paths, line numbers, and lines."
    args_schema = SearchTextArgs

    def run(self, **kwargs: Any) -> dict[str, Any]:
        args = self.validate_args(kwargs)
        assert isinstance(args, SearchTextArgs)
        root = _resolve_existing_dir(args.project_path)
        matches: list[dict[str, Any]] = []

        for path in iter_project_paths(root):
            if len(matches) >= args.max_results:
                break
            if not path.is_file():
                continue
            if _looks_binary(path):
                continue
            self._search_file(path, root, args.keyword, args.max_results, matches)

        return {
            "project_path": str(root),
            "keyword": args.keyword,
            "count": len(matches),
            "matches": matches,
        }

    def _search_file(
        self,
        path: Path,
        root: Path,
        keyword: str,
        max_results: int,
        matches: list[dict[str, Any]],
    ) -> None:
        try:
            with path.open("r", encoding="utf-8") as file_obj:
                for line_number, line in enumerate(file_obj, start=1):
                    if keyword in line:
                        matches.append(
                            {
                                "file_path": path.relative_to(root).as_posix(),
                                "line_number": line_number,
                                "line": line.rstrip("\n"),
                            }
                        )
                        if len(matches) >= max_results:
                            return
        except UnicodeDecodeError as exc:
            raise ToolError(f"Failed to decode text file: {path}") from exc
