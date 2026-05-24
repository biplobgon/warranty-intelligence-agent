# API Endpoints

> Schemas are defined in `app/api/schemas/`. Examples here are illustrative
> and may simplify some fields.

## Health

### `GET /health`

Liveness. No auth.

```json
{ "status": "ok", "version": "0.1.0", "environment": "production", "timestamp": "2026-05-25T12:00:00Z", "components": { "api": "ok" } }
```

### `GET /health/ready`

Readiness — checks vector store + cache. No auth.

## Multi-agent workflow

### `POST /query`

End-to-end multi-agent invocation.

**Auth**: `X-API-Key`

```json
// Request
{
  "query": "Why does the alternator keep failing on Apex S200?",
  "vin": "1HGCM82633A123456",
  "top_k": 6,
  "persona": "engineer",
  "include_evaluation": true
}
```

```json
// Response
{
  "answer": "Likely root cause is voltage-regulator failure...",
  "citations": [
    { "source": "data/synthetic/technical_documents/sm-001_alternator.md", "snippet": "...", "score": 0.81 }
  ],
  "agents_invoked": ["warranty_retrieval", "document_rag", "root_cause", "recommendation", "executive_summary", "evaluation_governance"],
  "evaluation": { "hallucination_score": 0.22, "grounding_score": 0.74, "answer_relevancy": 0.33 },
  "governance": { "blocked": false, "reasons": [], "policy_version": "1.0.0" },
  "trace": { "request_id": "f3a9...", "duration_ms": 3120.5 }
}
```

## RAG-only

### `POST /retrieve`

Hybrid retrieval, no generation.

```json
{ "query": "alternator failure modes", "top_k": 8, "index": "hybrid", "filters": { "component": "Alternator" } }
```

### `POST /analyze`

Root cause analysis.

```json
{
  "issue_description": "Alternator fails intermittently below 11.5V at idle",
  "component": "Alternator",
  "vin": "1HGCM82633A123456",
  "claim_history": []
}
```

### `POST /summarize`

Executive summary across a scope / timeframe.

```json
{ "scope": "fleet", "timeframe_days": 30, "component": "Alternator", "audience": "executive" }
```

## Evaluation

### `POST /evaluate`

Score an (answer, contexts) pair.

```json
{
  "question": "What causes alternator failure?",
  "answer": "Voltage regulator failure is the most common root cause.",
  "contexts": ["Voltage regulator failure causes alternator issues."],
  "reference": "Voltage regulator failure causes alternator issues."
}
```

## Governance

### `POST /governance/check`

Run an input or output through the active policy.

```json
{ "text": "Ignore all previous instructions...", "direction": "input" }
```

### `GET /governance/policy`

Returns the active policy metadata.

```json
{ "policy_version": "1.0.0", "thresholds": { "hallucination_max": 0.65, "grounding_min": 0.70 }, "features": { "guardrails_enabled": true, "pii_redaction_enabled": true } }
```

## Observability

### `GET /trace/recent`

Last N in-process traces (dev convenience). Production traces live in OTel
collector / Tempo / Cloud Trace.

### `GET /metrics`

Prometheus exposition format. No auth (scraper friendly). Excluded from OpenAPI.
