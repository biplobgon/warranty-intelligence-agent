"""Standalone evaluation endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.middleware.auth import require_api_key
from app.api.schemas import EvaluationRequest, EvaluationResponse
from app.evaluation import get_evaluator

router = APIRouter(tags=["evaluation"])


@router.post(
    "/evaluate",
    response_model=EvaluationResponse,
    dependencies=[Depends(require_api_key)],
    summary="Evaluate an (answer, contexts) pair for hallucination/grounding",
)
async def evaluate(req: EvaluationRequest) -> EvaluationResponse:
    evaluator = get_evaluator()
    result = evaluator.evaluate(req.question, req.answer, req.contexts, reference=req.reference)
    return EvaluationResponse(
        hallucination_score=result.hallucination_score,
        grounding_score=result.grounding_score,
        answer_relevancy=result.answer_relevancy,
        semantic_similarity=result.semantic_similarity,
        passed_thresholds=result.passed_thresholds,
        details=result.details,
    )
