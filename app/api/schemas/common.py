"""Shared API schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Liveness / readiness payload."""

    status: str = Field(..., examples=["ok"])
    version: str
    environment: str
    timestamp: datetime
    components: dict[str, str] = Field(
        default_factory=dict,
        description="Per-dependency health (llm, vector_store, redis, ...).",
    )


class ErrorResponse(BaseModel):
    """Uniform error envelope."""

    error: str
    detail: str | None = None
    request_id: str | None = None
    context: dict[str, Any] | None = None


class TraceMeta(BaseModel):
    """Trace metadata attached to LLM responses."""

    request_id: str
    trace_id: str | None = None
    duration_ms: float
    model: str | None = None
    tokens_prompt: int | None = None
    tokens_completion: int | None = None
