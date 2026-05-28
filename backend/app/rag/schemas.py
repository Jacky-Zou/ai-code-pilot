from pydantic import BaseModel, Field


class CodeChunk(BaseModel):
    """A retrievable slice of source text with stable file and line metadata."""

    file_path: str
    start_line: int = Field(ge=1)
    end_line: int = Field(ge=1)
    content: str


class RetrievedChunk(CodeChunk):
    """A chunk returned by vector search, enriched with similarity score."""

    score: float
