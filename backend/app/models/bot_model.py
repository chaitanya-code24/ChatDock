from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(slots=True)
class BotRecord:
    id: UUID
    user_id: UUID
    bot_name: str
    description: str | None
    created_at: datetime
    archived: bool = False
    tone: str = "professional"
    answer_length: str = "balanced"
    fallback_behavior: str = "strict"
    system_prompt: str | None = None
    greeting_message: str | None = None
    updated_at: datetime | None = None

