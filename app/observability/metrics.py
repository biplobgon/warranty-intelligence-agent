"""Prometheus metrics.

These are deliberately tuned for LLM/agent workloads:
- token usage (input vs output)
- per-agent latency histograms
- retrieval latency + hit-rate
- hallucination / grounding scores (observed as gauges/histograms)
"""

from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram
from prometheus_fastapi_instrumentator import Instrumentator

# ---- Request-level metrics ----
REQUEST_DURATION = Histogram(
    "warranty_request_duration_seconds",
    "End-to-end request duration in seconds, by route and outcome.",
    ["route", "outcome"],
    buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 20.0, 60.0),
)

# ---- LLM metrics ----
LLM_TOKEN_USAGE = Counter(
    "warranty_llm_token_usage_total",
    "LLM tokens consumed, by model and kind (prompt|completion).",
    ["model", "kind"],
)

LLM_CALL_LATENCY = Histogram(
    "warranty_llm_call_latency_seconds",
    "LLM call latency, by model.",
    ["model"],
    buckets=(0.1, 0.25, 0.5, 1.0, 2.0, 4.0, 8.0, 15.0, 30.0),
)

LLM_CALL_ERRORS = Counter(
    "warranty_llm_call_errors_total",
    "LLM call errors, by model and error class.",
    ["model", "error"],
)

# ---- Agent metrics ----
AGENT_INVOCATIONS = Counter(
    "warranty_agent_invocations_total",
    "Number of agent invocations, by agent name and status.",
    ["agent", "status"],
)

AGENT_LATENCY = Histogram(
    "warranty_agent_latency_seconds",
    "Per-agent execution latency.",
    ["agent"],
    buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0),
)

# ---- Retrieval metrics ----
RETRIEVAL_LATENCY = Histogram(
    "warranty_retrieval_latency_seconds",
    "Vector / hybrid retrieval latency, by index.",
    ["index"],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0),
)

RETRIEVAL_HITS = Counter(
    "warranty_retrieval_hits_total",
    "Retrieval results returned, by index.",
    ["index"],
)

# ---- Quality metrics ----
HALLUCINATION_SCORE = Histogram(
    "warranty_hallucination_score",
    "Per-response hallucination score (0=grounded, 1=hallucinated).",
    buckets=(0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0),
)

GROUNDING_SCORE = Histogram(
    "warranty_grounding_score",
    "Per-response grounding score (0=ungrounded, 1=fully grounded).",
    buckets=(0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0),
)

GOVERNANCE_BLOCKS = Counter(
    "warranty_governance_blocks_total",
    "Responses blocked by governance / guardrails, by reason.",
    ["reason"],
)

# ---- System / cache ----
CACHE_HITS = Counter("warranty_cache_hits_total", "Cache hits", ["namespace"])
CACHE_MISSES = Counter("warranty_cache_misses_total", "Cache misses", ["namespace"])

INFLIGHT_REQUESTS = Gauge(
    "warranty_inflight_requests",
    "In-flight requests being processed.",
)


def setup_metrics(app) -> None:  # type: ignore[no-untyped-def]
    """Attach Prometheus instrumentation to a FastAPI app."""
    instrumentator = Instrumentator(
        should_group_status_codes=True,
        should_ignore_untemplated=True,
        should_respect_env_var=False,
        excluded_handlers=["/metrics", "/health"],
    )
    instrumentator.instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)
