"""End-to-end RAG pipeline: ingest → chunk → embed → index, then query → answer."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.config import get_settings
from app.embeddings import get_embedder
from app.rag.chunker import Chunk, chunk_text
from app.rag.grounding import grounding_score, hallucination_score
from app.rag.retriever import HybridRetriever, RetrievedItem
from app.services.llm_provider import get_llm_provider
from app.services.vector_store import VectorRecord, get_vector_store
from app.utils.logging import get_logger

log = get_logger(__name__)


@dataclass
class IngestResult:
    document_id: str
    chunks_indexed: int
    index: str


@dataclass
class RAGAnswer:
    answer: str
    contexts: list[RetrievedItem]
    grounding: float
    hallucination: float
    model: str
    tokens_prompt: int
    tokens_completion: int


RAG_SYSTEM_PROMPT = """You are a senior warranty engineering assistant.
Answer ONLY using the supplied context.  If the context does not contain enough
information to answer, say "I don't have enough information in the provided
documents to answer reliably."  Cite source ids in square brackets like [doc_3].
Be concise, precise, and use engineering terminology."""


class RAGPipeline:
    def __init__(self) -> None:
        self._settings = get_settings()
        self._embedder = get_embedder()
        self._vstore = get_vector_store()
        self._llm = get_llm_provider()
        self.docs_retriever = HybridRetriever(self._settings.pinecone_index_docs)
        self.warranty_retriever = HybridRetriever(self._settings.pinecone_index_warranty)

    # ---------- Ingestion ----------
    async def ingest_text(
        self,
        text: str,
        *,
        document_id: str,
        source: str,
        index: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> IngestResult:
        idx = index or self._settings.pinecone_index_docs
        meta = {"source": source, **(metadata or {})}
        chunks = chunk_text(text, metadata=meta)
        if not chunks:
            return IngestResult(document_id=document_id, chunks_indexed=0, index=idx)

        vectors = await self._embedder.embed([c.text for c in chunks])
        records: list[VectorRecord] = []
        sparse_map: dict[str, str] = {}
        for chunk, vec in zip(chunks, vectors):
            rid = self._chunk_id(document_id, chunk)
            payload = {**chunk.metadata, "text": chunk.text, "document_id": document_id}
            records.append(VectorRecord(id=rid, values=vec, metadata=payload))
            sparse_map[rid] = chunk.text

        await self._vstore.upsert(idx, records)
        # Mirror into in-memory sparse index for hybrid retrieval.
        retriever = self.docs_retriever if idx == self._settings.pinecone_index_docs else self.warranty_retriever
        retriever.index_sparse(sparse_map)
        log.info("rag_ingest_complete", document_id=document_id, chunks=len(records), index=idx)
        return IngestResult(document_id=document_id, chunks_indexed=len(records), index=idx)

    async def ingest_file(self, path: str | Path, *, index: str | None = None) -> IngestResult:
        """Ingest a PDF / text file."""
        p = Path(path)
        text = _load_document(p)
        return await self.ingest_text(
            text,
            document_id=p.stem,
            source=str(p),
            index=index,
            metadata={"filename": p.name},
        )

    # ---------- Querying ----------
    async def answer(
        self,
        query: str,
        *,
        index: str = "docs",
        top_k: int = 6,
        filters: dict[str, Any] | None = None,
    ) -> RAGAnswer:
        retriever = (
            self.docs_retriever if index in {"docs", "documents"} else self.warranty_retriever
        )
        contexts = await retriever.retrieve(query, top_k=top_k, filters=filters)
        prompt = _build_prompt(query, contexts)
        resp = await self._llm.complete(prompt, system=RAG_SYSTEM_PROMPT, temperature=0.1, max_tokens=600)

        ctx_texts = [c.text for c in contexts]
        g = grounding_score(resp.text, ctx_texts).score
        h = hallucination_score(resp.text, ctx_texts)
        return RAGAnswer(
            answer=resp.text,
            contexts=contexts,
            grounding=g,
            hallucination=h,
            model=resp.model,
            tokens_prompt=resp.tokens_prompt,
            tokens_completion=resp.tokens_completion,
        )

    # ---------- Helpers ----------
    @staticmethod
    def _chunk_id(document_id: str, chunk: Chunk) -> str:
        h = hashlib.sha1(f"{document_id}:{chunk.index}:{chunk.text[:32]}".encode()).hexdigest()[:16]
        return f"{document_id}__{chunk.index}__{h}"


def _build_prompt(query: str, contexts: list[RetrievedItem]) -> str:
    blocks: list[str] = []
    for i, c in enumerate(contexts, start=1):
        tag = f"[doc_{i}]"
        src = c.source or c.metadata.get("source") or c.id
        blocks.append(f"{tag} (source={src})\n{c.text.strip()}")
    context_section = "\n\n".join(blocks) if blocks else "(no context retrieved)"
    return (
        f"Question:\n{query}\n\n"
        f"Context:\n{context_section}\n\n"
        f"Answer (cite source ids like [doc_1]):"
    )


def _load_document(p: Path) -> str:
    if p.suffix.lower() == ".pdf":
        try:
            from pypdf import PdfReader

            reader = PdfReader(str(p))
            return "\n\n".join((page.extract_text() or "") for page in reader.pages)
        except Exception as exc:
            log.warning("pdf_parse_failed", path=str(p), error=str(exc))
            return ""
    return p.read_text(encoding="utf-8", errors="ignore")


_pipeline: RAGPipeline | None = None


def get_rag_pipeline() -> RAGPipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = RAGPipeline()
    return _pipeline


def reset_rag_pipeline() -> None:
    global _pipeline
    _pipeline = None
