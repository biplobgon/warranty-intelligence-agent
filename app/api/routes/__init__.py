"""HTTP routes.

Each module exposes a :class:`fastapi.APIRouter` named ``router``.
"""

from app.api.routes import (
    analyze,
    evaluate,
    governance,
    health,
    query,
    retrieve,
    summarize,
    trace,
)

__all__ = ["analyze", "evaluate", "governance", "health", "query", "retrieve", "summarize", "trace"]
