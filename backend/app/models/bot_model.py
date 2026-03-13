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

