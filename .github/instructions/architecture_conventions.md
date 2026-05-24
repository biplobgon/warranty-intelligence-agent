# Architecture Conventions

> The non-negotiable shape of the codebase. See `REPO_STATE.md` for current state
> and `docs/architecture/system_architecture.md` for the full diagram.

## Layers (top → bottom)

1. **API** — `app/api/` (HTTP, validation, error envelope, middleware)
2. **Orchestration** — `app/workflows/` (LangGraph + sequential fallback)
3. **Agents** — `app/agents/` (one specialist per file, `BaseAgent` base)
4. **Domain services** — `app/rag/`, `app/evaluation/`, `app/governance/`, `app/inference/`
5. **Adapters** — `app/services/` (LLM provider, vector store, cache)
6. **Cross-cutting** — `app/observability/`, `app/utils/`, `app/config/`, `app/prompts/`, `app/models/`

## Allowed dependencies (downward only)

```
API
 ↓
Orchestration
 ↓
Agents
 ↓
Domain services
 ↓
Adapters
 ↓
Cross-cutting (observability, config, utils)
```

A lower layer NEVER imports from a higher one. Cross-cutting modules may be
imported by anyone.

## Single source of truth

| Concern | File |
|---|---|
| Runtime config | `app/config/settings.py` |
| Prompts | `app/prompts/registry.py` |
| API contracts | `app/api/schemas/` |
| Repo state | `REPO_STATE.md` |
| Architectural decisions | `CLAUDE.md` (compact ADR table) |
| Engineering memory | `REPO_STATE.md` + `.claude/skills/` + this directory |

## Abstractions (frozen — extend, don't replace)

- `LLMProvider` ABC (`app/services/llm_provider.py`)
- `VectorStore` ABC (`app/services/vector_store.py`)
- `BaseAgent` (`app/agents/base.py`)
- `AsyncCache` (`app/services/cache.py`)
- `Guardrails` (`app/governance/guardrails.py`)
- `Evaluator` (`app/evaluation/evaluator.py`)
- `RAGPipeline` (`app/rag/pipeline.py`)
- `HybridRetriever` (`app/rag/retriever.py`)
- `WarrantyGraph` (`app/workflows/warranty_graph.py`)

Don't replace these without RFC + 2 approvals.

## Naming

- Modules: `snake_case`
- Classes: `PascalCase`
- Functions / vars: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Prometheus metrics: `warranty_<domain>_<unit>{labels}`
- Env vars: `UPPER_SNAKE_CASE`
- K8s resources: `warranty-<thing>` (kebab-case)

## Folder rules

- Don't create new top-level folders. Use existing.
- New module under `app/` ⇒ create `<name>/__init__.py` exporting public symbols.
- One responsibility per module. If a file exceeds ~600 LOC, split.
- Tests mirror module layout: `app/x/y.py` → `tests/unit/test_y.py` and/or
  `tests/integration/test_y_integration.py`.

## Public symbols

- Every package `__init__.py` declares `__all__` and re-exports the package's
  intended public API. Importers should NOT reach into submodules.

## Configuration

- New runtime knob ⇒ `Settings` field + env var + `.env.example` entry + docs.
- Defaults are safe for production unless explicitly marked dev-only.
- Feature flags follow the `FEATURE_<NAME>` convention.

## Observability

- New agent ⇒ uses `BaseAgent` (metrics + logging free).
- New external call ⇒ wrap with a `Histogram` for latency + `Counter` for errors.
- New decision point in governance ⇒ bump `warranty_governance_blocks_total{reason}`.

## Errors

- Domain errors: define small classes; don't reuse `ValueError`/`RuntimeError`.
- API: always go through `HTTPException` so the global handler wraps cleanly.

## Extensibility

See `CLAUDE.md` "How to extend" and the matching `.claude/skills/` playbook.
