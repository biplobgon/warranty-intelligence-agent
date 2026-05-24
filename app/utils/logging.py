"""Structured logging using structlog.

Emits JSON logs in production for log aggregation pipelines (ELK/Loki/Cloud Logging),
and human-readable colored output in development.
"""

from __future__ import annotations

import logging
import sys
from typing import Any

import structlog

from app.config import get_settings


def configure_logging() -> None:
    """Configure structlog + stdlib logging.

    Called once at application startup.
    """
    settings = get_settings()
    level = getattr(logging, settings.log_level.upper(), logging.INFO)

    timestamper = structlog.processors.TimeStamper(fmt="iso", utc=True)
    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        timestamper,
    ]

    if settings.is_production:
        renderer: Any = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.processors.format_exc_info,
            renderer,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Route stdlib logs through the same pipeline.
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=level,
    )
    for noisy in ("uvicorn.access", "httpx", "openai", "urllib3"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Return a structlog logger bound to ``name``."""
    return structlog.get_logger(name or "app")
