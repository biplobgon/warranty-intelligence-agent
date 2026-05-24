"""Lightweight evaluation benchmark — runs in CI.

Deterministic: uses the fake LLM provider so we only assert pipeline plumbing
rather than absolute model quality.
"""

from __future__ import annotations

import pytest

from app.evaluation import get_evaluator
from app.workflows import get_warranty_graph

CASES = [
    {
        "query": "What causes alternator voltage regulator failure?",
        "reference": "voltage regulator failure causes alternator issues, replace assembly",
    },
    {
        "query": "Diagnose premature brake pad wear.",
        "reference": "uneven wear caused by caliper sticking, replace pads and rotors",
    },
]


@pytest.mark.evaluation
async def test_benchmark_runs(fake_llm):
    graph = get_warranty_graph()
    evaluator = get_evaluator()
    for case in CASES:
        state = await graph.run({"query": case["query"], "top_k": 3})
        contexts = [c.get("text", "") for c in state.get("rag_contexts", [])]
        ev = evaluator.evaluate(
            case["query"],
            state.get("rag_answer", ""),
            contexts,
            reference=case["reference"],
        )
        assert 0.0 <= ev.grounding_score <= 1.0
        assert 0.0 <= ev.hallucination_score <= 1.0
        assert ev.details["unsupported_sentences"] >= 0.0
