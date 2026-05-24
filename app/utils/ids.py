"""Lightweight ID helpers (request IDs, trace IDs)."""

from __future__ import annotations

import uuid


def new_request_id() -> str:
    """Generate a short, URL-safe request identifier."""
    return uuid.uuid4().hex[:16]


def new_trace_id() -> str:
    """Generate a 128-bit trace ID compatible with OpenTelemetry."""
    return uuid.uuid4().hex
