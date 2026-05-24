"""End-to-end agent orchestration endpoint."""

from __future__ import annotations

import time

import structlog
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.middleware.auth import require_api_key
from app.api.schemas import QueryRequest, QueryResponse
from app.api.schemas.common import TraceMeta
from app.api.schemas.query import Citation
from app.governance import get_guardrails
from app.utils.ids import new_request_id, new_trace_id
from app.workflows import get_warranty_graph

router = APIRouter(tags=["agents"])
log = structlog.get_logger(__name__)


@router.post(
    "/query",
    response_model=QueryResponse,
    dependencies=[Depends(require_api_key)],
    summary="Run the multi-agent warranty intelligence workflow",
)
async def query(req: QueryRequest) -> QueryResponse:
    started = time.perf_counter()
    request_id = new_request_id()
    trace_id = new_trace_id()
    guardrails = get_guardrails()

    # ----- Input governance -----
    input_report = guardrails.check_input(req.query)
    if input_report.blocked:
        log.warning("query_blocked_by_input_governance", reasons=input_report.reasons)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "input_blocked", "reasons": input_report.reasons},
        )

    # ----- Run the graph -----
    graph = get_warranty_graph()
    state = await graph.run(
        {
            "query": req.query,
            "vin": req.vin,
            "persona": req.persona,
            "top_k": req.top_k,
        }
    )

    duration_ms = (time.perf_counter() - started) * 1000.0

    citations: list[Citation] = []
    for c in state.get("rag_contexts", [])[:8]:
        citations.append(
            Citation(source=str(c.get("source") or c.get("id")), snippet=c.get("text", "")[:240], score=c.get("score"))
        )

    return QueryResponse(
        answer=state.get("executive_summary") or state.get("rag_answer") or "",
        citations=citations,
        agents_invoked=state.get("agents_invoked", []),
        evaluation=(state.get("evaluation") or {}).get("details"),
        governance=state.get("governance"),
        trace=TraceMeta(request_id=request_id, trace_id=trace_id, duration_ms=duration_ms),
    )
