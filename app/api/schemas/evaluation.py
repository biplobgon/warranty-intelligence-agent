"""Evaluation API schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class EvaluationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str
    answer: str
    contexts: list[str] = Field(default_factory=list)
    reference: str | None = None


class EvaluationResponse(BaseModel):
    hallucination_score: float = Field(..., ge=0.0, le=1.0)
    grounding_score: float = Field(..., ge=0.0, le=1.0)
    answer_relevancy: float = Field(..., ge=0.0, le=1.0)
    semantic_similarity: float | None = None
    passed_thresholds: bool
    details: dict[str, float] = Field(default_factory=dict)
