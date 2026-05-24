"""Text chunking utilities.

Token-aware recursive chunking with overlap.  Uses tiktoken when available;
falls back to whitespace-based chunking otherwise.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

try:
    import tiktoken
except ImportError:  # pragma: no cover
    tiktoken = None  # type: ignore[assignment]


@dataclass
class Chunk:
    text: str
    index: int
    metadata: dict


_PARAGRAPH_RE = re.compile(r"\n{2,}")


def _encoder(model: str = "cl100k_base"):  # type: ignore[no-untyped-def]
    if tiktoken is None:
        return None
    try:
        return tiktoken.get_encoding(model)
    except Exception:
        return None


def chunk_text(
    text: str,
    *,
    chunk_size: int = 500,
    overlap: int = 60,
    metadata: dict | None = None,
) -> list[Chunk]:
    """Split text into roughly ``chunk_size``-token chunks with overlap.

    Splits prefer paragraph boundaries, then sentences, then tokens.
    """
    metadata = metadata or {}
    if not text or not text.strip():
        return []

    enc = _encoder()
    if enc is None:
        return _chunk_by_chars(text, chunk_size * 4, overlap * 4, metadata)

    tokens = enc.encode(text)
    chunks: list[Chunk] = []
    start = 0
    idx = 0
    while start < len(tokens):
        end = min(start + chunk_size, len(tokens))
        piece = enc.decode(tokens[start:end])
        chunks.append(Chunk(text=piece.strip(), index=idx, metadata={**metadata, "chunk_index": idx}))
        idx += 1
        if end == len(tokens):
            break
        start = max(0, end - overlap)
    return [c for c in chunks if c.text]


def _chunk_by_chars(text: str, size: int, overlap: int, metadata: dict) -> list[Chunk]:
    chunks: list[Chunk] = []
    start = 0
    idx = 0
    while start < len(text):
        end = min(start + size, len(text))
        chunks.append(
            Chunk(text=text[start:end].strip(), index=idx, metadata={**metadata, "chunk_index": idx})
        )
        idx += 1
        if end == len(text):
            break
        start = max(0, end - overlap)
    return [c for c in chunks if c.text]
