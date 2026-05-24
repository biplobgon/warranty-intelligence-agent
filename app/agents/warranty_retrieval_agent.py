"""Warranty Retrieval Agent.

Retrieves the most relevant warranty claims from the claims vector index using
hybrid (dense+sparse) retrieval and metadata filters (component, VIN, date).
"""

from __future__ import annotations

from typing import Any

from app.agents.base import BaseAgent
from app.config import get_settings
from app.rag.retriever import HybridRetriever


class WarrantyRetrievalAgent(BaseAgent):
    name = "warranty_retrieval"

    def __init__(self) -> None:
        settings = get_settings()
        self._retriever = HybridRetriever(settings.pinecone_index_warranty)

    async def _execute(
        self,
        *,
        query: str,
        top_k: int = 8,
        component: str | None = None,
        vin: str | None = None,
        **_: Any,
    ) -> dict[str, Any]:
        filters: dict[str, Any] = {}
        if component:
            filters["component"] = component
        if vin:
            filters["vin"] = vin
        hits = await self._retriever.retrieve(query, top_k=top_k, filters=filters or None)
        return {
            "claims": [
                {
                    "id": h.id,
                    "score": h.score,
                    "text": h.text,
                    "source": h.source,
                    "metadata": h.metadata,
                }
                for h in hits
            ],
            "count": len(hits),
        }
