# Changelog

All notable changes to the Warranty Intelligence Agent Platform are documented here.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this
project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- `REPO_STATE.md` — single-source-of-truth compact state file for AI agents
- `.agentignore` — workspace-indexing exclusions for OpenCode / Cursor / Copilot
- Low-Token Development Workflow section in `OPENCODE.md` (prompt-size rules,
  module-scoped reasoning, model usage strategy, tool-call discipline,
  stop conditions, end-of-session checklist)
- Reranker integration (Cohere / local cross-encoder) — planned
- MCP server exposing agents as tools — planned

### Changed
- Compressed `CLAUDE.md`, `OPENCODE.md`, `CODEX.md`, `COPILOT.md` to thin,
  agent-specific guidance that defers all state to `REPO_STATE.md`
- Tightened `.gitignore` and `.dockerignore` to exclude generated outputs,
  artifacts, embeddings caches, demo media, and notebook checkpoints
- Demo / screenshots directories now tracked via `.gitkeep` placeholders only

## [0.1.0] — 2026-05-25

Initial production-grade scaffolding of the platform.

### Added — Core platform
- FastAPI async backend with routes: `/health`, `/health/ready`, `/query`, `/retrieve`, `/analyze`, `/summarize`, `/evaluate`, `/governance/check`, `/governance/policy`, `/trace/recent`, `/metrics`
- Six-agent system: WarrantyRetrieval, DocumentRAG, RootCause, Recommendation, ExecutiveSummary, EvaluationAndGovernance
- LangGraph `StateGraph` orchestration with **graceful fallback** to a sequential async runner
- Versioned prompt registry (`app/prompts/registry.py`)
- Pydantic v2 schemas and pydantic-settings-based config
- Domain models for Vehicle / Claim / TelemetryPoint / Document
- Per-request context middleware with `x-request-id` propagation and structured logging binding

### Added — RAG
- Token-aware chunker (`tiktoken` with character fallback)
- Embedder with provider-backed (OpenAI / Vertex) embeddings + deterministic hash fallback
- Hybrid retriever: dense (Pinecone) + BM25 (in-process) with Reciprocal Rank Fusion
- End-to-end RAG pipeline (`ingest_text`, `ingest_file`, `answer`) with citations
- Grounding score + per-sentence unsupported-sentence flagging

### Added — Inference
- LLM provider abstraction with OpenAI, Vertex AI, and local (vLLM/Triton via OpenAI-compatible HTTP) implementations
- Micro-batching `InferenceBatcher` for embeddings
- Optional Ray remote execution (`app/inference/ray_runtime.py`)
- Async cache layer (Redis with in-memory fallback) wired into the engine

### Added — Observability
- Prometheus metrics tuned for LLM workloads (tokens, agent latency, retrieval latency, hallucination/grounding distributions, governance blocks, cache hit/miss)
- OpenTelemetry tracing with auto-instrumentation for FastAPI + HTTPX
- MLflow experiment tracking helpers
- structlog with JSON renderer in production, console in dev

### Added — Governance & Evaluation
- Input/output guardrails (length, prompt-injection patterns, banned phrases, hallucination + grounding thresholds)
- PII detection / redaction (Microsoft Presidio with regex fallback)
- Deterministic evaluator (hallucination, grounding, relevancy, semantic similarity)
- Evaluation endpoint + Evaluation & Governance agent

### Added — Data
- Synthetic warranty data generator (`scripts/generate_synthetic_data.py`):
  - ~10k claim records with realistic component / failure mode distribution
  - ~50k telemetry points with anomaly flags
  - 15 service / troubleshooting markdown manuals
- End-to-end ingestion pipeline (`scripts/run_ingestion.py`)
- Offline evaluation benchmark (`scripts/eval_benchmark.py`)

### Added — Infrastructure
- Multi-stage production Dockerfile (non-root, tini, healthcheck)
- docker-compose stack: API + Redis + Prometheus + Grafana + OTel Collector + MLflow
- Kubernetes manifests: namespace, configmap, secret template, deployment, service, ingress, HPA, PDB, NetworkPolicy
- Helm chart `warranty-intel` with HPA / PDB / ServiceMonitor templates
- Terraform skeleton for GKE + Artifact Registry + Workload Identity SA
- Grafana provisioning + pre-built `warranty-overview` dashboard

### Added — CI/CD & Security
- GitHub Actions: `ci.yml` (lint, type, test, evaluation, build, scan), `deploy.yml` (Helm/GKE via OIDC), `security.yml` (CodeQL, Trivy, Gitleaks)
- Trivy filesystem + image scanning
- CodeQL Python analysis

### Added — Tests
- Unit tests for chunker, grounding, PII, guardrails, evaluator, retriever (in-memory store), batcher, prompts
- Integration tests for `/health`, `/metrics`, `/openapi.json`, `/evaluate`, `/governance/*`, full workflow execution
- Evaluation marker tests (`tests/evaluation/`) that run in CI on PRs

### Added — Documentation
- Recruiter-grade `README.md` with architecture diagrams, sequence flow, full feature matrix, benchmarks, and references
- Engineering memory files: `CLAUDE.md`, `OPENCODE.md`, `CODEX.md`, `COPILOT.md`
- Technical report (`docs/reports/technical_report.md`)
- Architecture / dataset / API documentation under `docs/`
- `.claude/skills/` playbooks
- `.github/instructions/` standards
