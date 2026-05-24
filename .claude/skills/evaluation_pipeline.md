# Skill — Evaluation Pipeline

> Playbook for adding, tuning, and running AI quality evaluations.

## When to load

- Adding a new evaluation metric
- Tightening / loosening thresholds
- Wiring RAGAS or DeepEval for richer scoring
- Writing a new benchmark golden set

## Mental model

Two tiers:

1. **Always-on (deterministic, free)** — `app/evaluation/evaluator.py` runs on every response.
2. **Periodic (richer, may cost API tokens)** — `tests/evaluation/` + `scripts/eval_benchmark.py`.

## Key files

| File | Role |
|---|---|
| `app/evaluation/evaluator.py` | Deterministic metrics + MLflow integration |
| `app/rag/grounding.py` | Lexical grounding building block |
| `app/observability/metrics.py` | `HALLUCINATION_SCORE`, `GROUNDING_SCORE` |
| `scripts/eval_benchmark.py` | p50/p95 latency + mean quality report |
| `tests/evaluation/test_benchmark.py` | CI regression gate |

## Standard tasks

### 1. Add a metric

```python
# app/evaluation/evaluator.py
def evaluate(self, ...):
    ...
    jaccard = _jaccard(_tokens(question), _tokens(answer))
    details["jaccard"] = jaccard
    JACCARD_HIST.observe(jaccard)  # add to metrics.py
    ...
```

- Emit a Prometheus histogram (bucket bounds 0..1 for score-style metrics)
- Update `EvaluationResponse` schema if exposed via API
- Log to MLflow via `details`

### 2. Tune thresholds

In `app/config/settings.py`:
- `hallucination_threshold` (default 0.65) — output flagged if score ≥ this
- `grounding_threshold` (default 0.70) — output flagged if score < this

Bump these via env var (`HALLUCINATION_THRESHOLD=0.55`) — no code change.
Document the change in `CHANGELOG.md`.

### 3. Integrate RAGAS

Optional dependency already in `requirements.txt`. Use in `tests/evaluation/`
or a dedicated nightly job — NOT in `app/evaluation/evaluator.py` (must stay
deterministic and key-free).

```python
from ragas import evaluate as ragas_eval
from ragas.metrics import faithfulness, answer_relevancy
# Run only when OPENAI_API_KEY is set
```

### 4. Extend the golden set

Edit `scripts/eval_benchmark.py::GOLDEN_SET`. Each entry is `{query, reference}`.
Mirror representative production queries; keep ~5–20 entries (fast CI).

## Hard rules

- `app/evaluation/` must run with NO API keys and produce stable scores.
- Always emit metrics — silent eval = no value.
- Run `pytest -m evaluation` in CI on PRs (regression gate).
- MLflow logging is best-effort — never let it crash the pipeline.

## Interpretation cheatsheet

| Score | Interpretation |
|---|---|
| grounding ≥ 0.70 | Good — answer largely from contexts |
| grounding 0.50–0.70 | Borderline — review prompt + chunking |
| grounding < 0.50 | Bad — likely hallucination or off-topic retrieval |
| hallucination ≥ 0.65 | Flag in governance; surface to caller |
| relevancy ≥ 0.30 (TF-IDF) | Answer addresses the question |
