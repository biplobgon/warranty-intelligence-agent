"""Offline evaluation benchmark.

Runs a curated set of warranty-domain (question, reference) pairs through the
graph and prints aggregate quality + latency metrics.  Designed to plug into
CI for regression detection.
"""

from __future__ import annotations

import asyncio
import json
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.evaluation import get_evaluator  # noqa: E402
from app.utils.logging import configure_logging, get_logger  # noqa: E402
from app.workflows import get_warranty_graph  # noqa: E402

GOLDEN_SET = [
    {
        "query": "What is the typical failure mode of the alternator and how is it diagnosed?",
        "reference": "alternator voltage regulator failure measured with multimeter; replace assembly",
    },
    {
        "query": "Battery shows premature discharge after 12 months. What is the recommended repair procedure?",
        "reference": "battery replacement under warranty, verify terminal corrosion, perform parasitic draw test",
    },
    {
        "query": "Outline the troubleshooting steps for an unresponsive infotainment touchscreen.",
        "reference": "module software update, harness inspection, replace unit, perform module relearn",
    },
    {
        "query": "Summarize root causes for repeated brake pad premature wear across Apex S200 fleet.",
        "reference": "uneven wear caused by caliper sticking or aggressive driving, replace pads and rotors",
    },
    {
        "query": "What are the recommended actions for a transmission slipping concern with fluid leak?",
        "reference": "inspect seal, pressure test, replace transmission, perform relearn",
    },
]


async def run() -> dict[str, float]:
    configure_logging()
    log = get_logger("benchmark")
    graph = get_warranty_graph()
    evaluator = get_evaluator()

    latencies: list[float] = []
    groundings: list[float] = []
    hallucinations: list[float] = []
    relevancies: list[float] = []

    for case in GOLDEN_SET:
        started = time.perf_counter()
        state = await graph.run({"query": case["query"], "top_k": 6})
        latency = (time.perf_counter() - started) * 1000.0
        contexts = [c.get("text", "") for c in state.get("rag_contexts", [])]
        ev = evaluator.evaluate(
            case["query"],
            state.get("rag_answer", ""),
            contexts,
            reference=case["reference"],
            run_name="benchmark",
        )
        latencies.append(latency)
        groundings.append(ev.grounding_score)
        hallucinations.append(ev.hallucination_score)
        relevancies.append(ev.answer_relevancy)
        log.info(
            "benchmark_case",
            query=case["query"][:80],
            grounding=round(ev.grounding_score, 3),
            hallucination=round(ev.hallucination_score, 3),
            latency_ms=round(latency, 1),
        )

    report = {
        "p50_latency_ms": float(statistics.median(latencies)),
        "p95_latency_ms": float(_percentile(latencies, 95)),
        "mean_grounding": float(statistics.mean(groundings)),
        "mean_hallucination": float(statistics.mean(hallucinations)),
        "mean_relevancy": float(statistics.mean(relevancies)),
        "cases": len(GOLDEN_SET),
    }
    print("\n=== Benchmark Report ===")
    print(json.dumps(report, indent=2))
    return report


def _percentile(data: list[float], p: float) -> float:
    if not data:
        return 0.0
    s = sorted(data)
    k = (len(s) - 1) * (p / 100.0)
    f = int(k)
    c = min(f + 1, len(s) - 1)
    return s[f] + (s[c] - s[f]) * (k - f)


if __name__ == "__main__":
    asyncio.run(run())
