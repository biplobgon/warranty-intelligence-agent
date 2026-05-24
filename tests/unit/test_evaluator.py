import pytest

from app.evaluation import get_evaluator


@pytest.mark.unit
def test_evaluator_high_quality():
    ev = get_evaluator()
    result = ev.evaluate(
        question="What causes alternator failure?",
        answer="Alternator voltage regulator failure is a common root cause.",
        contexts=["Alternator voltage regulator failure is the most common root cause."],
        reference="Voltage regulator failure causes alternator issues.",
    )
    assert result.grounding_score > 0.5
    assert result.hallucination_score < 0.5
    assert result.answer_relevancy > 0.0


@pytest.mark.unit
def test_evaluator_low_quality():
    ev = get_evaluator()
    result = ev.evaluate(
        question="What causes alternator failure?",
        answer="Banana smoothies are tasty.",
        contexts=["Voltage regulator failure causes alternator issues."],
    )
    assert result.hallucination_score > 0.7
    assert result.passed_thresholds is False
