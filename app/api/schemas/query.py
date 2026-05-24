"""Schemas for the user-facing query, retrieve, analyze, summarize endpoints."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.api.schemas.common import TraceMeta


# ---------- Retrieve ----------
class RetrieveRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str = Field(..., min_length=1, max_length=4000)
    top_k: int = Field(8, ge=1, le=50)
    index: Literal["warranty", "docs", "hybrid"] = "hybrid"
    filters: dict[str, Any] | None = None


class RetrievedDocument(BaseModel):
    id: str
    score: float
    text: str
    source: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class RetrieveResponse(BaseModel):
    query: str
    documents: list[RetrievedDocument]
    trace: TraceMeta


# ---------- Query (full agent orchestration) ----------
class QueryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str = Field(..., min_length=1, max_length=4000)
    vin: str | None = Field(None, pattern=r"^[A-HJ-NPR-Z0-9]{11,17}$")
    top_k: int = Field(8, ge=1, le=50)
    include_evaluation: bool = True
    persona: Literal["engineer", "executive", "service_tech"] = "engineer"
    metadata: dict[str, Any] | None = None


class Citation(BaseModel):
    source: str
    snippet: str
    score: float | None = None


class QueryResponse(BaseModel):
    answer: str
    citations: list[Citation] = Field(default_factory=list)
    agents_invoked: list[str] = Field(default_factory=list)
    evaluation: dict[str, float] | None = None
    governance: dict[str, Any] | None = None
    trace: TraceMeta


# ---------- Analyze (root cause) ----------
class AnalyzeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    issue_description: str = Field(..., min_length=10, max_length=4000)
    component: str | None = None
    vin: str | None = None
    claim_history: list[dict[str, Any]] | None = None


class RootCauseHypothesis(BaseModel):
    cause: str
    probability: float = Field(..., ge=0.0, le=1.0)
    evidence: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)


class AnalyzeResponse(BaseModel):
    hypotheses: list[RootCauseHypothesis]
    summary: str
    trace: TraceMeta


# ---------- Summarize (executive) ----------
class SummarizeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scope: Literal["claim", "vehicle", "fleet", "component"] = "fleet"
    timeframe_days: int = Field(30, ge=1, le=730)
    component: str | None = None
    audience: Literal["executive", "engineering", "service"] = "executive"


class SummarizeResponse(BaseModel):
    summary: str
    key_metrics: dict[str, float]
    recommendations: list[str]
    trace: TraceMeta
