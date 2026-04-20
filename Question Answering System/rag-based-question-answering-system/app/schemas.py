from pydantic import BaseModel, Field
from typing import List, Optional


class UploadResponse(BaseModel):
    document_id: str
    filename: str
    status: str
    message: str


class DocumentStatusResponse(BaseModel):
    document_id: str
    filename: str
    status: str
    chunks_indexed: int = 0
    error: Optional[str] = None


class AskRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=1000)
    document_ids: Optional[List[str]] = None
    top_k: int = Field(default=4, ge=1, le=10)


class SourceChunk(BaseModel):
    document_id: str
    chunk_id: str
    filename: str
    score: float
    text: str


class AskResponse(BaseModel):
    answer: str
    sources: List[SourceChunk]
    latency_ms: float
    top_score: Optional[float] = None