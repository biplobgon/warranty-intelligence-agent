import pytest


@pytest.mark.integration
def test_evaluate_endpoint(api_client):
    resp = api_client.post(
        "/evaluate",
        json={
            "question": "What causes alternator failure?",
            "answer": "Alternator voltage regulator failure is the most common root cause.",
            "contexts": ["Alternator voltage regulator failure is the most common root cause."],
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "hallucination_score" in body
    assert "grounding_score" in body
    assert body["grounding_score"] >= 0.0
