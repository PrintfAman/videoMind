from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)


class SearchResult(BaseModel):
    score: float
    video: str
    event_id: str | None = None
    start: float | None = None
    end: float | None = None
    speech: str = ""
    vision: str = ""
