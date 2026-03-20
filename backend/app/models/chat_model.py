from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(slots=True)
class ChatThreadRecord:
    id: UUID
    bot_id: UUID
    user_id: UUID
    title: str
    created_at: datetime
    updated_at: datetime


@dataclass(slots=True)
class ChatLogRecord:
    id: UUID
    conversation_id: UUID
    bot_id: UUID
    user_id: UUID
    question: str
    response: str
    cached: bool
    timestamp: datetime

