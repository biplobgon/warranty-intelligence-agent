"""Grounding / faithfulness checks.

Provides a lexical-overlap based grounding score that runs cheaply on every
response.  For higher-fidelity scoring, integrate with RAGAS or DeepEval in
the evaluation pipeline.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_WORD_RE = re.compile(r"[A-Za-z0-9]+")


@dataclass
class GroundingResult:
    score: float
    matched_terms: int
    total_terms: int
    unsupported_sentences: list[str]


def _tokens(s: str) -> set[str]:
    return {t.lower() for t in _WORD_RE.findall(s)}


def grounding_score(answer: str, contexts: list[str]) -> GroundingResult:
    """Compute a lexical grounding score.

    Heuristic: fraction of content-bearing tokens in the answer that also
    appear in the union of retrieved contexts.  Sentences with <40% overlap
    are flagged as ``unsupported_sentences``.
    """
    if not answer.strip():
        return GroundingResult(score=0.0, matched_terms=0, total_terms=0, unsupported_sentences=[])

    answer_tokens = _tokens(answer)
    if not answer_tokens:
        return GroundingResult(score=0.0, matched_terms=0, total_terms=0, unsupported_sentences=[])

    context_tokens: set[str] = set()
    for c in contexts:
        context_tokens |= _tokens(c)

    matched = answer_tokens & context_tokens
    score = len(matched) / max(len(answer_tokens), 1)

    unsupported: list[str] = []
    for sentence in re.split(r"(?<=[.!?])\s+", answer):
        s_tokens = _tokens(sentence)
        if not s_tokens:
            continue
        overlap = len(s_tokens & context_tokens) / len(s_tokens)
        if overlap < 0.4 and len(s_tokens) > 4:
            unsupported.append(sentence.strip())

    return GroundingResult(
        score=score,
        matched_terms=len(matched),
        total_terms=len(answer_tokens),
        unsupported_sentences=unsupported,
    )


def hallucination_score(answer: str, contexts: list[str]) -> float:
    """1 - grounding_score, clamped to [0, 1]."""
    g = grounding_score(answer, contexts)
    return max(0.0, min(1.0, 1.0 - g.score))
