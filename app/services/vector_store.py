"""Vector store abstraction.

Supports:
- Pinecone (production)
- In-memory FAISS-like fallback (dev / tests)

The interface is intentionally narrow — upsert, query, delete — so swapping
backends does not ripple into agents or RAG pipelines.
"""

from __future__ import annotations

import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from app.config import Settings, get_settings
from app.observability.metrics import RETRIEVAL_HITS, RETRIEVAL_LATENCY
from app.utils.logging import get_logger

log = get_logger(__name__)


@dataclass
class VectorRecord:
    id: str
    values: list[float]
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class VectorHit:
    id: str
    score: float
    metadata: dict[str, Any]


class VectorStore(ABC):
    @abstractmethod
    async def upsert(self, index: str, records: list[VectorRecord]) -> int: ...

    @abstractmethod
    async def query(
        self,
        index: str,
        vector: list[float],
        top_k: int = 8,
        filters: dict[str, Any] | None = None,
    ) -> list[VectorHit]: ...

    @abstractmethod
    async def delete(self, index: str, ids: list[str]) -> int: ...


# ---------------- Pinecone ----------------
class PineconeVectorStore(VectorStore):
    """Async wrapper over the Pinecone v5 SDK (which is sync-only)."""

    def __init__(self, settings: Settings) -> None:
        from pinecone import Pinecone

        self._settings = settings
        api_key = settings.pinecone_api_key.get_secret_value()
        if not api_key:
            raise RuntimeError("PINECONE_API_KEY is not configured.")
        self._pc = Pinecone(api_key=api_key)
        self._indexes: dict[str, Any] = {}

    def _get(self, index: str):  # type: ignore[no-untyped-def]
        if index not in self._indexes:
            self._indexes[index] = self._pc.Index(index)
        return self._indexes[index]

    async def upsert(self, index: str, records: list[VectorRecord]) -> int:
        if not records:
            return 0
        payload = [(r.id, r.values, r.metadata) for r in records]
        idx = self._get(index)
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: idx.upsert(vectors=payload))
        return len(records)

    async def query(
        self,
        index: str,
        vector: list[float],
        top_k: int = 8,
        filters: dict[str, Any] | None = None,
    ) -> list[VectorHit]:
        idx = self._get(index)
        started = time.perf_counter()
        loop = asyncio.get_event_loop()
        try:
            resp = await loop.run_in_executor(
                None,
                lambda: idx.query(
                    vector=vector,
                    top_k=top_k,
                    include_metadata=True,
                    filter=filters,
                ),
            )
        finally:
            RETRIEVAL_LATENCY.labels(index=index).observe(time.perf_counter() - started)

        matches = getattr(resp, "matches", []) or []
        hits = [
            VectorHit(id=m["id"], score=float(m["score"]), metadata=m.get("metadata") or {})
            for m in matches
        ]
        RETRIEVAL_HITS.labels(index=index).inc(len(hits))
        return hits

    async def delete(self, index: str, ids: list[str]) -> int:
        if not ids:
            return 0
        idx = self._get(index)
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: idx.delete(ids=ids))
        return len(ids)


# ---------------- In-memory fallback ----------------
class InMemoryVectorStore(VectorStore):
    """Dev / test backend. Cosine similarity, naive scan.

    Not suitable for production but invaluable for unit/integration tests where
    spinning up a real vector DB is overkill.
    """

    def __init__(self) -> None:
        self._data: dict[str, dict[str, VectorRecord]] = {}

    @staticmethod
    def _cos(a: list[float], b: list[float]) -> float:
        import math

        if not a or not b or len(a) != len(b):
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        na = math.sqrt(sum(x * x for x in a))
        nb = math.sqrt(sum(y * y for y in b))
        if na == 0 or nb == 0:
            return 0.0
        return dot / (na * nb)

    async def upsert(self, index: str, records: list[VectorRecord]) -> int:
        bucket = self._data.setdefault(index, {})
        for r in records:
            bucket[r.id] = r
        return len(records)

    async def query(
        self,
        index: str,
        vector: list[float],
        top_k: int = 8,
        filters: dict[str, Any] | None = None,
    ) -> list[VectorHit]:
        started = time.perf_counter()
        bucket = self._data.get(index, {})
        scored: list[VectorHit] = []
        for r in bucket.values():
            if filters and not all(r.metadata.get(k) == v for k, v in filters.items()):
                continue
            scored.append(VectorHit(id=r.id, score=self._cos(vector, r.values), metadata=r.metadata))
        scored.sort(key=lambda h: h.score, reverse=True)
        RETRIEVAL_LATENCY.labels(index=index).observe(time.perf_counter() - started)
        RETRIEVAL_HITS.labels(index=index).inc(min(len(scored), top_k))
        return scored[:top_k]

    async def delete(self, index: str, ids: list[str]) -> int:
        bucket = self._data.get(index, {})
        removed = 0
        for i in ids:
            if i in bucket:
                del bucket[i]
                removed += 1
        return removed


# ---------------- Factory ----------------
_store: VectorStore | None = None


def get_vector_store() -> VectorStore:
    global _store
    if _store is not None:
        return _store
    settings = get_settings()
    if settings.vector_backend == "pinecone" and settings.pinecone_api_key.get_secret_value():
        try:
            _store = PineconeVectorStore(settings)
            log.info("vector_store_initialized", backend="pinecone")
            return _store
        except Exception as exc:
            log.warning("pinecone_init_failed_falling_back_to_memory", error=str(exc))
    _store = InMemoryVectorStore()
    log.info("vector_store_initialized", backend="in_memory")
    return _store


def reset_vector_store() -> None:
    global _store
    _store = None
