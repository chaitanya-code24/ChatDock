from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

ToneValue = Literal["professional", "friendly", "technical"]
AnswerLengthValue = Literal["short", "balanced", "detailed"]
FallbackBehaviorValue = Literal["strict", "helpful"]


class BotCreate(BaseModel):
    bot_name: str = Field(min_length=2, max_length=80)
    description: str | None = Field(default=None, max_length=400)


class BotUpdate(BaseModel):
    bot_name: str | None = Field(default=None, min_length=2, max_length=80)
    description: str | None = Field(default=None, max_length=400)
    tone: ToneValue | None = None
    answer_length: AnswerLengthValue | None = None
    fallback_behavior: FallbackBehaviorValue | None = None
    system_prompt: str | None = Field(default=None, max_length=4000)
    greeting_message: str | None = Field(default=None, max_length=1000)


class BotArchiveRequest(BaseModel):
    archived: bool = True


class BotSummary(BaseModel):
    id: UUID
    user_id: UUID
    bot_name: str
    description: str | None = None
    created_at: datetime
    archived: bool = False
    tone: ToneValue = "professional"
    answer_length: AnswerLengthValue = "balanced"
    fallback_behavior: FallbackBehaviorValue = "strict"
    system_prompt: str | None = None
    greeting_message: str | None = None
    updated_at: datetime | None = None
    document_count: int
    chunk_count: int
