from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(slots=True)
class ChatLogRecord:
    id: UUID
    bot_id: UUID
    user_id: UUID
    question: str
    response: str
    cached: bool
    timestamp: datetime

