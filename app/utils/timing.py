"""Timing helpers."""

from __future__ import annotations

import time
from contextlib import contextmanager
from typing import Iterator


@contextmanager
def stopwatch() -> Iterator[dict]:
    """Context manager that captures elapsed wall-clock time in ms.

    Example::

        with stopwatch() as sw:
            do_work()
        log.info("done", duration_ms=sw["elapsed_ms"])
    """
    started = time.perf_counter()
    box: dict = {"elapsed_ms": 0.0}
    try:
        yield box
    finally:
        box["elapsed_ms"] = (time.perf_counter() - started) * 1000.0
