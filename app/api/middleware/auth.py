"""Simple API key auth for protected routes.

For production, replace with OIDC / mTLS / service mesh auth.
"""

from __future__ import annotations

from fastapi import Header, HTTPException, status

from app.config import get_settings


async def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """FastAPI dependency that enforces ``X-API-Key`` on protected routes."""
    settings = get_settings()
    expected = settings.api_key.get_secret_value()
    if not expected or expected == "dev-local-key-change-me":
        # Permit anonymous access only in development.
        if settings.is_production:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="API key not configured in production environment.",
            )
        return
    if x_api_key != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key.",
        )
