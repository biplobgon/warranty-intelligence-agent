"""OpenTelemetry tracing setup.

Exports OTLP spans to a collector (e.g. otel-collector → Tempo/Jaeger/Cloud Trace).
Instruments FastAPI and HTTPX out-of-the-box.
"""

from __future__ import annotations

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from app.config import get_settings
from app.utils.logging import get_logger

log = get_logger(__name__)

_initialized = False


def setup_tracing(app=None) -> None:  # type: ignore[no-untyped-def]
    """Initialize global tracer + instrument FastAPI / HTTPX.

    Safe to call multiple times — initialization is idempotent.
    """
    global _initialized
    if _initialized:
        return

    settings = get_settings()
    resource = Resource.create(
        {
            "service.name": settings.otel_service_name,
            "service.version": settings.app_version,
            "deployment.environment": settings.app_env,
        }
    )
    provider = TracerProvider(resource=resource)

    try:
        exporter = OTLPSpanExporter(endpoint=settings.otel_exporter_otlp_endpoint, insecure=True)
        provider.add_span_processor(BatchSpanProcessor(exporter))
    except Exception as exc:  # pragma: no cover - exporter init can fail in dev
        log.warning("otel_exporter_init_failed", error=str(exc))

    trace.set_tracer_provider(provider)

    if app is not None:
        try:
            FastAPIInstrumentor.instrument_app(app)
        except Exception as exc:  # pragma: no cover
            log.warning("fastapi_instrumentation_failed", error=str(exc))

    try:
        HTTPXClientInstrumentor().instrument()
    except Exception as exc:  # pragma: no cover
        log.warning("httpx_instrumentation_failed", error=str(exc))

    _initialized = True
    log.info("tracing_initialized", endpoint=settings.otel_exporter_otlp_endpoint)


def get_tracer(name: str):  # type: ignore[no-untyped-def]
    """Return a tracer for a module/component."""
    return trace.get_tracer(name)
