"""Executive summarization endpoint."""

from __future__ import annotations

import time

from fastapi import APIRouter, Depends

from app.agents import ExecutiveSummaryAgent, WarrantyRetrievalAgent
from app.api.middleware.auth import require_api_key
from app.api.schemas import SummarizeRequest, SummarizeResponse
from app.api.schemas.common import TraceMeta
from app.utils.ids import new_request_id

router = APIRouter(tags=["agents"])

_retrieval = WarrantyRetrievalAgent()
_summary = ExecutiveSummaryAgent()


@router.post(
    "/summarize",
    response_model=SummarizeResponse,
    dependencies=[Depends(require_api_key)],
    summary="Generate an executive-grade summary across a scope",
)
async def summarize(req: SummarizeRequest) -> SummarizeResponse:
    started = time.perf_counter()
    seed_query = f"{req.scope} {req.component or ''} issues last {req.timeframe_days} days".strip()
    retrieval = await _retrieval.run(query=seed_query, top_k=12, component=req.component)
    claims = (retrieval.output or {}).get("claims", [])
    findings = [c.get("text", "")[:200] for c in claims[:10]]

    repair_costs = [
        float(c.get("metadata", {}).get("repair_cost_usd", 0.0) or 0.0) for c in claims
    ]
    metrics: dict[str, float] = {
        "claims_retrieved": float(len(claims)),
        "total_repair_cost_usd": float(round(sum(repair_costs), 2)),
        "avg_repair_cost_usd": float(round(sum(repair_costs) / len(repair_costs), 2) if repair_costs else 0.0),
    }

    summary = await _summary.run(
        scope=req.scope,
        timeframe_days=req.timeframe_days,
        audience=req.audience,
        findings=findings,
        metrics=metrics,
    )

    recommendations = [
        "Engage component supplier for failure-mode review.",
        "Open targeted technical service bulletin (TSB) review.",
        "Schedule field data collection on flagged VINs.",
    ]
    duration_ms = (time.perf_counter() - started) * 1000.0

    return SummarizeResponse(
        summary=(summary.output or {}).get("summary", ""),
        key_metrics=metrics,
        recommendations=recommendations,
        trace=TraceMeta(request_id=new_request_id(), duration_ms=duration_ms),
    )
