from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(slots=True)
class DocumentRecord:
    id: UUID
    bot_id: UUID
    file_name: str
    mime_type: str
    raw_text: str
    uploaded_at: datetime


@dataclass(slots=True)
class ChunkRecord:
    id: UUID
    document_id: UUID
    bot_id: UUID
    text: str
    token_count: int

