"""
Two-tier caching: Redis (if available) → in-memory fallback.
All cached values are JSON-serialized with TTL support.
"""

import json
import time
import hashlib
from typing import Any, Optional

from utils.logger import setup_logger

log = setup_logger("cache")


class InMemoryCache:
    """Thread-safe in-memory cache with TTL expiry."""

    def __init__(self):
        self._store: dict[str, tuple[Any, float]] = {}

    async def get(self, key: str) -> Optional[Any]:
        if key in self._store:
            value, expires_at = self._store[key]
            if time.time() < expires_at:
                log.info(f"Cache HIT (memory): {key[:60]}")
                return value
            else:
                del self._store[key]
                log.info(f"Cache EXPIRED (memory): {key[:60]}")
        return None

    async def set(self, key: str, value: Any, ttl: int = 3600):
        self._store[key] = (value, time.time() + ttl)
        log.info(f"Cache SET (memory): {key[:60]} | TTL={ttl}s")

    async def delete(self, key: str):
        self._store.pop(key, None)

    async def clear(self):
        self._store.clear()


class RedisCache:
    """Async Redis cache wrapper."""

    def __init__(self, redis_client):
        self._redis = redis_client

    async def get(self, key: str) -> Optional[Any]:
        raw = await self._redis.get(key)
        if raw:
            log.info(f"Cache HIT (redis): {key[:60]}")
            return json.loads(raw)
        return None

    async def set(self, key: str, value: Any, ttl: int = 3600):
        await self._redis.setex(key, ttl, json.dumps(value, default=str))
        log.info(f"Cache SET (redis): {key[:60]} | TTL={ttl}s")

    async def delete(self, key: str):
        await self._redis.delete(key)

    async def clear(self):
        await self._redis.flushdb()


# ── Factory ──

_cache_instance = None


async def get_cache():
    """Returns Redis cache if available, else in-memory fallback."""
    global _cache_instance
    if _cache_instance:
        return _cache_instance

    try:
        import redis.asyncio as aioredis
        from config import get_settings
        settings = get_settings()

        if settings.redis_url:
            client = aioredis.from_url(settings.redis_url)
            await client.ping()
            _cache_instance = RedisCache(client)
            log.info("Cache backend: Redis")
            return _cache_instance
    except Exception as e:
        log.info(f"Redis unavailable ({e}), using in-memory cache")

    _cache_instance = InMemoryCache()
    log.info("Cache backend: In-Memory")
    return _cache_instance


def make_cache_key(*parts: str) -> str:
    """Generate a deterministic cache key from variable parts."""
    raw = "|".join(str(p) for p in parts)
    return f"rjf:{hashlib.md5(raw.encode()).hexdigest()}"
