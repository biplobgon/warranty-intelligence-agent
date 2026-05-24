"""BaseAgent.

Common scaffolding (metrics, logging, retries) so individual agents stay focused
on their domain logic.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from app.observability.metrics import AGENT_INVOCATIONS, AGENT_LATENCY
from app.utils.logging import get_logger

log = get_logger(__name__)


@dataclass
class AgentResult:
    agent: str
    output: Any
    metadata: dict[str, Any] = field(default_factory=dict)
    success: bool = True
    error: str | None = None
    duration_ms: float = 0.0


class BaseAgent(ABC):
    """Abstract base for all platform agents."""

    name: str = "base"

    async def run(self, **inputs: Any) -> AgentResult:
        started = time.perf_counter()
        bound = log.bind(agent=self.name)
        bound.info("agent_run_start", inputs={k: _truncate(v) for k, v in inputs.items()})
        try:
            output = await self._execute(**inputs)
            duration_ms = (time.perf_counter() - started) * 1000.0
            AGENT_INVOCATIONS.labels(agent=self.name, status="success").inc()
            AGENT_LATENCY.labels(agent=self.name).observe(duration_ms / 1000.0)
            bound.info("agent_run_complete", duration_ms=duration_ms)
            return AgentResult(agent=self.name, output=output, duration_ms=duration_ms)
        except Exception as exc:
            duration_ms = (time.perf_counter() - started) * 1000.0
            AGENT_INVOCATIONS.labels(agent=self.name, status="error").inc()
            AGENT_LATENCY.labels(agent=self.name).observe(duration_ms / 1000.0)
            bound.exception("agent_run_failed", error=str(exc))
            return AgentResult(
                agent=self.name,
                output=None,
                success=False,
                error=str(exc),
                duration_ms=duration_ms,
            )

    @abstractmethod
    async def _execute(self, **inputs: Any) -> Any:  # pragma: no cover - abstract
        ...


def _truncate(value: Any, limit: int = 240) -> Any:
    if isinstance(value, str) and len(value) > limit:
        return value[:limit] + f"... <truncated {len(value) - limit}>"
    return value
