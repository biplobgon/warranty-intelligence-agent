"""Executive Summary Agent."""

from __future__ import annotations

import json
from typing import Any

from app.agents.base import BaseAgent
from app.prompts import get_prompt
from app.services.llm_provider import get_llm_provider


class ExecutiveSummaryAgent(BaseAgent):
    name = "executive_summary"

    def __init__(self) -> None:
        self._llm = get_llm_provider()
        self._prompt = get_prompt("executive_summary")

    async def _execute(
        self,
        *,
        scope: str,
        timeframe_days: int,
        audience: str,
        findings: list[str],
        metrics: dict[str, float],
        **_: Any,
    ) -> dict[str, Any]:
        rendered = self._prompt.render(
            scope=scope,
            timeframe_days=timeframe_days,
            audience=audience,
            findings="\n".join(f"- {f}" for f in findings)[:5000],
            metrics=json.dumps(metrics, indent=2)[:1500],
        )
        resp = await self._llm.complete(
            rendered, system=self._prompt.system, temperature=0.3, max_tokens=700
        )
        return {
            "summary": resp.text,
            "model": resp.model,
            "tokens_prompt": resp.tokens_prompt,
            "tokens_completion": resp.tokens_completion,
        }
