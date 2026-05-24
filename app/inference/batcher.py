"""Lightweight async micro-batcher for embeddings / completions.

Coalesces concurrent single-item calls into batched requests within a small
time window (default 20ms) to dramatically improve throughput against rate-
limited LLM endpoints.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass
class _PendingItem:
    payload: Any
    future: asyncio.Future = field(default_factory=lambda: asyncio.get_event_loop().create_future())


class InferenceBatcher:
    """Generic async batcher.

    Args:
        batch_fn:   coroutine that accepts a list of payloads and returns a list of results.
        max_batch:  maximum batch size.
        max_wait_ms: maximum time to wait for a full batch before flushing.
    """

    def __init__(
        self,
        batch_fn: Callable[[list[Any]], Awaitable[list[Any]]],
        *,
        max_batch: int = 32,
        max_wait_ms: int = 20,
    ) -> None:
        self._batch_fn = batch_fn
        self._max_batch = max_batch
        self._max_wait_s = max_wait_ms / 1000.0
        self._queue: list[_PendingItem] = []
        self._lock = asyncio.Lock()
        self._flush_task: asyncio.Task | None = None

    async def submit(self, payload: Any) -> Any:
        item = _PendingItem(payload=payload)
        async with self._lock:
            self._queue.append(item)
            if self._flush_task is None or self._flush_task.done():
                self._flush_task = asyncio.create_task(self._flush_loop())
            if len(self._queue) >= self._max_batch:
                await self._flush_now()
        return await item.future

    async def _flush_loop(self) -> None:
        await asyncio.sleep(self._max_wait_s)
        async with self._lock:
            await self._flush_now()

    async def _flush_now(self) -> None:
        if not self._queue:
            return
        batch = self._queue
        self._queue = []
        payloads = [it.payload for it in batch]
        try:
            results = await self._batch_fn(payloads)
            for it, res in zip(batch, results):
                if not it.future.done():
                    it.future.set_result(res)
        except Exception as exc:
            for it in batch:
                if not it.future.done():
                    it.future.set_exception(exc)
