from pathlib import Path

from app.rag.indexer import ProjectFile
from app.rag.schemas import CodeChunk


class CodeChunker:
    """Split source files into line-based chunks for retrieval.

    Phase 2 deliberately uses predictable line windows instead of AST parsing.
    The retained line numbers make retrieved snippets easy to cite in answers,
    and the class can later be extended with function/class level chunking.
    """

    def __init__(self, chunk_size_lines: int = 80, overlap_lines: int = 10) -> None:
        if chunk_size_lines < 1:
            raise ValueError("chunk_size_lines must be greater than 0")
        if overlap_lines < 0:
            raise ValueError("overlap_lines must be greater than or equal to 0")
        if overlap_lines >= chunk_size_lines:
            raise ValueError("overlap_lines must be smaller than chunk_size_lines")
        self.chunk_size_lines = chunk_size_lines
        self.overlap_lines = overlap_lines

    def chunk_file(self, file_path: str | Path, relative_path: str | None = None) -> list[CodeChunk]:
        path = Path(file_path)
        lines = path.read_text(encoding="utf-8").splitlines()
        return self.chunk_lines(lines, relative_path or path.as_posix())

    def chunk_project_files(self, files: list[ProjectFile]) -> list[CodeChunk]:
        chunks: list[CodeChunk] = []
        for project_file in files:
            chunks.extend(self.chunk_file(project_file.path, project_file.relative_path))
        return chunks

    def chunk_lines(self, lines: list[str], file_path: str) -> list[CodeChunk]:
        if not lines:
            return []

        chunks: list[CodeChunk] = []
        step = self.chunk_size_lines - self.overlap_lines
        start_index = 0

        while start_index < len(lines):
            end_index = min(start_index + self.chunk_size_lines, len(lines))
            chunk_lines = lines[start_index:end_index]
            chunks.append(
                CodeChunk(
                    file_path=file_path,
                    start_line=start_index + 1,
                    end_line=end_index,
                    content="\n".join(chunk_lines),
                )
            )
            if end_index == len(lines):
                break
            start_index += step

        return chunks
