# Skill — Microservices Patterns

## When to load

- Splitting a module into a separate service
- Adding inter-service communication
- Designing a new sidecar / worker

## When to split

This platform is a **modular monolith** by design — splitting too early adds
operational cost without business value. Split when:

- A module needs independent scaling (e.g. embeddings worker on GPU pool)
- A module has different SLA / availability requirements
- A module has a different security boundary (multi-tenant isolation)
- A module has a different release cadence (e.g. prompts service)

Don't split because "microservices are best practice." They're not, for this size.

## Standard split patterns

### 1. Embeddings worker

Extract `app/embeddings/` + `app/inference/batcher.py` into a worker that
consumes from a queue (NATS / Redis Streams / Kafka). API publishes embed
requests and awaits results via correlation IDs.

Pros: GPU-bound work isolated; can autoscale separately.
Cons: extra hop = +5–10 ms; queue is a new failure domain.

### 2. Ingestion worker (CronJob)

Already supported via Kubernetes CronJob. Run `scripts/run_ingestion.py` on
a schedule with the same image but a different command.

### 3. Eval service

Extract `app/evaluation/` into its own service. Useful when running
expensive LLM-as-judge or RAGAS on a sampled fraction of prod traffic
without slowing the request path.

### 4. MCP server

Wrap the agents as MCP tools so other IDEs / orchestrators can invoke them.
New deployment, same image (different command). Add to `Helm values.yaml`:

```yaml
mcpServer:
  enabled: true
  image: { tag: same-as-api }
  command: ["python", "-m", "app.mcp.server"]
```

## Communication

- **Within a pod**: function calls (preferred).
- **Within the cluster**: ClusterIP services + HTTP (FastAPI ↔ FastAPI).
- **Across regions**: gRPC + mTLS (consider Istio / Linkerd if you need it).
- **Async / fan-out**: queue (NATS / Redis Streams).

## Service contract conventions

- Every service exposes `/health`, `/health/ready`, `/metrics`.
- Every service emits OTel traces with `service.name` set.
- Every service uses the same `ErrorResponse` envelope (`app/api/schemas/common.py`).
- Cross-service auth via mTLS (in-cluster) or API key (external).

## Anti-patterns

- ❌ Splitting a 200-line module into its own deployment "for cleanliness".
- ❌ Synchronous RPC chains > 3 deep.
- ❌ Sharing a database between services.
- ❌ A "shared utilities" service (couples everyone to one team's release).
