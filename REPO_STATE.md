# REPO_STATE.md — Single source of truth for repo state

> Read this file FIRST. All agent memory files (CLAUDE / OPENCODE / CODEX / COPILOT) reference it.
> Update only the section you change. Keep entries terse.

**Version:** 0.1.0 · **Last update:** 2026-05-25

## 1. Current architecture (one-liner)

FastAPI async backend → LangGraph 6-agent workflow → hybrid RAG (Pinecone+BM25+RRF) → provider-agnostic LLM (OpenAI/Vertex/local vLLM) → Prom/OTel/MLflow observability → Presidio+regex governance → K8s/Helm deploy.

## 2. Module status

| Module | State | File / Entry point |
|---|---|---|
| API routes | ✅ | `app/api/routes/{health,query,retrieve,analyze,summarize,evaluate,governance,trace}.py` |
| Agents (6) | ✅ | `app/agents/` (BaseAgent + 6 specialists) |
| Workflow | ✅ | `app/workflows/warranty_graph.py` (LangGraph + sequential fallback) |
| RAG pipeline | ✅ | `app/rag/{chunker,retriever,grounding,pipeline}.py` |
| Embeddings | ✅ | `app/embeddings/embedder.py` (+ hash fallback) |
| LLM provider | ✅ | `app/services/llm_provider.py` (OpenAI/Vertex/local) |
| Vector store | ✅ | `app/services/vector_store.py` (Pinecone + in-memory) |
| Cache | ✅ | `app/services/cache.py` (Redis + in-memory) |
| Inference | ✅ | `app/inference/{batcher,engine,ray_runtime}.py` |
| Governance | ✅ | `app/governance/{guardrails,pii}.py` |
| Evaluation | ✅ | `app/evaluation/evaluator.py` |
| Observability | ✅ | `app/observability/{metrics,tracing,mlflow_tracker}.py` |
| Prompts | ✅ | `app/prompts/registry.py` (versioned templates) |
| Config | ✅ | `app/config/settings.py` (pydantic-settings) |
| Domain models | ✅ | `app/models/domain.py` |
| Tests | ✅ | `tests/{unit,integration,evaluation}/` |
| Infra | ✅ | `Dockerfile`, `docker-compose.yml`, `infrastructure/{kubernetes,helm,terraform,monitoring}/` |
| CI/CD | ✅ | `.github/workflows/{ci,deploy,security}.yml` |
| Synthetic data | ✅ | `scripts/generate_synthetic_data.py` |
| Ingestion | ✅ | `scripts/run_ingestion.py` |
| Benchmark | ✅ | `scripts/eval_benchmark.py` |
| Docs | ✅ | `README.md`, `docs/{architecture,reports,datasets,api}/` |
| Skills/Instructions | 🟡 | `.claude/skills/`, `.github/instructions/` (stubs) |
| Demo media | ⏳ | user-captured (`docs/screenshots/`, `demos/`) |

## 3. Deployment status

- **Local**: `make docker-up` → API:8000, Prom:9090, Graf:3000, MLflow:5000
- **K8s**: raw manifests + Helm chart; HPA 3..20, PDB minAvailable=2, NetworkPolicy locked down
- **Cloud**: Terraform GKE skeleton; OIDC deploy via `deploy.yml`
- **Image**: multi-stage Dockerfile, non-root user, read-only FS, tini, healthcheck

## 4. API status (contract — do not break)

| Method | Path | Auth |
|---|---|---|
| GET  | `/health`, `/health/ready` | none |
| GET  | `/metrics`, `/openapi.json`, `/docs` | none |
| POST | `/query`, `/retrieve`, `/analyze`, `/summarize`, `/evaluate` | X-API-Key |
| POST | `/governance/check`; GET `/governance/policy` | X-API-Key |
| GET  | `/trace/recent` | X-API-Key |

## 5. RAG pipeline status

Chunker (token-aware, 500/60) → Embedder (provider + hash fallback) → Pinecone upsert + in-process BM25 → HybridRetriever (RRF k=60) → grounded prompt → LLM → `grounding_score` + `hallucination_score` on every response.

## 6. Evaluation status

Deterministic evaluator (`app/evaluation/evaluator.py`): hallucination, grounding, answer_relevancy (TF-IDF), optional semantic_similarity. Runs in `tests/evaluation/` and `scripts/eval_benchmark.py`. Logs to MLflow when reachable.

## 7. Observability status

Prom metrics: `warranty_{request_duration,llm_token_usage,llm_call_latency,agent_latency,retrieval_latency,hallucination_score,grounding_score,governance_blocks,cache_hits/misses,inflight_requests}`. OTel auto-instruments FastAPI + HTTPX. structlog JSON in prod. Grafana dashboard at `infrastructure/monitoring/grafana/dashboards/warranty-overview.json`.

## 8. Governance status

Input: length cap, prompt-injection regex, PII (Presidio + regex fallback) → block/redact. Output: banned phrases, hallucination ≥ 0.65 flag, grounding < 0.70 flag, PII leak detection. Policy version on every `GovernanceReport`.

## 9. Known blockers / tech debt

| Item | Severity |
|---|---|
| BM25 index is in-process (not HA) | medium |
| Trace ring buffer in-memory only | low |
| LLM JSON output uses tolerant parsing (no structured outputs yet) | medium |
| No streaming responses (SSE/WS) | medium |

## 10. Next priorities

1. Reranker (cross-encoder / Cohere) behind `FEATURE_RERANKER`.
2. MCP server exposing agents as tools.
3. Cohort analytics agent (claim clustering).
4. Streaming `/query` (SSE).
5. Online RAGAS/DeepEval sampling on prod traffic.

## 11. Hard constraints (do NOT break)

- `/health`, `/health/ready`, `/metrics`, `/openapi.json` contracts are frozen.
- LLM access goes through `app/services/llm_provider.py` only.
- Vector access goes through `app/services/vector_store.py` only.
- Offline test path: tests must pass with no API keys (use `fake_llm` fixture).
- pydantic v2 only (`model_dump()`, `model_config`).
- Async on the hot path; no `print()` in `app/` — use `structlog` via `get_logger`.
- Every governance decision logged + bumps `warranty_governance_blocks_total`.
- Bumping a prompt = bump its `version` in `app/prompts/registry.py`.
- New runtime dep ⇒ update both `requirements.txt` and `pyproject.toml`.

## 12. Update protocol

After any meaningful change:
1. Touch **only the affected sections** of this file.
2. Add a one-line entry to `CHANGELOG.md` under `[Unreleased]`.
3. Per-agent memory files (CLAUDE/OPENCODE/CODEX/COPILOT) point HERE — do not duplicate state.
