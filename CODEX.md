# CODEX.md — Codex / GPT coding-agent memory (compact)

> **Read `REPO_STATE.md` first.** Do not duplicate repo state here.

## Project one-liner

Enterprise multi-agent AI platform for warranty intelligence. Production-grade. See `README.md` (pitch), `REPO_STATE.md` (state), `CHANGELOG.md` (last changes).

## Bootstrap reading order

1. `REPO_STATE.md`
2. `CHANGELOG.md` `[Unreleased]`
3. Target module under `app/<module>/` + matching `tests/`

Do NOT read the whole repo. Use `grep`/`glob`.

## Codex sweet spot

- Implementing a clear spec (schema → service → route → test) in one shot
- Tightening prompts in `app/prompts/registry.py` (bump `version`!)
- Writing/raising unit-test coverage from a function signature
- Generating type stubs / Pydantic models

## Hard constraints (also in REPO_STATE §11)

- No `print()`; structlog via `get_logger(__name__)`.
- No naked `except`; log structured + bump metric + return typed error.
- Pydantic v2 only. `model_dump()`, `model_config`.
- LLM access through `app/services/llm_provider.py` only.
- Tests must pass offline (no API keys); use `fake_llm` fixture.
- New runtime dep ⇒ update `requirements.txt` AND `pyproject.toml`.

## Canonical patterns

```python
from app.utils.logging import get_logger
log = get_logger(__name__)

try:
    result = await call_external()
except SpecificError as exc:
    log.warning("op_failed", op="ingest", error=str(exc))
    METRIC.labels(reason="external").inc()
    return _fallback()
```

```python
# Metrics: warranty_<domain>_<unit>{labels}
from prometheus_client import Histogram
H = Histogram(
    "warranty_widget_duration_seconds",
    "Widget op duration.",
    ["widget"],
    buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
)
```

## Commit message convention

Conventional Commits. Scope = module.

```
feat(rag): add cross-encoder reranker behind FEATURE_RERANKER flag
fix(api): return 422 envelope from validation errors
perf(inference): batch embeddings to 64 within 20 ms window
docs(report): expand evaluation section
test(governance): cover prompt injection edge cases
```

## Per-session workflow

1. `git pull --rebase`
2. Read `REPO_STATE.md` + `CHANGELOG.md`.
3. Read ONLY target module + tests.
4. Edit (smallest diff).
5. `make lint && make test`.
6. Update `REPO_STATE.md` (changed sections only) + `CHANGELOG.md`.
7. Commit.

## Token discipline

- Don't restate architecture in answers — point to file paths.
- Don't expand multi-file diffs unless the user asks.
- Prefer one focused tool call over many speculative ones.
