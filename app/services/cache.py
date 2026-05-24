"""Async cache wrapper (Redis with in-memory fallback)."""

from __future__ import annotations

import json
from typing import Any

from app.config import get_settings
from app.observability.metrics import CACHE_HITS, CACHE_MISSES
from app.utils.logging import get_logger

log = get_logger(__name__)


class AsyncCache:
    """Minimal async cache abstraction.

    Tries Redis first; falls back to an in-memory dict if Redis is unreachable
    (useful for tests and local dev without docker-compose up).
    """

    def __init__(self) -> None:
        self._settings = get_settings()
        self._memory: dict[str, str] = {}
        self._redis = None

    async def _client(self):  # type: ignore[no-untyped-def]
        if self._redis is not None:
            return self._redis
        try:
            from redis.asyncio import from_url

            client = from_url(self._settings.redis_url, decode_responses=True)
            await client.ping()
            self._redis = client
            return self._redis
        except Exception as exc:
            log.debug("redis_unavailable_using_memory", error=str(exc))
            return None

    async def get(self, namespace: str, key: str) -> Any | None:
        client = await self._client()
        composite = f"{namespace}:{key}"
        try:
            raw = await client.get(composite) if client is not None else self._memory.get(composite)
        except Exception as exc:
            log.debug("cache_get_failed", error=str(exc))
            raw = self._memory.get(composite)
        if raw is None:
            CACHE_MISSES.labels(namespace=namespace).inc()
            return None
        CACHE_HITS.labels(namespace=namespace).inc()
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return raw

    async def set(self, namespace: str, key: str, value: Any, ttl: int | None = None) -> None:
        composite = f"{namespace}:{key}"
        payload = json.dumps(value, default=str)
        ttl = ttl if ttl is not None else self._settings.cache_ttl_seconds
        client = await self._client()
        try:
            if client is not None:
                await client.set(composite, payload, ex=ttl)
                return
        except Exception as exc:
            log.debug("cache_set_failed", error=str(exc))
        self._memory[composite] = payload


_cache: AsyncCache | None = None


def get_cache() -> AsyncCache:
    global _cache
    if _cache is None:
        _cache = AsyncCache()
    return _cache
