# Rate Limits

The application layer doesn't enforce rate limits — that responsibility lives
at the edge (ingress / API gateway / WAF). This keeps the API focused and
allows org-wide rate policies to be applied uniformly.

## Recommended defaults

| Tier | RPS / client | Burst | Notes |
|---|---|---|---|
| Internal services (in-cluster) | unlimited | unlimited | Trusted, mTLS |
| Internal users | 20 | 60 | Engineers triaging issues |
| External partners | 5 | 15 | Per-API-key |
| Anonymous (none) | 0 | 0 | API key required |

## NGINX Ingress example

```yaml
metadata:
  annotations:
    nginx.ingress.kubernetes.io/limit-rps: "20"
    nginx.ingress.kubernetes.io/limit-burst-multiplier: "3"
    nginx.ingress.kubernetes.io/limit-connections: "100"
```

## Application back-pressure

The application back-pressures via:

- HPA scaling (CPU / memory)
- In-flight gauge `warranty_inflight_requests` (alert > N)
- Inference batcher merges concurrent embed calls into batches

For LLM call budgets, set per-tenant quotas in the API gateway and emit
`warranty_llm_budget_exceeded_total` from the inference engine when triggered.

## Long-running queries

The `/query` endpoint can take several seconds end-to-end. Configure proxy
timeouts to ≥ 120 s (already set in `infrastructure/kubernetes/ingress.yaml`).

For future streaming responses (SSE), proxy timeouts must accommodate idle
chunks (keep-alive every 15 s recommended).
