"""Lightweight evaluation pipeline.

Computes four standard LLM-app metrics for each (question, answer, contexts)
triple:

* hallucination_score   — 1 - lexical grounding overlap
* grounding_score       — lexical overlap between answer and contexts
* answer_relevancy      — TF-IDF cosine similarity (question vs answer)
* semantic_similarity   — TF-IDF cosine similarity (answer vs reference) — optional

For high-fidelity evaluation, swap this for RAGAS or DeepEval in the
benchmarking workflow; this module intentionally has zero external
service dependencies so it can run inside unit tests and CI.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass

from app.config import get_settings
from app.observability.metrics import GROUNDING_SCORE, HALLUCINATION_SCORE
from app.observability.mlflow_tracker import log_metrics, start_run
from app.rag.grounding import grounding_score, hallucination_score


@dataclass
class EvaluationResult:
    hallucination_score: float
    grounding_score: float
    answer_relevancy: float
    semantic_similarity: float | None
    passed_thresholds: bool
    details: dict[str, float]


_WORD_RE = re.compile(r"[A-Za-z0-9]+")


def _tf(text: str) -> Counter[str]:
    return Counter(t.lower() for t in _WORD_RE.findall(text))


def _cosine(a: Counter[str], b: Counter[str]) -> float:
    if not a or not b:
        return 0.0
    common = set(a) & set(b)
    dot = sum(a[t] * b[t] for t in common)
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


class Evaluator:
    def __init__(self) -> None:
        self._settings = get_settings()

    def evaluate(
        self,
        question: str,
        answer: str,
        contexts: list[str],
        *,
        reference: str | None = None,
        run_name: str | None = None,
    ) -> EvaluationResult:
        g = grounding_score(answer, contexts).score
        h = hallucination_score(answer, contexts)
        rel = _cosine(_tf(question), _tf(answer))
        sim = _cosine(_tf(answer), _tf(reference)) if reference else None

        HALLUCINATION_SCORE.observe(h)
        GROUNDING_SCORE.observe(g)

        passed = (
            h <= self._settings.hallucination_threshold
            and g >= self._settings.grounding_threshold
        )

        details = {
            "hallucination_score": h,
            "grounding_score": g,
            "answer_relevancy": rel,
            "unsupported_sentences": float(
                len(grounding_score(answer, contexts).unsupported_sentences)
            ),
        }
        if sim is not None:
            details["semantic_similarity"] = sim

        # Track to MLflow when a run name is supplied.
        if run_name:
            with start_run(run_name=run_name, tags={"component": "evaluator"}):
                log_metrics(details)

        return EvaluationResult(
            hallucination_score=h,
            grounding_score=g,
            answer_relevancy=rel,
            semantic_similarity=sim,
            passed_thresholds=passed,
            details=details,
        )


_evaluator: Evaluator | None = None


def get_evaluator() -> Evaluator:
    global _evaluator
    if _evaluator is None:
        _evaluator = Evaluator()
    return _evaluator
