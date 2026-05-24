"""LLM provider abstraction.

Single interface (``LLMProvider``) with concrete implementations for:

* OpenAI / OpenAI-compatible (default)
* Vertex AI (Gemini)
* Local (vLLM / Triton via OpenAI-compatible HTTP)

This keeps agents and workflows decoupled from any specific vendor and makes
swapping providers a configuration change rather than a code change.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from app.config import Settings, get_settings
from app.observability.metrics import LLM_CALL_ERRORS, LLM_CALL_LATENCY, LLM_TOKEN_USAGE
from app.utils.logging import get_logger

log = get_logger(__name__)


@dataclass
class LLMResponse:
    text: str
    model: str
    tokens_prompt: int = 0
    tokens_completion: int = 0
    raw: Any | None = None


class LLMProvider(ABC):
    """Abstract LLM client."""

    name: str = "abstract"

    @abstractmethod
    async def complete(
        self,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 1024,
        **kwargs: Any,
    ) -> LLMResponse:  # pragma: no cover - abstract
        ...

    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]:  # pragma: no cover - abstract
        ...


# ---------------- OpenAI ----------------
class OpenAIProvider(LLMProvider):
    name = "openai"

    def __init__(self, settings: Settings) -> None:
        from openai import AsyncOpenAI

        self._settings = settings
        self._client = AsyncOpenAI(
            api_key=settings.openai_api_key.get_secret_value() or "sk-local-dev",
            base_url=None,
        )
        self.model = settings.openai_model
        self.embed_model = settings.openai_embed_model

    async def complete(
        self,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 1024,
        **kwargs: Any,
    ) -> LLMResponse:
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        started = time.perf_counter()
        try:
            resp = await self._client.chat.completions.create(
                model=self.model,
                messages=messages,  # type: ignore[arg-type]
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except Exception as exc:
            LLM_CALL_ERRORS.labels(model=self.model, error=type(exc).__name__).inc()
            raise
        finally:
            LLM_CALL_LATENCY.labels(model=self.model).observe(time.perf_counter() - started)

        text = resp.choices[0].message.content or ""
        prompt_tokens = getattr(resp.usage, "prompt_tokens", 0) or 0
        completion_tokens = getattr(resp.usage, "completion_tokens", 0) or 0
        LLM_TOKEN_USAGE.labels(model=self.model, kind="prompt").inc(prompt_tokens)
        LLM_TOKEN_USAGE.labels(model=self.model, kind="completion").inc(completion_tokens)
        return LLMResponse(
            text=text,
            model=self.model,
            tokens_prompt=prompt_tokens,
            tokens_completion=completion_tokens,
            raw=resp,
        )

    async def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        resp = await self._client.embeddings.create(model=self.embed_model, input=texts)
        return [d.embedding for d in resp.data]


# ---------------- Vertex AI ----------------
class VertexAIProvider(LLMProvider):
    name = "vertexai"

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self.model = settings.vertex_model

    async def complete(
        self,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 1024,
        **kwargs: Any,
    ) -> LLMResponse:
        # Lazy import: vertex SDK has heavy import-time cost.
        from vertexai.generative_models import GenerativeModel  # type: ignore

        model = GenerativeModel(self.model, system_instruction=system) if system else GenerativeModel(self.model)
        started = time.perf_counter()
        try:
            response = await model.generate_content_async(  # type: ignore[attr-defined]
                prompt,
                generation_config={
                    "temperature": temperature,
                    "max_output_tokens": max_tokens,
                },
            )
        except Exception as exc:
            LLM_CALL_ERRORS.labels(model=self.model, error=type(exc).__name__).inc()
            raise
        finally:
            LLM_CALL_LATENCY.labels(model=self.model).observe(time.perf_counter() - started)

        text = getattr(response, "text", "") or ""
        return LLMResponse(text=text, model=self.model, raw=response)

    async def embed(self, texts: list[str]) -> list[list[float]]:
        from vertexai.language_models import TextEmbeddingModel  # type: ignore

        embed_model = TextEmbeddingModel.from_pretrained("text-embedding-004")
        embeddings = embed_model.get_embeddings(texts)
        return [e.values for e in embeddings]


# ---------------- Local (vLLM / Triton via OpenAI-compatible) ----------------
class LocalOpenAICompatProvider(OpenAIProvider):
    """For self-hosted vLLM or Triton's OpenAI-compatible endpoint."""

    name = "local"

    def __init__(self, settings: Settings) -> None:
        from openai import AsyncOpenAI

        self._settings = settings
        self._client = AsyncOpenAI(
            api_key="local",
            base_url=settings.local_inference_base_url,
        )
        self.model = settings.local_inference_model
        self.embed_model = settings.openai_embed_model


# ---------------- Factory ----------------
_provider_cache: LLMProvider | None = None


def get_llm_provider() -> LLMProvider:
    """Return a cached LLM provider chosen by settings.

    The cache is process-local; in async contexts the provider is safe to share.
    """
    global _provider_cache
    if _provider_cache is not None:
        return _provider_cache

    settings = get_settings()
    if settings.llm_provider == "vertexai":
        _provider_cache = VertexAIProvider(settings)
    elif settings.llm_provider == "local":
        _provider_cache = LocalOpenAICompatProvider(settings)
    else:
        _provider_cache = OpenAIProvider(settings)
    log.info("llm_provider_initialized", provider=_provider_cache.name)
    return _provider_cache


def reset_llm_provider() -> None:
    """Reset the cached provider (used by tests)."""
    global _provider_cache
    _provider_cache = None
