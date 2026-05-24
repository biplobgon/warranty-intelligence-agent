import pytest

from app.workflows import get_warranty_graph


@pytest.mark.integration
async def test_warranty_graph_runs_end_to_end(fake_llm):
    graph = get_warranty_graph()
    state = await graph.run(
        {
            "query": "Why does the alternator keep failing on Apex S200?",
            "persona": "engineer",
            "top_k": 3,
        }
    )

    assert "agents_invoked" in state
    # 6 nodes expected (retrieval, rag, root_cause, recommendation, exec_summary, eval)
    assert len(state["agents_invoked"]) >= 5
    assert "rag_answer" in state
    assert "evaluation" in state
    assert "governance" in state
