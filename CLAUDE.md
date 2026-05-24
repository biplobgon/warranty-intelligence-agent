# CLAUDE.md — Claude Code memory (compact)

> **Read `REPO_STATE.md` first.** This file holds only Claude-specific guidance.
> Do NOT duplicate repo state here.

## Project one-liner

Production-grade enterprise multi-agent AI platform for warranty intelligence (retrieval, root-cause, doc RAG, exec insight, decision support). Quality bar: BlackRock / Fortune-500 applied AI.

## Bootstrap reading order (every new session)

1. `REPO_STATE.md` — current state, hard constraints, next priorities
2. `CHANGELOG.md` — last shipped changes
3. Only the module(s) you will edit (`app/<module>/`)
4. Related test file(s) under `tests/`

**Do not** read the whole repo. Use `grep`/`glob` for targeted lookups.

## North-star principles (terse)

1. Production realism over breadth.
2. Provider-agnostic (LLM, vector, cloud).
3. Deterministic evaluation in CI (no API keys required).
4. Observability is non-optional.
5. Governance by default (guardrails + PII).
6. Graceful degradation (every external dep has a fallback).
7. `app/config/settings.py` is the single source of runtime config.

## Architecture decisions (ADR pointers)

| # | Decision | Where |
|---|---|---|
| 1 | LangGraph + sequential fallback | `app/workflows/warranty_graph.py` |
| 2 | Hybrid retrieval (dense + BM25 + RRF) | `app/rag/retriever.py` |
| 3 | LLM provider ABC | `app/services/llm_provider.py` |
| 4 | In-memory vector store fallback | `app/services/vector_store.py` |
| 5 | Lexical grounding (always-on) | `app/rag/grounding.py` |
| 6 | Pydantic v2 + pydantic-settings | `app/config/settings.py` |
| 7 | structlog JSON in prod | `app/utils/logging.py` |
| 8 | Prometheus + OTel (vendor-neutral) | `app/observability/` |
| 9 | Helm chart + raw manifests | `infrastructure/{helm,kubernetes}/` |
| 10 | MIT license | `LICENSE` |

## Coding standards (terse)

- Python 3.11+, async on hot path, type hints on public APIs.
- No `print()`; use `structlog` via `get_logger(__name__)`.
- No naked `except`; catch specific, log structured, bump metric.
- Pydantic v2 (`model_dump()`, `model_config`), not v1.
- New module ⇒ unit test. New route ⇒ integration test.
- Bumping a prompt ⇒ bump `version` in `app/prompts/registry.py`.

## How to extend (1-liners)

- New agent ⇒ subclass `BaseAgent`, register node in `WarrantyGraph._build_graph`, add unit test.
- New LLM provider ⇒ subclass `LLMProvider`, wire `get_llm_provider`, add `LLM_PROVIDER=<n>` to settings.
- New eval metric ⇒ extend `Evaluator.evaluate`, emit Prometheus histogram, log to MLflow.
- New route ⇒ `app/api/routes/*.py` + schema in `app/api/schemas/` + mount in `app/main.py` + integration test.

## Per-session workflow

```
1. git pull --rebase
2. read REPO_STATE.md (always)
3. read CHANGELOG.md [Unreleased]
4. read only target module + tests
5. edit (smallest possible diff)
6. make lint && make test
7. update REPO_STATE.md (only changed sections) + CHANGELOG.md
8. commit with Conventional Commit message
```

## Multi-agent IDE continuity contract

This repo is safe for Claude Code, OpenCode, Codex, Copilot, Cursor.
Cross-agent contract:

1. Update `REPO_STATE.md` + `CHANGELOG.md` on any meaningful change.
2. Never break `/health`, `/metrics`, `/openapi.json`.
3. Never remove fallbacks (in-memory vector store, hash embeddings, regex PII).
4. Never introduce a hard dep without an offline test path.
