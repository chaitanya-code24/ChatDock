from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    bot_id: UUID
    message: str = Field(min_length=2, max_length=4_000)


class SourceChunk(BaseModel):
    document_id: UUID
    document_name: str
    chunk_id: UUID
    score: float
    excerpt: str


class ChatResponse(BaseModel):
    bot_id: UUID
    answer: str
    cached: bool
    sources: list[SourceChunk]


class AnalyticsOverview(BaseModel):
    user_id: UUID
    total_bots: int
    total_documents: int
    total_chunks: int
    total_queries: int
    cached_queries: int


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    project_name: str
    max_context_chunks: int
    chunk_size_tokens: int

