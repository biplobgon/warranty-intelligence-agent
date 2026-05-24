"""Pure retrieval endpoint (no LLM generation)."""

from __future__ import annotations

import time

from fastapi import APIRouter, Depends

from app.api.middleware.auth import require_api_key
from app.api.schemas import RetrieveRequest, RetrieveResponse
from app.api.schemas.common import TraceMeta
from app.api.schemas.query import RetrievedDocument
from app.config import get_settings
from app.rag.retriever import HybridRetriever
from app.utils.ids import new_request_id

router = APIRouter(tags=["rag"])


@router.post(
    "/retrieve",
    response_model=RetrieveResponse,
    dependencies=[Depends(require_api_key)],
    summary="Hybrid (dense+sparse) retrieval across warranty and document indexes",
)
async def retrieve(req: RetrieveRequest) -> RetrieveResponse:
    started = time.perf_counter()
    settings = get_settings()
    index_name = {
        "docs": settings.pinecone_index_docs,
        "warranty": settings.pinecone_index_warranty,
        "hybrid": settings.pinecone_index_docs,
    }[req.index]
    retriever = HybridRetriever(index_name)
    hits = await retriever.retrieve(req.query, top_k=req.top_k, filters=req.filters)
    duration_ms = (time.perf_counter() - started) * 1000.0
    return RetrieveResponse(
        query=req.query,
        documents=[
            RetrievedDocument(
                id=h.id, score=h.score, text=h.text, source=h.source, metadata=h.metadata
            )
            for h in hits
        ],
        trace=TraceMeta(request_id=new_request_id(), duration_ms=duration_ms),
    )
