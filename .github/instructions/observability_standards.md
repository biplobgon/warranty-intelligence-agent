# Observability Standards

> What every contributor must instrument when shipping code.

## Three pillars

| Pillar | Tool | Where |
|---|---|---|
| Metrics | Prometheus | `app/observability/metrics.py` |
| Traces | OpenTelemetry | `app/observability/tracing.py` |
| Logs | structlog (JSON in prod) | `app/utils/logging.py` |

Experiment tracking (MLflow) is a fourth, AI-specific pillar.

## Metric design rules

- Naming: `warranty_<domain>_<unit>{labels}`.
- Units: `seconds`, `bytes`, `total` (counters), `score` (0..1).
- Label cardinality: **strictly < ~10 unique values per label**. NEVER use VIN,
  claim_id, request_id, user_id, or free-text as labels.
- Latency: histograms, not gauges.
- Counts: counters, not gauges.
- State at a point in time (queue depth, in-flight): gauges.
- Bucket bounds: choose to capture both P50 and P99 meaningfully. The platform's
  default histogram buckets are tuned for LLM workloads (50 ms – 60 s).

## What must be instrumented

| Event | Metric |
|---|---|
| Every LLM call | `warranty_llm_call_latency_seconds`, `warranty_llm_token_usage_total`, `warranty_llm_call_errors_total` (on error) |
| Every agent run | `warranty_agent_invocations_total`, `warranty_agent_latency_seconds` |
| Every retrieval | `warranty_retrieval_latency_seconds`, `warranty_retrieval_hits_total` |
| Every response | `warranty_hallucination_score`, `warranty_grounding_score` |
| Every governance decision | `warranty_governance_blocks_total{reason}` |
| Every cache op | `warranty_cache_hits_total`, `warranty_cache_misses_total` |
| Every request | `warranty_request_duration_seconds`, `warranty_inflight_requests` |

## Trace design rules

- Service name: set via `OTEL_SERVICE_NAME` (default `warranty-intel-api`).
- Spans for: every API request (auto), every outbound HTTPX call (auto), every
  agent `_execute`, every retrieval, every LLM call.
- Span attributes: include `request_id`, agent name, model name. NEVER include
  user input verbatim — include length / hash if needed.
- Don't create spans for cheap pure-Python work (< 1 ms).

## Log design rules

- structlog only. Get logger via `get_logger(__name__)`.
- key=value form. No f-strings. No multi-line strings.
- Include `request_id` automatically (already bound by middleware).
- Levels:
  - `debug` — local development; verbose
  - `info` — normal lifecycle (startup, agent_run_complete, ingest_complete)
  - `warning` — recoverable problems (retry, fallback, degraded mode)
  - `error` — non-recoverable, request-affecting
  - `exception` — paired with a real exception, includes stack trace
- NEVER log PII, prompts, completions, secrets, or full bodies. Log shapes /
  counts / hashes instead.

## Dashboards

- `warranty-overview` dashboard ships pre-built panels (RPS, latency p95,
  per-agent latency, token throughput, hallucination distribution, governance
  blocks, cache hit ratio).
- New top-level metric ⇒ add a panel (and update the dashboard JSON).
- Group panels by concern (request, LLM, retrieval, quality, governance, cache).

## Alerts (recommended, not yet wired)

- p95 `/query` latency > 8 s for 10 min → page on-call.
- Hallucination p50 > 0.5 for 30 min → page on-call (quality incident).
- `warranty_governance_blocks_total{reason="banned_phrase"}` rate > 0 → notify (audit).
- `warranty_llm_call_errors_total` rate > 5/min → page on-call.
- Cache hit ratio < 0.2 for 1 h → notify (cost incident).

## Sampling

- 100% lexical grounding (cheap).
- 0% LLM-as-judge online (cost). Run periodically via `scripts/eval_benchmark.py`.
- Adjust trace sampling via the OTel collector (typically 100% in staging, 5–10% in prod).

## DO

- Instrument before optimizing.
- Use histograms for anything time-related.
- Test that new metrics appear at `/metrics`.
- Update the Grafana dashboard when adding a metric you care about.

## DON'T

- Don't add high-cardinality labels.
- Don't log raw inputs / outputs.
- Don't create one-off ad-hoc loggers.
- Don't bypass `BaseAgent` and lose free instrumentation.
