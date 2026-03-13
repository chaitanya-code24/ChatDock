from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from app.core.config import settings

try:
    import redis  # type: ignore
except ImportError:  # pragma: no cover
    redis = None


@dataclass(slots=True)
class CacheEntry:
    response: str
    expires_at: datetime


class CacheService:
    def __init__(self) -> None:
        self._items: dict[str, CacheEntry] = {}
        self._redis = None
        if redis is not None:
            try:
                client = redis.Redis.from_url(settings.redis_url, decode_responses=True)
                client.ping()
                self._redis = client
            except Exception:
                self._redis = None

    def get(self, key: str) -> str | None:
        if self._redis is not None:
            value = self._redis.get(self._namespaced(key))
            return value if value else None

        entry = self._items.get(key)
        if entry is None:
            return None
        if entry.expires_at < datetime.now(timezone.utc):
            self._items.pop(key, None)
            return None
        return entry.response

    def set(self, key: str, response: str) -> None:
        if self._redis is not None:
            self._redis.setex(self._namespaced(key), settings.response_cache_ttl_seconds, response)
            return

        self._items[key] = CacheEntry(
            response=response,
            expires_at=datetime.now(timezone.utc) + timedelta(seconds=settings.response_cache_ttl_seconds),
        )

    def clear(self) -> None:
        if self._redis is not None:
            keys = self._redis.keys("chatdock:cache:*")
            if keys:
                self._redis.delete(*keys)
            return
        self._items.clear()

    @staticmethod
    def _namespaced(key: str) -> str:
        return f"chatdock:cache:{key}"


cache_service = CacheService()

