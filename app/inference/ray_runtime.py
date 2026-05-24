"""Ray runtime helpers (optional).

Enables distributed agent execution across a Ray cluster.  Import is lazy so
the rest of the platform runs fine without Ray installed at runtime.
"""

from __future__ import annotations

from typing import Any

from app.config import get_settings
from app.utils.logging import get_logger

log = get_logger(__name__)

_ray_initialized = False


def init_ray() -> bool:
    """Initialize Ray; returns True on success, False if Ray is unavailable."""
    global _ray_initialized
    if _ray_initialized:
        return True
    try:
        import ray  # type: ignore

        settings = get_settings()
        if not ray.is_initialized():
            ray.init(address=settings.ray_address, ignore_reinit_error=True, log_to_driver=False)
        _ray_initialized = True
        log.info("ray_initialized", address=settings.ray_address)
        return True
    except Exception as exc:
        log.warning("ray_init_failed", error=str(exc))
        return False


def shutdown_ray() -> None:
    global _ray_initialized
    try:
        import ray  # type: ignore

        if ray.is_initialized():
            ray.shutdown()
    except Exception:  # pragma: no cover
        pass
    _ray_initialized = False


async def remote_call(fn, *args: Any, **kwargs: Any):  # type: ignore[no-untyped-def]
    """Execute ``fn`` on Ray if available; otherwise run inline."""
    if not init_ray():
        return await fn(*args, **kwargs) if _is_coro(fn) else fn(*args, **kwargs)
    import ray  # type: ignore

    remote = ray.remote(fn)
    ref = remote.remote(*args, **kwargs)
    return ray.get(ref)


def _is_coro(fn) -> bool:  # type: ignore[no-untyped-def]
    import inspect

    return inspect.iscoroutinefunction(fn)
