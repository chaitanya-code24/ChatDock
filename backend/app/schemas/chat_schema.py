from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    bot_id: UUID
    message: str = Field(min_length=2, max_length=4_000)
    nocache: bool = Field(default=False)
    # If omitted, the backend will create a new conversation id and return it.
    conversation_id: UUID | None = None


class SourceChunk(BaseModel):
    document_id: UUID
    document_name: str
    chunk_id: UUID
    score: float
    excerpt: str


class ChatResponse(BaseModel):
    bot_id: UUID
    conversation_id: UUID
    answer: str
    cached: bool
    sources: list[SourceChunk]
    logs: list[str] = []


class ChatThreadMessage(BaseModel):
    role: Literal["assistant", "user"]
    text: str
    created_at: str


class ChatThreadSummary(BaseModel):
    id: UUID
    bot_id: UUID
    title: str
    created_at: str
    updated_at: str
    messages: list[ChatThreadMessage] = []
    logs: list[str] = []


class ChatThreadCreate(BaseModel):
    bot_id: UUID
    title: str | None = None


class ChatThreadUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=160)


class TopQuery(BaseModel):
    question: str
    count: int


class BotQueryStat(BaseModel):
    bot_id: UUID
    bot_name: str
    queries: int


class AnalyticsOverview(BaseModel):
    user_id: UUID
    selected_bot_id: UUID | None = None
    selected_bot_name: str | None = None
    total_bots: int
    total_documents: int
    total_chunks: int
    total_queries: int
    cached_queries: int
    top_queries: list[TopQuery] = []
    query_trend_last_7_days: list[int] = []
    bot_queries: list[BotQueryStat] = []


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    project_name: str
    max_context_chunks: int
    chunk_size_tokens: int

