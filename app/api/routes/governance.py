"""Governance endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.api.middleware.auth import require_api_key
from app.api.schemas import GovernanceReport
from app.governance import get_guardrails

router = APIRouter(prefix="/governance", tags=["governance"])


class GovernanceCheckRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=16000)
    direction: str = Field("input", pattern="^(input|output)$")
    hallucination_score: float | None = None
    grounding_score: float | None = None


@router.post("/check", response_model=GovernanceReport, dependencies=[Depends(require_api_key)])
async def check(req: GovernanceCheckRequest) -> GovernanceReport:
    guardrails = get_guardrails()
    if req.direction == "input":
        return guardrails.check_input(req.text)
    return guardrails.check_output(
        req.text,
        hallucination_score=req.hallucination_score,
        grounding_score=req.grounding_score,
    )


@router.get("/policy", summary="Active governance policy metadata")
async def policy() -> dict[str, object]:
    g = get_guardrails()
    return {
        "policy_version": g.policy_version,
        "thresholds": {
            "hallucination_max": g._settings.hallucination_threshold,
            "grounding_min": g._settings.grounding_threshold,
        },
        "features": {
            "guardrails_enabled": g._settings.enable_guardrails,
            "pii_redaction_enabled": g._settings.enable_pii_redaction,
        },
    }
