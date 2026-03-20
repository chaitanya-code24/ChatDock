from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Literal

from app.core.config import settings

try:
    import redis  # type: ignore
except ImportError:  # pragma: no cover
    redis = None


Role = Literal["user", "assistant"]


@dataclass(slots=True)
class ConversationEntry:
    role: Role
    content: str
    created_at: str


class ConversationService:
    """
    Conversation memory for multi-turn chat.

    - Prefers Redis (shared across processes/containers)
    - Falls back to an in-memory store for local/dev/unit tests
    """

    def __init__(self) -> None:
        self._items: dict[str, tuple[datetime, list[ConversationEntry]]] = {}
        self._redis = None
        if redis is not None:
            try:
                client = redis.Redis.from_url(settings.redis_url, decode_responses=True)
                client.ping()
                self._redis = client
            except Exception:
                self._redis = None

    def get(self, key: str) -> list[ConversationEntry]:
        if self._redis is not None:
            values = self._redis.lrange(self._namespaced(key), 0, -1)
            out: list[ConversationEntry] = []
            for raw in values:
                try:
                    obj = json.loads(raw)
                    out.append(
                        ConversationEntry(
                            role=obj.get("role", "user"),
                            content=obj.get("content", ""),
                            created_at=obj.get("created_at", ""),
                        )
                    )
                except Exception:
                    continue
            return out

        record = self._items.get(key)
        if record is None:
            return []
        expires_at, entries = record
        if expires_at < datetime.now(timezone.utc):
            self._items.pop(key, None)
            return []
        return list(entries)

    def append(self, key: str, role: Role, content: str) -> None:
        content = (content or "").strip()
        if not content:
            return

        entry = ConversationEntry(
            role=role,
            content=content,
            created_at=datetime.now(timezone.utc).isoformat(),
        )

        if self._redis is not None:
            rkey = self._namespaced(key)
            payload = {"role": entry.role, "content": entry.content, "created_at": entry.created_at}
            self._redis.rpush(rkey, json.dumps(payload, ensure_ascii=True))
            # Keep only the most recent N messages.
            self._redis.ltrim(rkey, -settings.conversation_max_messages, -1)
            self._redis.expire(rkey, settings.conversation_ttl_seconds)
            return

        expires_at = datetime.now(timezone.utc) + timedelta(seconds=settings.conversation_ttl_seconds)
        _expires_at, entries = self._items.get(key, (expires_at, []))
        entries = list(entries)
        entries.append(entry)
        if len(entries) > settings.conversation_max_messages:
            entries = entries[-settings.conversation_max_messages :]
        self._items[key] = (expires_at, entries)

    def clear(self, key: str) -> None:
        if self._redis is not None:
            self._redis.delete(self._namespaced(key))
            return
        self._items.pop(key, None)

    @staticmethod
    def _namespaced(key: str) -> str:
        return f"chatdock:conv:{key}"


conversation_service = ConversationService()
