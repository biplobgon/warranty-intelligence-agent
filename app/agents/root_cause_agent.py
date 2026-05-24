"""Root Cause Analysis Agent.

Reasons over warranty claims, telemetry, and technical document evidence to
generate ranked root-cause hypotheses with supporting evidence.
"""

from __future__ import annotations

import json
from typing import Any

from app.agents.base import BaseAgent
from app.prompts import get_prompt
from app.services.llm_provider import get_llm_provider
from app.utils.logging import get_logger

log = get_logger(__name__)


class RootCauseAgent(BaseAgent):
    name = "root_cause"

    def __init__(self) -> None:
        self._llm = get_llm_provider()
        self._prompt = get_prompt("root_cause")

    async def _execute(
        self,
        *,
        issue: str,
        component: str | None = None,
        history: list[dict[str, Any]] | None = None,
        evidence: list[str] | None = None,
        **_: Any,
    ) -> dict[str, Any]:
        rendered = self._prompt.render(
            issue=issue,
            component=component or "unspecified",
            history=json.dumps(history or [])[:4000],
            evidence="\n---\n".join((evidence or [])[:8])[:6000],
        )
        resp = await self._llm.complete(
            rendered, system=self._prompt.system, temperature=0.2, max_tokens=900
        )
        hypotheses = _parse_hypotheses(resp.text)
        return {
            "hypotheses": hypotheses,
            "raw": resp.text,
            "model": resp.model,
            "tokens_prompt": resp.tokens_prompt,
            "tokens_completion": resp.tokens_completion,
        }


def _parse_hypotheses(text: str) -> list[dict[str, Any]]:
    """Tolerant JSON extraction with safe fallback."""
    text = text.strip()
    # Strip common markdown code fences.
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
        text = text.strip()
    try:
        data = json.loads(text)
        if isinstance(data, list):
            return [_coerce(h) for h in data]
        if isinstance(data, dict) and "hypotheses" in data:
            return [_coerce(h) for h in data["hypotheses"]]
    except json.JSONDecodeError:
        pass
    log.warning("root_cause_json_parse_failed_returning_inconclusive")
    return [
        {
            "cause": "Inconclusive — model response could not be parsed.",
            "probability": 0.0,
            "evidence": [],
            "recommended_actions": ["Collect additional diagnostic data and re-run analysis."],
        }
    ]


def _coerce(h: Any) -> dict[str, Any]:
    if not isinstance(h, dict):
        return {"cause": str(h), "probability": 0.0, "evidence": [], "recommended_actions": []}
    return {
        "cause": str(h.get("cause", "unknown"))[:300],
        "probability": float(h.get("probability", 0.0) or 0.0),
        "evidence": list(h.get("evidence") or [])[:10],
        "recommended_actions": list(h.get("recommended_actions") or [])[:10],
    }
