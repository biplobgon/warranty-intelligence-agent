"""Embedding generation.

Delegates to the configured LLM provider's embedding API, batched for throughput.
For local/dev use without API keys, falls back to a deterministic hash-based
pseudo-embedding so the rest of the pipeline keeps working.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from app.services.llm_provider import get_llm_provider
from app.utils.logging import get_logger

log = get_logger(__name__)


@dataclass
class EmbedResult:
    text: str
    vector: list[float]


class Embedder:
    def __init__(self, dim: int = 1536, batch_size: int = 64) -> None:
        self.dim = dim
        self.batch_size = batch_size

    async def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        try:
            provider = get_llm_provider()
            vectors: list[list[float]] = []
            for i in range(0, len(texts), self.batch_size):
                batch = texts[i : i + self.batch_size]
                vectors.extend(await provider.embed(batch))
            return vectors
        except Exception as exc:
            log.warning("embedding_provider_failed_using_hash_fallback", error=str(exc))
            return [self._hash_embed(t) for t in texts]

    def _hash_embed(self, text: str) -> list[float]:
        """Deterministic pseudo-embedding for offline/dev use.

        Not semantically meaningful — only ensures determinism and shape.
        """
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        # Expand digest deterministically to `self.dim` floats in [-1, 1].
        floats: list[float] = []
        seed = 0
        while len(floats) < self.dim:
            seed_bytes = hashlib.sha256(digest + seed.to_bytes(4, "big")).digest()
            for i in range(0, len(seed_bytes), 2):
                if len(floats) >= self.dim:
                    break
                val = int.from_bytes(seed_bytes[i : i + 2], "big") / 65535.0
                floats.append((val * 2.0) - 1.0)
            seed += 1
        return floats


_embedder: Embedder | None = None


def get_embedder() -> Embedder:
    global _embedder
    if _embedder is None:
        _embedder = Embedder()
    return _embedder
