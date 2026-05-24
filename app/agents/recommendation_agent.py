"""Recommendation Agent.

Generates prioritized engineering / operational actions based on the upstream
agents' outputs (retrieval, root cause).
"""

from __future__ import annotations

import json
from typing import Any

from app.agents.base import BaseAgent
from app.prompts import get_prompt
from app.services.llm_provider import get_llm_provider
from app.utils.logging import get_logger

log = get_logger(__name__)


class RecommendationAgent(BaseAgent):
    name = "recommendation"

    def __init__(self) -> None:
        self._llm = get_llm_provider()
        self._prompt = get_prompt("recommendation")

    async def _execute(
        self,
        *,
        hypotheses: list[dict[str, Any]],
        evidence: list[str] | None = None,
        **_: Any,
    ) -> dict[str, Any]:
        rendered = self._prompt.render(
            hypotheses=json.dumps(hypotheses, indent=2)[:4000],
            evidence="\n".join((evidence or [])[:8])[:4000],
        )
        resp = await self._llm.complete(
            rendered, system=self._prompt.system, temperature=0.2, max_tokens=700
        )
        actions = _parse_actions(resp.text)
        return {
            "actions": actions,
            "raw": resp.text,
            "model": resp.model,
            "tokens_prompt": resp.tokens_prompt,
            "tokens_completion": resp.tokens_completion,
        }


def _parse_actions(text: str) -> list[dict[str, Any]]:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
        text = text.strip()
    try:
        data = json.loads(text)
        if isinstance(data, list):
            return [_coerce(a) for a in data]
        if isinstance(data, dict) and "actions" in data:
            return [_coerce(a) for a in data["actions"]]
    except json.JSONDecodeError:
        pass
    log.warning("recommendation_json_parse_failed")
    return []


_URGENCY = {"P0", "P1", "P2", "P3"}
_EFFORT = {"S", "M", "L"}


def _coerce(a: Any) -> dict[str, Any]:
    if not isinstance(a, dict):
        return {"action": str(a), "owner_role": "engineering", "urgency": "P2", "effort": "M"}
    urgency = str(a.get("urgency", "P2")).upper()
    effort = str(a.get("effort", "M")).upper()
    return {
        "action": str(a.get("action", ""))[:300],
        "owner_role": str(a.get("owner_role", "engineering")),
        "expected_impact": str(a.get("expected_impact", ""))[:300],
        "urgency": urgency if urgency in _URGENCY else "P2",
        "effort": effort if effort in _EFFORT else "M",
    }
