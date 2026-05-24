import pytest

from app.rag.grounding import grounding_score, hallucination_score


@pytest.mark.unit
def test_grounding_high_overlap():
    answer = "The alternator voltage regulator is failing and must be replaced."
    contexts = ["Diagnosing alternator voltage regulator failure requires replacement."]
    res = grounding_score(answer, contexts)
    assert res.score > 0.6
    assert hallucination_score(answer, contexts) < 0.4


@pytest.mark.unit
def test_grounding_no_overlap():
    answer = "Banana smoothies require frozen fruit and yogurt."
    contexts = ["The alternator voltage regulator failed."]
    res = grounding_score(answer, contexts)
    assert res.score < 0.2
    assert hallucination_score(answer, contexts) > 0.8


@pytest.mark.unit
def test_grounding_empty():
    res = grounding_score("", ["anything"])
    assert res.score == 0.0
