# Skill — Hallucination Detection

## When to load

- Diagnosing high `warranty_hallucination_score`
- Adding a new detection signal
- Wiring NLI / LLM-as-judge for higher fidelity

## Mental model

We use a layered approach:

1. **Layer 0 — Lexical** (always-on, deterministic): `app/rag/grounding.py`
   - Token overlap between answer and contexts
   - Per-sentence flagging (<40% overlap → unsupported)
2. **Layer 1 — Statistical** (planned): TF-IDF / BM25 similarity of answer vs contexts
3. **Layer 2 — Semantic** (planned): cross-encoder NLI on (premise=context, hypothesis=sentence)
4. **Layer 3 — LLM-as-judge** (periodic): RAGAS faithfulness / DeepEval

## Key files

| File | Role |
|---|---|
| `app/rag/grounding.py` | `grounding_score`, `hallucination_score`, unsupported-sentence flagging |
| `app/evaluation/evaluator.py` | Aggregates and emits metrics |
| `app/governance/guardrails.py` | Uses thresholds to flag (or block) outputs |
| `app/observability/metrics.py` | `HALLUCINATION_SCORE`, `GROUNDING_SCORE` histograms |

## Standard tasks

### 1. Lower hallucination scores in production

Run through this checklist BEFORE changing thresholds:

- [ ] Inspect retrieved contexts — are they relevant? (try `/retrieve` directly)
- [ ] Try a tighter prompt with explicit "do not invent" clauses
- [ ] Lower temperature (already 0.1 default for RAG)
- [ ] Increase `top_k` (6 → 8) or add a reranker
- [ ] Verify chunks aren't truncated mid-sentence
- [ ] Check `unsupported_sentences` in details — pattern? proper nouns? numbers?

### 2. Add NLI-based scoring

```python
# app/rag/nli.py  (new)
from sentence_transformers import CrossEncoder
_NLI = CrossEncoder("cross-encoder/nli-deberta-v3-base")

def nli_score(answer_sentences, contexts):
    pairs = [(ctx, sent) for ctx in contexts for sent in answer_sentences]
    scores = _NLI.predict(pairs)
    # scores: [contradiction, entailment, neutral] per pair
    return ...
```

Gate behind `FEATURE_NLI_GROUNDING` to avoid 50 MB model in slim image.

### 3. LLM-as-judge (periodic)

Implement in `scripts/eval_judge.py`. Use OpenAI / Vertex with a strict rubric.
Cache by content hash so repeated runs are cheap. Compare scores to lexical for drift.

## Hard rules

- Lexical layer MUST stay in `app/rag/grounding.py` — it's the always-on safety net.
- Heavy / model-loaded layers MUST be optional (feature-flagged).
- Hallucination score is a *signal*, not a *verdict* — combine with grounding + relevancy.
- Never silently drop unsupported_sentences; surface them in `details`.

## Score interpretation

| Hallucination | Grounding | Likely cause |
|---|---|---|
| < 0.30 | > 0.70 | Good — well-grounded answer |
| 0.30–0.65 | 0.50–0.70 | Borderline — review prompt + chunking |
| ≥ 0.65 | < 0.50 | High risk — flagged by governance; investigate retrieval quality |
| ≥ 0.65 | > 0.70 | Suspicious — likely paraphrasing without true grounding; try NLI layer |
