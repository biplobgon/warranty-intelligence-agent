"""Root cause analysis endpoint."""

from __future__ import annotations

import time

from fastapi import APIRouter, Depends

from app.agents import RootCauseAgent, WarrantyRetrievalAgent
from app.api.middleware.auth import require_api_key
from app.api.schemas import AnalyzeRequest, AnalyzeResponse
from app.api.schemas.common import TraceMeta
from app.api.schemas.query import RootCauseHypothesis
from app.utils.ids import new_request_id

router = APIRouter(tags=["agents"])

_retrieval = WarrantyRetrievalAgent()
_root_cause = RootCauseAgent()


@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
    dependencies=[Depends(require_api_key)],
    summary="Root cause analysis over warranty + technical evidence",
)
async def analyze(req: AnalyzeRequest) -> AnalyzeResponse:
    started = time.perf_counter()

    # Pull supporting evidence from the warranty index for grounded reasoning.
    retrieval = await _retrieval.run(
        query=req.issue_description, top_k=8, component=req.component, vin=req.vin
    )
    evidence = [c.get("text", "") for c in (retrieval.output or {}).get("claims", [])]

    rc = await _root_cause.run(
        issue=req.issue_description,
        component=req.component,
        history=req.claim_history,
        evidence=evidence,
    )
    hypotheses = (rc.output or {}).get("hypotheses", [])

    summary = "; ".join(h["cause"] for h in hypotheses[:3]) or "No root cause could be determined."
    duration_ms = (time.perf_counter() - started) * 1000.0

    return AnalyzeResponse(
        hypotheses=[
            RootCauseHypothesis(
                cause=h["cause"],
                probability=h["probability"],
                evidence=h["evidence"],
                recommended_actions=h["recommended_actions"],
            )
            for h in hypotheses
        ],
        summary=summary,
        trace=TraceMeta(request_id=new_request_id(), duration_ms=duration_ms),
    )
