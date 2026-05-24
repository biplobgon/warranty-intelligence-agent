"""Per-request context: request_id, structured logger binding, timing."""

from __future__ import annotations

import time

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.observability.metrics import INFLIGHT_REQUESTS, REQUEST_DURATION
from app.utils.ids import new_request_id


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Binds a per-request `request_id` to structlog context vars,
    records duration metrics, and propagates the ID via a response header.
    """

    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[no-untyped-def]
        request_id = request.headers.get("x-request-id") or new_request_id()
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            path=request.url.path,
            method=request.method,
        )
        started = time.perf_counter()
        route = request.url.path
        outcome = "success"
        INFLIGHT_REQUESTS.inc()
        try:
            response = await call_next(request)
            if response.status_code >= 500:
                outcome = "server_error"
            elif response.status_code >= 400:
                outcome = "client_error"
            response.headers["x-request-id"] = request_id
            return response
        except Exception:
            outcome = "exception"
            raise
        finally:
            INFLIGHT_REQUESTS.dec()
            duration = time.perf_counter() - started
            REQUEST_DURATION.labels(route=route, outcome=outcome).observe(duration)
