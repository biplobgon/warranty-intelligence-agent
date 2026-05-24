# Error Handling

All errors return a uniform JSON envelope:

```json
{
  "error": "<machine-readable code>",
  "detail": "<human-readable message>",
  "request_id": "<correlation id>",
  "context": { "...optional..." }
}
```

`request_id` matches the `X-Request-Id` response header.

## Status codes

| Code | When | Notes |
|---|---|---|
| 200 | Success | Standard response |
| 400 | Input blocked by governance | Body contains `reasons[]` |
| 401 | Missing / invalid API key | |
| 404 | Unknown route | |
| 422 | Request validation failure | `context.errors` lists Pydantic errors |
| 429 | Rate-limited | Typically returned by ingress / WAF, not this app |
| 500 | Unexpected error | `request_id` is your investigation handle |
| 502 / 503 | Upstream dependency unavailable | Treat as transient |

## Standard error codes

| `error` | Meaning |
|---|---|
| `http_error` | Generic non-2xx |
| `validation_error` | Request schema invalid |
| `input_blocked` | Governance rejected the input |
| `internal_error` | Catch-all server error |

Custom modules may add more specific codes. Document new codes here.

## Retry guidance for clients

| Status | Retry? | Strategy |
|---|---|---|
| 200 / 201 | No | Success |
| 400 / 422 | No | Fix request |
| 401 / 403 | No | Fix auth |
| 404 | No | Don't retry; surface to caller |
| 408 | Yes | Backoff |
| 429 | Yes | Backoff with jitter; respect `Retry-After` if present |
| 500 | Yes (limited) | 3 retries max, exponential backoff |
| 502 / 503 / 504 | Yes | Exponential backoff with jitter |

Suggested client retry config: 3 attempts, exponential backoff with base 0.5 s
and cap 8 s, plus 0–500 ms jitter. The reference implementation in `app/utils/retry.py`
mirrors this for our outbound calls.

## Idempotency

The platform's mutating endpoints are **read-shaped** (LLM completions don't
mutate persistent state). Clients can safely retry on transient failures.

For future write endpoints (e.g. claim updates), pass `Idempotency-Key` headers
and implement deduplication on the server side.

## Investigation workflow

Given a `request_id`:

1. Search the structured log aggregator for `request_id=<id>`.
2. Pull the trace from OTel backend using `request_id` (set as span attribute).
3. Check Prometheus for `warranty_request_duration_seconds{route=...}` p95 spike.
4. Check `warranty_llm_call_errors_total` and `warranty_governance_blocks_total`
   in the relevant time window.
