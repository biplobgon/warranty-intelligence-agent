"""MLflow experiment tracking helpers.

Tracks evaluation runs, prompt versions, and agent benchmarks.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator

try:
    import mlflow
except ImportError:  # pragma: no cover
    mlflow = None  # type: ignore[assignment]

from app.config import get_settings
from app.utils.logging import get_logger

log = get_logger(__name__)


def _configure() -> bool:
    if mlflow is None:
        return False
    settings = get_settings()
    try:
        mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
        mlflow.set_experiment(settings.mlflow_experiment)
        return True
    except Exception as exc:  # pragma: no cover
        log.warning("mlflow_configure_failed", error=str(exc))
        return False


@contextmanager
def start_run(run_name: str, tags: dict[str, str] | None = None) -> Iterator[Any]:
    """Context manager that opens an MLflow run, gracefully no-ops if disabled."""
    if not _configure():
        yield None
        return
    with mlflow.start_run(run_name=run_name, tags=tags or {}) as run:
        yield run


def log_metrics(metrics: dict[str, float]) -> None:
    if not _configure():
        return
    try:
        mlflow.log_metrics(metrics)
    except Exception as exc:  # pragma: no cover
        log.warning("mlflow_log_metrics_failed", error=str(exc))


def log_params(params: dict[str, Any]) -> None:
    if not _configure():
        return
    try:
        mlflow.log_params(params)
    except Exception as exc:  # pragma: no cover
        log.warning("mlflow_log_params_failed", error=str(exc))
