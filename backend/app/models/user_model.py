from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(slots=True)
class UserRecord:
    id: UUID
    email: str
    password_hash: str
    created_at: datetime

