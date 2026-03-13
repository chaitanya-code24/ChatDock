from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class BotCreate(BaseModel):
    bot_name: str = Field(min_length=2, max_length=80)
    description: str | None = Field(default=None, max_length=400)


class BotSummary(BaseModel):
    id: UUID
    user_id: UUID
    bot_name: str
    description: str | None = None
    created_at: datetime
    document_count: int
    chunk_count: int

