"""Shared pytest fixtures.

Importantly, fixtures here:
* point all clients to in-memory / dev backends,
* monkey-patch the LLM provider with a deterministic fake,
* expose a FastAPI TestClient for integration tests.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# ---- Set safe defaults BEFORE importing app modules ----
os.environ.setdefault("APP_ENV", "development")
os.environ.setdefault("LLM_PROVIDER", "openai")
os.environ.setdefault("OPENAI_API_KEY", "")
os.environ.setdefault("VECTOR_BACKEND", "faiss")
os.environ.setdefault("PINECONE_API_KEY", "")
os.environ.setdefault("ENABLE_GUARDRAILS", "true")
os.environ.setdefault("ENABLE_PII_REDACTION", "true")


@pytest.fixture(autouse=True)
def _reset_singletons(monkeypatch):
    """Reset cached singletons between tests for isolation."""
    from app.config import settings as settings_mod
    from app.rag import pipeline as rag_mod
    from app.services import llm_provider as llm_mod
    from app.services import vector_store as vs_mod
    from app.workflows import warranty_graph as wg_mod

    settings_mod.get_settings.cache_clear()  # type: ignore[attr-defined]
    llm_mod.reset_llm_provider()
    vs_mod.reset_vector_store()
    rag_mod.reset_rag_pipeline()
    wg_mod.reset_warranty_graph()
    yield
    llm_mod.reset_llm_provider()
    vs_mod.reset_vector_store()
    rag_mod.reset_rag_pipeline()
    wg_mod.reset_warranty_graph()


class _FakeLLM:
    """Deterministic, dependency-free LLM stand-in for unit tests."""

    name = "fake"
    model = "fake-1"
    embed_model = "fake-embed"

    async def complete(self, prompt, *, system=None, temperature=0.2, max_tokens=1024, **kw):  # type: ignore[no-untyped-def]
        from app.services.llm_provider import LLMResponse

        text = f"[fake-answer] tokens_in={len(prompt.split())}"
        if system and "JSON" in (system + " " + prompt):
            text = (
                '[{"cause":"premature wear","probability":0.7,'
                '"evidence":["claim CLM-1"],"recommended_actions":["replace component"]}]'
            )
        return LLMResponse(text=text, model=self.model, tokens_prompt=10, tokens_completion=20)

    async def embed(self, texts):  # type: ignore[no-untyped-def]
        # deterministic 8-dim vectors based on text length / first chars
        out: list[list[float]] = []
        for t in texts:
            v = [0.0] * 8
            for i, ch in enumerate((t or "x")[:8]):
                v[i] = (ord(ch) % 31) / 31.0
            out.append(v)
        return out


@pytest.fixture
def fake_llm(monkeypatch):
    from app.services import llm_provider as llm_mod

    fake = _FakeLLM()
    monkeypatch.setattr(llm_mod, "get_llm_provider", lambda: fake)
    # Force any modules that already imported the symbol to pick up the fake too.
    for mod_name in (
        "app.embeddings.embedder",
        "app.rag.pipeline",
        "app.agents.root_cause_agent",
        "app.agents.executive_summary_agent",
        "app.agents.recommendation_agent",
        "app.agents.document_rag_agent",
        "app.inference.engine",
    ):
        mod = sys.modules.get(mod_name)
        if mod and hasattr(mod, "get_llm_provider"):
            monkeypatch.setattr(mod, "get_llm_provider", lambda: fake, raising=False)
    return fake


@pytest.fixture
def api_client(fake_llm):
    from fastapi.testclient import TestClient

    from app.main import create_app

    app = create_app()
    with TestClient(app) as client:
        yield client
