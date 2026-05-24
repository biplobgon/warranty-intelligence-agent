import pytest

from app.rag.chunker import chunk_text


@pytest.mark.unit
def test_chunk_text_basic():
    text = "Sentence one. Sentence two. " * 200
    chunks = chunk_text(text, chunk_size=80, overlap=10)
    assert len(chunks) > 1
    assert all(c.text for c in chunks)
    assert all(c.metadata["chunk_index"] == i for i, c in enumerate(chunks))


@pytest.mark.unit
def test_chunk_text_empty():
    assert chunk_text("") == []
    assert chunk_text("   ") == []


@pytest.mark.unit
def test_chunk_text_short_returns_single():
    text = "A short paragraph that fits in one chunk."
    chunks = chunk_text(text, chunk_size=500, overlap=20)
    assert len(chunks) == 1
    assert chunks[0].text == text
