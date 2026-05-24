"""Retry/backoff helpers built on Tenacity.

Centralizes retry policies so every outbound call (LLM, vector store, HTTP)
inherits the same well-tested behavior.
"""

from __future__ import annotations

from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

DEFAULT_RETRY_EXCEPTIONS: tuple[type[BaseException], ...] = (
    ConnectionError,
    TimeoutError,
)


def default_async_retry(
    max_attempts: int = 4,
    multiplier: float = 0.5,
    max_wait: float = 8.0,
    exceptions: tuple[type[BaseException], ...] = DEFAULT_RETRY_EXCEPTIONS,
) -> AsyncRetrying:
    """Return an `AsyncRetrying` instance with exponential backoff + jitter.

    Usage::

        async for attempt in default_async_retry():
            with attempt:
                result = await call_external_api()
    """
    return AsyncRetrying(
        reraise=True,
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=multiplier, max=max_wait),
        retry=retry_if_exception_type(exceptions),
    )
