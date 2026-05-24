"""Evaluation & Governance Agent.

Runs the deterministic evaluator over (question, answer, contexts) and surfaces
hallucination / grounding signals.  This agent is intentionally NON-LLM —
deterministic scoring makes governance auditable and reproducible.
"""

from __future__ import annotations

from typing import Any

from app.agents.base import BaseAgent
from app.evaluation import get_evaluator
from app.governance import get_guardrails


class EvaluationAgent(BaseAgent):
    name = "evaluation_governance"

    def __init__(self) -> None:
        self._evaluator = get_evaluator()
        self._guardrails = get_guardrails()

    async def _execute(
        self,
        *,
        question: str,
        answer: str,
        contexts: list[str],
        reference: str | None = None,
        **_: Any,
    ) -> dict[str, Any]:
        result = self._evaluator.evaluate(question, answer, contexts, reference=reference)
        gov = self._guardrails.check_output(
            answer,
            hallucination_score=result.hallucination_score,
            grounding_score=result.grounding_score,
        )
        return {
            "evaluation": {
                "hallucination_score": result.hallucination_score,
                "grounding_score": result.grounding_score,
                "answer_relevancy": result.answer_relevancy,
                "semantic_similarity": result.semantic_similarity,
                "passed_thresholds": result.passed_thresholds,
                "details": result.details,
            },
            "governance": gov.model_dump(),
        }
