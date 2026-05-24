import pytest

from app.services.vector_store import InMemoryVectorStore, VectorRecord


@pytest.mark.unit
async def test_in_memory_vector_store_query():
    store = InMemoryVectorStore()
    await store.upsert(
        "test",
        [
            VectorRecord(id="a", values=[1.0, 0.0, 0.0], metadata={"text": "alpha"}),
            VectorRecord(id="b", values=[0.0, 1.0, 0.0], metadata={"text": "beta"}),
            VectorRecord(id="c", values=[0.0, 0.0, 1.0], metadata={"text": "gamma"}),
        ],
    )
    hits = await store.query("test", vector=[1.0, 0.0, 0.0], top_k=2)
    assert len(hits) == 2
    assert hits[0].id == "a"


@pytest.mark.unit
async def test_in_memory_vector_store_filters():
    store = InMemoryVectorStore()
    await store.upsert(
        "test",
        [
            VectorRecord(id="a", values=[1.0, 0.0], metadata={"text": "alpha", "kind": "x"}),
            VectorRecord(id="b", values=[1.0, 0.0], metadata={"text": "beta", "kind": "y"}),
        ],
    )
    hits = await store.query("test", vector=[1.0, 0.0], top_k=5, filters={"kind": "y"})
    assert [h.id for h in hits] == ["b"]
