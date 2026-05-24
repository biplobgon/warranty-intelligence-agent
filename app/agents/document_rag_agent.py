"""Technical Document RAG Agent.

Retrieves manual / SOP / troubleshooting passages and produces a grounded
answer.  Delegates to :class:`app.rag.RAGPipeline` for the heavy lifting.
"""

from __future__ import annotations

from typing import Any

from app.agents.base import BaseAgent
from app.rag.pipeline import get_rag_pipeline


class DocumentRAGAgent(BaseAgent):
    name = "document_rag"

    def __init__(self) -> None:
        self._rag = get_rag_pipeline()

    async def _execute(
        self,
        *,
        query: str,
        top_k: int = 6,
        filters: dict[str, Any] | None = None,
        **_: Any,
    ) -> dict[str, Any]:
        result = await self._rag.answer(query, index="docs", top_k=top_k, filters=filters)
        return {
            "answer": result.answer,
            "contexts": [
                {"id": c.id, "text": c.text, "source": c.source, "score": c.score}
                for c in result.contexts
            ],
            "grounding": result.grounding,
            "hallucination": result.hallucination,
            "model": result.model,
            "tokens_prompt": result.tokens_prompt,
            "tokens_completion": result.tokens_completion,
        }
