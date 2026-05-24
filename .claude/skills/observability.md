# Skill — Observability

> Playbook for metrics, traces, and structured logs.

## When to load

- Adding a new metric
- Wiring a new external observability backend
- Debugging "why is latency high?" / "where are my traces?"

## Mental model

```
app code → structlog (json in prod) → stdout → log aggregator
        ↘ Prometheus client → /metrics → Prometheus → Grafana
        ↘ OTel SDK → OTLP gRPC → otel-collector → Tempo/Jaeger/Cloud Trace
        ↘ MLflow client (best-effort) → MLflow server
```

## Key files

| File | Role |
|---|---|
| `app/observability/metrics.py` | All Prometheus counters / histograms / gauges |
| `app/observability/tracing.py` | OTel provider + instrumentation |
| `app/observability/mlflow_tracker.py` | `start_run`, `log_metrics`, `log_params` |
| `app/utils/logging.py` | structlog configuration |
| `infrastructure/monitoring/grafana/dashboards/warranty-overview.json` | Pre-built dashboard |
| `infrastructure/monitoring/prometheus/prometheus.yml` | Scrape config |
| `infrastructure/monitoring/otel-collector.yaml` | OTel pipeline |

## Metric naming convention

```
warranty_<domain>_<unit>{label1,label2}
```

Examples:
- `warranty_request_duration_seconds{route,outcome}`
- `warranty_llm_token_usage_total{model,kind}`
- `warranty_agent_latency_seconds{agent}`

Units: `seconds`, `total` (counter), `bytes`, `score` (0..1).

## Standard tasks

### 1. Add a metric

```python
# app/observability/metrics.py
from prometheus_client import Histogram, Counter

WIDGET_DURATION = Histogram(
    "warranty_widget_duration_seconds",
    "Widget operation duration.",
    ["widget"],
    buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
)

# In code:
WIDGET_DURATION.labels(widget="resize").observe(elapsed)
```

Then add a Grafana panel referencing it (see existing dashboard JSON).

### 2. Add a trace span

```python
from app.observability.tracing import get_tracer
tracer = get_tracer(__name__)

async def my_op(x):
    with tracer.start_as_current_span("my_op", attributes={"x.size": len(x)}):
        return await do_work(x)
```

### 3. Add an MLflow run

```python
from app.observability.mlflow_tracker import start_run, log_metrics

with start_run("benchmark", tags={"component": "evaluator"}):
    log_metrics({"grounding": 0.78, "hallucination": 0.22})
```

`start_run` is a no-op context manager if MLflow is unreachable — safe to use anywhere.

### 4. Structured logging

```python
from app.utils.logging import get_logger
log = get_logger(__name__)

log.info("ingest_complete", chunks=42, index="docs", elapsed_ms=120)
log.warning("retry_after_failure", attempt=2, error=str(exc))
```

Never use `f"{var}"` interpolation in log messages — always pass key=value.

## Hard rules

- Histograms beat gauges for latency. Counters beat gauges for events.
- Label cardinality < ~10 per label. NEVER use VIN, claim_id, request_id as labels.
- Trace exporter init failures must NOT crash the app (already handled).
- `/metrics` and `/health` must remain unauthenticated (probe + scraper friendly).

## Debugging

- Hit `/metrics` and grep for the metric name to confirm it's registered.
- Check otel-collector logs (`docker logs warranty-otel`) for export errors.
- Grafana `Explore` → Prometheus → query metric name to confirm scrape.
