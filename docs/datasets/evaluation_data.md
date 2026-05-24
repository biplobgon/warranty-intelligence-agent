# Evaluation Data

## Golden set

The canonical evaluation set lives in `scripts/eval_benchmark.py::GOLDEN_SET`.
Each entry has:

```python
{
    "query": "<user-style question>",
    "reference": "<short reference answer or key facts>",
}
```

Default set (5 cases) covers:

1. Alternator failure mode + diagnosis
2. Premature battery discharge + repair procedure
3. Infotainment touchscreen troubleshooting
4. Brake pad premature wear root cause
5. Transmission slipping + fluid leak actions

## Extending the golden set

When adding a case:

- Mirror a real production query pattern (no synthetic-only queries).
- Provide a short reference answer (1–2 sentences, key facts only).
- Keep the set size 5–20 for fast CI; bigger sets go in a nightly job.
- Diversify across components, failure modes, and personas
  (engineer / service tech / executive).

## CI gate

`pytest -m evaluation` runs `tests/evaluation/test_benchmark.py` which:

1. Runs each case through the full graph with `fake_llm` (deterministic).
2. Asserts every score is in [0, 1].
3. Does NOT assert absolute quality — that's the benchmark script's job
   against a real model.

To gate merges on absolute quality, run `scripts/eval_benchmark.py` in CI with
real API keys and add threshold assertions to the script (recommended for the
mainline release pipeline, not for every PR).

## Benchmark report

`scripts/eval_benchmark.py` prints:

```json
{
  "p50_latency_ms": 3120.5,
  "p95_latency_ms": 5860.2,
  "mean_grounding": 0.74,
  "mean_hallucination": 0.22,
  "mean_relevancy": 0.33,
  "cases": 5
}
```

These are logged to MLflow when reachable so you can plot quality / latency
over time and detect regressions visually.

## Targets (synthetic baseline)

| Metric | Target |
|---|---|
| p50 retrieval latency | < 20 ms (in-memory) / < 100 ms (Pinecone) |
| p95 `/query` end-to-end | < 6 s |
| Mean grounding | ≥ 0.70 |
| Mean hallucination | ≤ 0.30 |
| Mean relevancy (TF-IDF) | ≥ 0.25 |

## Heavier evaluation (optional)

For higher-fidelity scoring, swap or augment the deterministic evaluator with:

- **RAGAS** (`ragas`): `faithfulness`, `answer_relevancy`, `context_precision`,
  `context_recall`. Requires an LLM judge.
- **DeepEval** (`deepeval`): NLI-based faithfulness + custom assertions.
- **LangSmith**: live evaluation runs in the LangChain ecosystem.

Run these against the golden set + a sampled fraction of production traffic.
Persist results to MLflow.

## Data versioning

- The golden set is versioned with the code (it's a Python literal).
- When you change a case, add a `CHANGELOG.md` entry under `[Unreleased]`.
- For larger sets (nightly), store as JSON under `data/evaluation/` and
  version with Git LFS or DVC.
