"""FastAPI application entry point.

Wire-up:
    1. Configure structured logging
    2. Setup OpenTelemetry tracing
    3. Mount Prometheus instrumentation
    4. Register middleware (CORS, request-context)
    5. Register API routers
    6. Wire global exception handlers
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.middleware import RequestContextMiddleware
from app.api.routes import analyze, evaluate, governance, health, query, retrieve, summarize, trace
from app.api.schemas import ErrorResponse
from app.config import get_settings
from app.observability import setup_metrics, setup_tracing
from app.utils.logging import configure_logging, get_logger

log = get_logger(__name__)


@asynccontextmanager
async def _lifespan(app: FastAPI):  # type: ignore[no-untyped-def]
    settings = get_settings()
    configure_logging()
    setup_tracing(app)
    log.info(
        "app_starting",
        env=settings.app_env,
        version=settings.app_version,
        provider=settings.llm_provider,
        vector_backend=settings.vector_backend,
    )
    yield
    log.info("app_shutting_down")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Warranty Intelligence Agent Platform",
        description=(
            "Enterprise multi-agent AI system for warranty analytics, root-cause "
            "analysis, technical document intelligence, executive insight, and "
            "AI-assisted decision support."
        ),
        version=settings.app_version,
        default_response_class=ORJSONResponse,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=_lifespan,
        contact={"name": "Warranty Intelligence Platform Team"},
        license_info={"name": "MIT"},
    )

    # ---- Middleware ----
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["x-request-id"],
    )
    app.add_middleware(RequestContextMiddleware)

    # ---- Metrics (also mounts /metrics) ----
    setup_metrics(app)

    # ---- Routers ----
    app.include_router(health.router)
    app.include_router(query.router)
    app.include_router(retrieve.router)
    app.include_router(analyze.router)
    app.include_router(summarize.router)
    app.include_router(evaluate.router)
    app.include_router(governance.router)
    app.include_router(trace.router)

    # ---- Exception handlers ----
    @app.exception_handler(StarletteHTTPException)
    async def http_exc_handler(request: Request, exc: StarletteHTTPException):  # type: ignore[no-untyped-def]
        log.warning("http_exception", status=exc.status_code, detail=str(exc.detail))
        body = ErrorResponse(
            error="http_error",
            detail=str(exc.detail),
            request_id=request.headers.get("x-request-id"),
        )
        return ORJSONResponse(status_code=exc.status_code, content=body.model_dump())

    @app.exception_handler(RequestValidationError)
    async def validation_exc_handler(request: Request, exc: RequestValidationError):  # type: ignore[no-untyped-def]
        log.warning("validation_error", errors=exc.errors())
        body = ErrorResponse(
            error="validation_error",
            detail="Request validation failed.",
            request_id=request.headers.get("x-request-id"),
            context={"errors": exc.errors()},
        )
        return ORJSONResponse(status_code=422, content=body.model_dump())

    @app.exception_handler(Exception)
    async def unhandled_exc_handler(request: Request, exc: Exception):  # type: ignore[no-untyped-def]
        log.exception("unhandled_exception", error=str(exc))
        body = ErrorResponse(
            error="internal_error",
            detail="An unexpected error occurred.",
            request_id=request.headers.get("x-request-id"),
        )
        return ORJSONResponse(status_code=500, content=body.model_dump())

    @app.get("/", include_in_schema=False)
    async def root() -> dict[str, str]:
        return {
            "name": settings.app_name,
            "version": settings.app_version,
            "docs": "/docs",
            "health": "/health",
            "metrics": "/metrics",
        }

    return app


app = create_app()
