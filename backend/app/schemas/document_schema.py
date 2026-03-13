from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class DocumentSummary(BaseModel):
    id: UUID
    bot_id: UUID
    file_name: str
    uploaded_at: datetime
    chunk_count: int
    mime_type: str

