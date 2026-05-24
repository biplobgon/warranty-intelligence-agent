"""Inference engine facade.

Wraps the configured ``LLMProvider`` with:
* per-request micro-batching for embeddings
* Redis-backed result cache for deterministic prompts
* optional Ray remote execution for horizontal scale-out

This is the entry-point the agents *should* use whenever they want batched
or cached inference; for single ad-hoc calls, the provider directly is fine.
"""

from __future__ import annotations

import hashlib
from typing import Any

from app.inference.batcher import InferenceBatcher
from app.services.cache import get_cache
from app.services.llm_provider import LLMResponse, get_llm_provider
from app.utils.logging import get_logger

log = get_logger(__name__)


class InferenceEngine:
    def __init__(self) -> None:
        self._provider = get_llm_provider()
        self._cache = get_cache()
        self._embed_batcher = InferenceBatcher(self._provider.embed, max_batch=64, max_wait_ms=20)

    async def complete(
        self,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 1024,
        cache: bool = False,
        **kwargs: Any,
    ) -> LLMResponse:
        cache_key = None
        if cache and temperature == 0.0:
            cache_key = self._key(prompt, system, max_tokens)
            cached = await self._cache.get("llm", cache_key)
            if cached is not None:
                return LLMResponse(**cached)

        resp = await self._provider.complete(
            prompt, system=system, temperature=temperature, max_tokens=max_tokens, **kwargs
        )

        if cache_key:
            await self._cache.set(
                "llm",
                cache_key,
                {
                    "text": resp.text,
                    "model": resp.model,
                    "tokens_prompt": resp.tokens_prompt,
                    "tokens_completion": resp.tokens_completion,
                },
            )
        return resp

    async def embed_one(self, text: str) -> list[float]:
        return await self._embed_batcher.submit(text)  # type: ignore[return-value]

    async def embed_many(self, texts: list[str]) -> list[list[float]]:
        return await self._provider.embed(texts)

    @staticmethod
    def _key(prompt: str, system: str | None, max_tokens: int) -> str:
        h = hashlib.sha1()
        h.update((system or "").encode())
        h.update(b"\x00")
        h.update(prompt.encode())
        h.update(f"|{max_tokens}".encode())
        return h.hexdigest()


_engine: InferenceEngine | None = None


def get_inference_engine() -> InferenceEngine:
    global _engine
    if _engine is None:
        _engine = InferenceEngine()
    return _engine
