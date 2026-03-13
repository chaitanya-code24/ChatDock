from __future__ import annotations

from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status

from app.core.config import settings

try:
    import redis  # type: ignore
except ImportError:  # pragma: no cover
    redis = None


class RateLimiter:
    def __init__(self) -> None:
        self._buckets: dict[str, deque[datetime]] = defaultdict(deque)
        self._redis = None
        if redis is not None:
            try:
                client = redis.Redis.from_url(settings.redis_url, decode_responses=True)
                client.ping()
                self._redis = client
            except Exception:
                self._redis = None

    def check(self, subject: str) -> None:
        if self._redis is not None:
            self._check_redis(subject)
            return

        now = datetime.now(timezone.utc)
        bucket = self._buckets[subject]
        cutoff = now - timedelta(seconds=settings.rate_limit_window_seconds)
        while bucket and bucket[0] < cutoff:
            bucket.popleft()
        if len(bucket) >= settings.rate_limit_requests:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded")
        bucket.append(now)

    def reset(self) -> None:
        if self._redis is not None:
            keys = self._redis.keys("chatdock:ratelimit:*")
            if keys:
                self._redis.delete(*keys)
            return
        self._buckets.clear()

    def _check_redis(self, subject: str) -> None:
        key = f"chatdock:ratelimit:{subject}"
        count = self._redis.incr(key)  # type: ignore[union-attr]
        if count == 1:
            self._redis.expire(key, settings.rate_limit_window_seconds)  # type: ignore[union-attr]
        if count > settings.rate_limit_requests:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded")


rate_limiter = RateLimiter()
