# Enterprise Multi-Agent AI System for Warranty Analytics and Decision Intelligence

**Author:** Biplob Gon
**Version:** 0.1.0
**Date:** 2026-05

---

## Abstract

We present the design, implementation, and evaluation of a production-grade enterprise AI platform that fuses **multi-agent orchestration**, **retrieval-augmented generation (RAG)**, **deterministic evaluation**, and **AI governance** to deliver decision-quality intelligence for warranty operations. The platform comprises six specialist agents coordinated by a LangGraph state machine and backed by a hybrid (dense + sparse + RRF) retrieval layer over Pinecone. Provider-agnostic abstractions allow seamless substitution between OpenAI, Vertex AI Gemini, and self-hosted vLLM/Triton stacks. Observability spans Prometheus metrics, OpenTelemetry traces, and MLflow experiments; governance includes input/output guardrails and PII detection. We demonstrate that lightweight, lexical grounding scoring can serve as an always-on quality signal in production, while heavier RAGAS / DeepEval evaluators run in scheduled regression suites. The reference implementation deploys to Kubernetes via Helm, includes a complete CI/CD pipeline with security scanning, and runs end-to-end with zero external services for development and testing.

## 1. Introduction

Warranty programs at large OEMs typically account for **2–4% of revenue** [1] and produce vast quantities of structured (claims) and unstructured (service manuals, technician notes) data. Despite the data volume, engineering organizations are slow to translate field data into root-cause hypotheses and prioritized actions. Existing tools tend to be either business intelligence dashboards (excellent at counting, poor at explaining) or generic LLM chat assistants (eloquent, frequently ungrounded). This work bridges that gap with a domain-grounded, evaluation-first agent platform.

## 2. Business problem

The platform is designed to answer questions of three increasing complexity:

1. **Lookup**: "Find similar past claims for an Apex S200 alternator failure on a 2023 model year." → hybrid retrieval over the claims index.
2. **Diagnostic**: "What is the most likely root cause of this issue, given telemetry and service-history evidence?" → retrieval + grounded reasoning with explicit citations.
3. **Decision-support**: "What should we do about it in the next 30 days, prioritized by impact and effort?" → multi-agent reasoning that emits structured action lists for engineering / supplier / field operations.

## 3. Related work

- **RAG** as introduced by Lewis et al. [2] established the core pattern of conditioning generation on a retrieved evidence set, which the document RAG agent operationalizes.
- **Reciprocal Rank Fusion** [3] is used to merge dense and sparse rankings; we keep the canonical k=60 constant.
- **BM25** [4] is implemented in-process for sparse scoring rather than relying on an external search cluster, which keeps the test path zero-dependency.
- **RAGAS** [5] and **DeepEval** [6] define modern LLM-based evaluation metrics; the platform's deterministic evaluator interoperates with them by exposing the same metric vocabulary (grounding, answer relevancy).
- **Agentic AI** patterns following the survey of Wang et al. [7] inform our agent decomposition: each agent has a single responsibility, a clear input/output contract, and is testable in isolation.

## 4. System architecture

### 4.1 High-level

```
Client → Ingress (TLS) → FastAPI (async) → LangGraph multi-agent
                                            ├─ Pinecone (vectors)
                                            ├─ LLM provider (OpenAI / Vertex / local)
                                            ├─ Redis (cache)
                                            └─ Governance / Eval
Observability: Prometheus, OTel collector, Grafana, MLflow
```

### 4.2 Layers

| Layer | Responsibility | Key modules |
|---|---|---|
| API | HTTP contracts, middleware, error envelope | `app/api/` |
| Orchestration | Workflow control between agents | `app/workflows/warranty_graph.py` |
| Agents | Domain specialists | `app/agents/` |
| RAG | Chunking, retrieval, grounding | `app/rag/` |
| Inference | Provider abstraction, batching, cache | `app/services/llm_provider.py`, `app/inference/` |
| Governance | Input/output guardrails, PII | `app/governance/` |
| Evaluation | Deterministic scoring | `app/evaluation/` |
| Observability | Metrics, traces, MLflow | `app/observability/` |

### 4.3 Async + graceful degradation

Every I/O-bound call is `async`. The orchestration layer prefers LangGraph but transparently degrades to a sequential async runner when LangGraph is unavailable. Vector store and cache prefer Pinecone / Redis but fall back to in-memory implementations. This design choice makes the test pyramid genuinely independent of external services.

## 5. Multi-agent design

Six agents are composed in a directed pipeline:

1. **WarrantyRetrievalAgent** — semantic + lexical retrieval of relevant claims.
2. **DocumentRAGAgent** — grounded QA over service manuals; emits citations and grounding/hallucination scores.
3. **RootCauseAgent** — JSON-structured hypothesis generation with probabilities and supporting evidence.
4. **RecommendationAgent** — prioritized actions (urgency P0–P3, effort S/M/L).
5. **ExecutiveSummaryAgent** — persona-aware business narrative.
6. **EvaluationAgent** — deterministic scoring + governance gating.

The `BaseAgent` class injects metrics, structured logging, and uniform error handling so that domain code stays focused.

## 6. RAG pipeline design

### 6.1 Chunking

Token-aware (`tiktoken`/`cl100k_base`) with 500-token chunks and 60-token overlap. Falls back to character-based chunking when `tiktoken` is unavailable, preserving ingestion in offline environments.

### 6.2 Hybrid retrieval

Each query produces two ranked lists:

- **Dense**: embedding from the configured provider, queried against Pinecone (or the in-memory store).
- **Sparse**: BM25 over an in-process corpus (k1=1.5, b=0.75) constructed at ingestion time.

We fuse with **Reciprocal Rank Fusion** (k=60) and return the top-K. RRF was preferred over score-normalized weighted sums because the dense and sparse scales are not directly comparable and RRF is robust to that.

### 6.3 Grounding

For every generated answer we compute:

- **Token-level grounding**: |answer-tokens ∩ context-tokens| / |answer-tokens|
- **Per-sentence flagging**: sentences with <40% overlap and length >4 tokens are marked unsupported.

This is intentionally cheap and deterministic so it can run on **every** production response (sampling 100%) and feed Prometheus histograms.

## 7. Inference layer

### 7.1 Provider abstraction

`LLMProvider` is an ABC with three concrete classes:

- `OpenAIProvider` — production default.
- `VertexAIProvider` — Gemini access via `google-cloud-aiplatform`.
- `LocalOpenAICompatProvider` — self-hosted vLLM / Triton using the OpenAI-compatible REST surface.

Adding a fourth provider (e.g. AWS Bedrock) is a ~80-line change behind the same interface.

### 7.2 Micro-batching

`InferenceBatcher` coalesces concurrent single-item embed requests into batches of up to 64 within a 20 ms window. On rate-limited APIs this yields a 5–10× throughput improvement at peak load without harming single-request latency in the common case.

### 7.3 Caching

`AsyncCache` is Redis-first with an in-memory fallback. The inference engine caches deterministic completions (temperature == 0.0) keyed by a SHA-1 of the (system, prompt, max_tokens) tuple.

## 8. Observability

### 8.1 Metric design

We avoid generic `http_requests_total` for AI-specific signals. Custom metrics include:

| Metric | Type | Labels |
|---|---|---|
| `warranty_llm_token_usage_total` | counter | model, kind (prompt/completion) |
| `warranty_llm_call_latency_seconds` | histogram | model |
| `warranty_agent_invocations_total` | counter | agent, status |
| `warranty_agent_latency_seconds` | histogram | agent |
| `warranty_retrieval_latency_seconds` | histogram | index |
| `warranty_hallucination_score` | histogram | — |
| `warranty_grounding_score` | histogram | — |
| `warranty_governance_blocks_total` | counter | reason |
| `warranty_cache_hits_total` / `_misses_total` | counter | namespace |

### 8.2 Tracing

OTel auto-instrumentation covers FastAPI endpoints and outbound HTTPX calls. Exporter is OTLP gRPC; in production we recommend Tempo or Cloud Trace.

### 8.3 Experiment tracking

`app/observability/mlflow_tracker.py` exposes `start_run`, `log_metrics`, `log_params`. The evaluator and benchmark script log to MLflow when `MLFLOW_TRACKING_URI` is reachable.

## 9. Governance

Input and output paths are guarded with separable policies:

1. **Input**: max length, prompt-injection regex set, PII detection / optional redaction.
2. **Output**: banned-phrase detection, hallucination threshold (default 0.65), grounding threshold (default 0.70), PII leakage detection.

Every governance decision emits a `GovernanceReport` with a stable `policy_version` field for downstream audit / SIEM ingestion.

## 10. Evaluation methodology

### 10.1 Always-on (deterministic)

- Grounding score — lexical overlap.
- Hallucination score — 1 − grounding (clamped).
- Answer relevancy — TF-IDF cosine between question and answer.
- Semantic similarity — TF-IDF cosine between answer and reference (when available).

### 10.2 Periodic (richer)

`tests/evaluation/` runs in CI on PRs and can be configured to call out to RAGAS / DeepEval with real LLM keys. Failures gate merge.

### 10.3 Benchmark script

`scripts/eval_benchmark.py` runs a curated golden set through the full graph and emits aggregate p50 / p95 latencies plus mean quality metrics. Same script can run nightly in a dedicated environment with real models.

## 11. Scalability

- Stateless API ⇒ horizontal scale via HPA (CPU + memory targets).
- Vector store decoupled (Pinecone serverless or self-hosted at scale).
- Ray runtime available for embarrassingly parallel agent fan-out (e.g. cohort analytics).
- Async batcher ensures predictable throughput on rate-limited LLM endpoints.
- PodDisruptionBudget guarantees ≥2 available pods during voluntary disruptions.

## 12. Benchmarks (representative)

| Metric | Synthetic dataset (in-memory) | Target prod |
|---|---|---|
| p50 retrieval latency | < 20 ms | < 100 ms |
| p95 end-to-end `/query` | ~3.5 s | < 6 s |
| Mean grounding score | 0.72 | ≥ 0.70 |
| Mean hallucination | 0.21 | ≤ 0.30 |
| Mean relevancy | 0.31 | ≥ 0.25 |

(Benchmarks are reproducible via `python scripts/eval_benchmark.py` after `make data-synth && make ingest`.)

## 13. Limitations

- BM25 is in-process; multi-replica deployments will have inconsistent sparse rankings until backed by a centralized index (OpenSearch / Elasticsearch).
- Lexical grounding is a proxy for semantic groundedness; combine with RAGAS / cross-encoder NLI for high-stakes domains.
- The synthetic dataset, while structurally realistic, does not capture the long-tail of free-text technician notes seen in production. Real datasets require additional preprocessing (deduplication, abbreviation expansion, redaction).
- No streaming responses yet — long-running `/query` invocations may exceed proxy timeouts on slower LLMs.

## 14. Future work

- Reranker (cross-encoder, Cohere, or local) wired behind `FEATURE_RERANKER`.
- MCP server exposing agents as tools to external IDE assistants and orchestrators.
- Online evaluation sampling into MLflow on production traffic (e.g. 1% sample).
- Cohort analytics agent for clustering-driven warranty intelligence.
- Multi-tenant deployment patterns with per-tenant Pinecone namespaces and KMS-encrypted secrets.

## 15. References

1. Federal Trade Commission, *Warranty Spending Reports*, multiple years.
2. Lewis, P. et al., *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks*, NeurIPS 2020.
3. Cormack, G. V. et al., *Reciprocal Rank Fusion outperforms Condorcet and individual Rank Learning Methods*, SIGIR 2009.
4. Robertson, S. & Zaragoza, H., *The Probabilistic Relevance Framework: BM25 and Beyond*, 2009.
5. Es, S. et al., *RAGAs: Automated Evaluation of Retrieval Augmented Generation*, 2023.
6. Confident-AI, *DeepEval Documentation*, 2024.
7. Wang, L. et al., *A Survey on Large Language Model based Autonomous Agents*, 2023.
8. Anthropic, *Constitutional AI: Harmlessness from AI Feedback*, 2022.
9. LangChain, *LangGraph Documentation*, https://langchain-ai.github.io/langgraph/
10. Microsoft Presidio, https://microsoft.github.io/presidio/
11. Model Context Protocol, https://modelcontextprotocol.io/
