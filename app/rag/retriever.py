"""Hybrid retriever: dense (vector) + sparse (BM25-style) fusion with optional reranker.

Implements a pragmatic Reciprocal Rank Fusion (RRF) over two ranked lists
(vector search + lexical search) followed by an optional cross-encoder rerank.
"""

from __future__ import annotations

import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any

from app.config import get_settings
from app.embeddings import get_embedder
from app.observability.metrics import RETRIEVAL_HITS
from app.services.vector_store import VectorHit, get_vector_store
from app.utils.logging import get_logger

log = get_logger(__name__)


@dataclass
class RetrievedItem:
    id: str
    text: str
    score: float
    source: str | None
    metadata: dict[str, Any]


class HybridRetriever:
    """Dense + sparse retrieval with RRF fusion."""

    def __init__(self, index: str) -> None:
        self.index = index
        self._settings = get_settings()
        self._store = get_vector_store()
        self._embedder = get_embedder()
        # Lightweight in-memory sparse corpus for hybrid scoring.
        # Production deployments should back this with Elasticsearch or OpenSearch.
        self._sparse_corpus: dict[str, str] = {}

    def index_sparse(self, docs: dict[str, str]) -> None:
        """Register raw text for lexical scoring."""
        self._sparse_corpus.update(docs)

    async def retrieve(
        self,
        query: str,
        top_k: int = 8,
        filters: dict[str, Any] | None = None,
    ) -> list[RetrievedItem]:
        # ---- Dense ----
        vector = (await self._embedder.embed([query]))[0]
        dense_hits = await self._store.query(self.index, vector, top_k=top_k * 2, filters=filters)

        if not self._settings.feature_hybrid_retrieval or not self._sparse_corpus:
            return _to_items(dense_hits[:top_k])

        # ---- Sparse (BM25-lite) ----
        sparse_hits = _bm25_topk(query, self._sparse_corpus, top_k=top_k * 2)

        # ---- RRF fusion ----
        fused = _rrf([h.id for h in dense_hits], [doc_id for doc_id, _ in sparse_hits])
        # Build merged items.
        meta_by_id: dict[str, dict[str, Any]] = {h.id: h.metadata for h in dense_hits}
        score_by_id: dict[str, float] = {h.id: h.score for h in dense_hits}
        for doc_id, _ in sparse_hits:
            meta_by_id.setdefault(doc_id, {"text": self._sparse_corpus.get(doc_id, "")})

        ranked_ids = [doc_id for doc_id, _ in sorted(fused.items(), key=lambda kv: kv[1], reverse=True)]
        items: list[RetrievedItem] = []
        for doc_id in ranked_ids[:top_k]:
            meta = meta_by_id.get(doc_id, {})
            items.append(
                RetrievedItem(
                    id=doc_id,
                    text=meta.get("text", self._sparse_corpus.get(doc_id, "")),
                    score=score_by_id.get(doc_id, fused[doc_id]),
                    source=meta.get("source"),
                    metadata=meta,
                )
            )
        RETRIEVAL_HITS.labels(index=self.index).inc(len(items))
        return items


def _to_items(hits: list[VectorHit]) -> list[RetrievedItem]:
    return [
        RetrievedItem(
            id=h.id,
            text=h.metadata.get("text", ""),
            score=h.score,
            source=h.metadata.get("source"),
            metadata=h.metadata,
        )
        for h in hits
    ]


_WORD_RE = re.compile(r"[A-Za-z0-9]+")


def _tokenize(s: str) -> list[str]:
    return [t.lower() for t in _WORD_RE.findall(s)]


def _bm25_topk(query: str, corpus: dict[str, str], top_k: int = 16, k1: float = 1.5, b: float = 0.75):
    """Compact BM25 implementation."""
    q_tokens = _tokenize(query)
    if not q_tokens or not corpus:
        return []
    docs = {doc_id: _tokenize(text) for doc_id, text in corpus.items()}
    n_docs = len(docs)
    avgdl = sum(len(d) for d in docs.values()) / max(n_docs, 1)
    df: Counter[str] = Counter()
    for tokens in docs.values():
        df.update(set(tokens))
    idf = {t: math.log((n_docs - df[t] + 0.5) / (df[t] + 0.5) + 1.0) for t in set(q_tokens)}

    scores: dict[str, float] = {}
    for doc_id, tokens in docs.items():
        tf = Counter(tokens)
        dl = len(tokens) or 1
        s = 0.0
        for t in q_tokens:
            if t not in tf:
                continue
            num = tf[t] * (k1 + 1)
            den = tf[t] + k1 * (1 - b + b * dl / avgdl)
            s += idf.get(t, 0.0) * (num / den)
        if s > 0:
            scores[doc_id] = s
    return sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:top_k]


def _rrf(ranking_a: list[str], ranking_b: list[str], k: int = 60) -> dict[str, float]:
    """Reciprocal Rank Fusion."""
    out: dict[str, float] = defaultdict(float)
    for rank, doc_id in enumerate(ranking_a):
        out[doc_id] += 1.0 / (k + rank + 1)
    for rank, doc_id in enumerate(ranking_b):
        out[doc_id] += 1.0 / (k + rank + 1)
    return out
