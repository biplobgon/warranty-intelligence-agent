"""Trace inspection endpoint (lightweight in-process trace cache)."""

from __future__ import annotations

from collections import deque
from datetime import datetime, timezone
from threading import Lock

from fastapi import APIRouter, Depends

from app.api.middleware.auth import require_api_key

router = APIRouter(prefix="/trace", tags=["observability"])

# Bounded in-memory trace ring (last 200 invocations).  Production should
# ship traces via OTLP to a backend like Tempo, Jaeger, or Cloud Trace.
_TRACE_RING: deque[dict] = deque(maxlen=200)
_LOCK = Lock()


def record_trace(entry: dict) -> None:
    with _LOCK:
        _TRACE_RING.append({**entry, "ts": datetime.now(timezone.utc).isoformat()})


@router.get("/recent", dependencies=[Depends(require_api_key)], summary="Recent in-process traces")
async def recent(limit: int = 50) -> dict[str, object]:
    with _LOCK:
        items = list(_TRACE_RING)[-limit:]
    return {"count": len(items), "items": items}
