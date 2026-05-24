"""Liveness / readiness endpoints."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter

from app.api.schemas import HealthResponse
from app.config import get_settings
from app.services.cache import get_cache
from app.services.vector_store import get_vector_store

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse, summary="Liveness probe")
async def liveness() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ok",
        version=settings.app_version,
        environment=settings.app_env,
        timestamp=datetime.now(timezone.utc),
        components={"api": "ok"},
    )


@router.get("/health/ready", response_model=HealthResponse, summary="Readiness probe")
async def readiness() -> HealthResponse:
    settings = get_settings()
    components: dict[str, str] = {"api": "ok"}

    # Vector store
    try:
        get_vector_store()
        components["vector_store"] = "ok"
    except Exception as exc:
        components["vector_store"] = f"degraded:{exc.__class__.__name__}"

    # Cache (best-effort)
    try:
        cache = get_cache()
        await cache.set("health", "probe", {"t": datetime.now(timezone.utc).isoformat()}, ttl=10)
        components["cache"] = "ok"
    except Exception as exc:
        components["cache"] = f"degraded:{exc.__class__.__name__}"

    overall = "ok" if all(v == "ok" for v in components.values()) else "degraded"
    return HealthResponse(
        status=overall,
        version=settings.app_version,
        environment=settings.app_env,
        timestamp=datetime.now(timezone.utc),
        components=components,
    )
