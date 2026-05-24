"""Warranty intelligence workflow.

Pipeline (LangGraph StateGraph):

    ┌──────────────────────────┐
    │  Warranty Retrieval      │
    └─────────────┬────────────┘
                  │
                  ▼
    ┌──────────────────────────┐        ┌─────────────────────────┐
    │  Document RAG            │───────►│  Root Cause Analysis    │
    └─────────────┬────────────┘        └─────────────┬───────────┘
                  │                                   │
                  └──────────────┬────────────────────┘
                                 ▼
                ┌──────────────────────────┐
                │  Recommendation          │
                └─────────────┬────────────┘
                              ▼
                ┌──────────────────────────┐
                │  Executive Summary       │
                └─────────────┬────────────┘
                              ▼
                ┌──────────────────────────┐
                │  Evaluation & Governance │
                └──────────────────────────┘

The graph is also runnable WITHOUT langgraph installed (degrades gracefully
to a sequential async runner), which keeps the test environment minimal.
"""

from __future__ import annotations

from typing import Any, TypedDict

from app.agents import (
    DocumentRAGAgent,
    EvaluationAgent,
    ExecutiveSummaryAgent,
    RecommendationAgent,
    RootCauseAgent,
    WarrantyRetrievalAgent,
)
from app.utils.logging import get_logger

log = get_logger(__name__)


class WarrantyState(TypedDict, total=False):
    # ---- inputs ----
    query: str
    vin: str | None
    component: str | None
    persona: str
    top_k: int
    # ---- outputs ----
    claims: list[dict[str, Any]]
    rag_answer: str
    rag_contexts: list[dict[str, Any]]
    hypotheses: list[dict[str, Any]]
    actions: list[dict[str, Any]]
    executive_summary: str
    evaluation: dict[str, Any]
    governance: dict[str, Any]
    agents_invoked: list[str]
    errors: list[str]


class WarrantyGraph:
    """Multi-agent workflow with LangGraph (with graceful fallback)."""

    def __init__(self) -> None:
        self.retrieval = WarrantyRetrievalAgent()
        self.rag = DocumentRAGAgent()
        self.root_cause = RootCauseAgent()
        self.recommendation = RecommendationAgent()
        self.exec_summary = ExecutiveSummaryAgent()
        self.evaluator = EvaluationAgent()
        self._graph = self._build_graph()

    # ------------ Build ------------
    def _build_graph(self):  # type: ignore[no-untyped-def]
        try:
            from langgraph.graph import END, StateGraph

            g: StateGraph = StateGraph(WarrantyState)
            g.add_node("retrieval", self._node_retrieval)
            g.add_node("document_rag", self._node_rag)
            g.add_node("root_cause", self._node_root_cause)
            g.add_node("recommendation", self._node_recommendation)
            g.add_node("executive_summary", self._node_summary)
            g.add_node("evaluation", self._node_evaluation)

            g.set_entry_point("retrieval")
            g.add_edge("retrieval", "document_rag")
            g.add_edge("document_rag", "root_cause")
            g.add_edge("root_cause", "recommendation")
            g.add_edge("recommendation", "executive_summary")
            g.add_edge("executive_summary", "evaluation")
            g.add_edge("evaluation", END)
            return g.compile()
        except Exception as exc:
            log.warning("langgraph_unavailable_using_sequential_runner", error=str(exc))
            return None

    # ------------ Public ------------
    async def run(self, initial: dict[str, Any]) -> WarrantyState:
        state: WarrantyState = {
            "query": initial["query"],
            "vin": initial.get("vin"),
            "component": initial.get("component"),
            "persona": initial.get("persona", "engineer"),
            "top_k": int(initial.get("top_k", 6)),
            "agents_invoked": [],
            "errors": [],
        }
        if self._graph is not None:
            try:
                result: WarrantyState = await self._graph.ainvoke(state)  # type: ignore[assignment]
                return result
            except Exception as exc:
                log.exception("langgraph_execution_failed_falling_back", error=str(exc))
        return await self._run_sequential(state)

    async def _run_sequential(self, state: WarrantyState) -> WarrantyState:
        for node in (
            self._node_retrieval,
            self._node_rag,
            self._node_root_cause,
            self._node_recommendation,
            self._node_summary,
            self._node_evaluation,
        ):
            updates = await node(state)
            state.update(updates)  # type: ignore[arg-type]
        return state

    # ------------ Nodes ------------
    async def _node_retrieval(self, state: WarrantyState) -> dict[str, Any]:
        r = await self.retrieval.run(
            query=state["query"], top_k=state.get("top_k", 6),
            component=state.get("component"), vin=state.get("vin"),
        )
        return _merge(state, "warranty_retrieval", r, {"claims": (r.output or {}).get("claims", [])})

    async def _node_rag(self, state: WarrantyState) -> dict[str, Any]:
        r = await self.rag.run(query=state["query"], top_k=state.get("top_k", 6))
        out = r.output or {}
        return _merge(
            state,
            "document_rag",
            r,
            {"rag_answer": out.get("answer", ""), "rag_contexts": out.get("contexts", [])},
        )

    async def _node_root_cause(self, state: WarrantyState) -> dict[str, Any]:
        evidence = [c.get("text", "") for c in state.get("rag_contexts", [])]
        evidence += [c.get("text", "") for c in state.get("claims", [])]
        r = await self.root_cause.run(
            issue=state["query"],
            component=state.get("component"),
            history=state.get("claims", []),
            evidence=evidence,
        )
        return _merge(state, "root_cause", r, {"hypotheses": (r.output or {}).get("hypotheses", [])})

    async def _node_recommendation(self, state: WarrantyState) -> dict[str, Any]:
        evidence = [c.get("text", "") for c in state.get("rag_contexts", [])]
        r = await self.recommendation.run(
            hypotheses=state.get("hypotheses", []),
            evidence=evidence,
        )
        return _merge(state, "recommendation", r, {"actions": (r.output or {}).get("actions", [])})

    async def _node_summary(self, state: WarrantyState) -> dict[str, Any]:
        findings = [h.get("cause", "") for h in state.get("hypotheses", [])]
        metrics = {
            "claims_retrieved": float(len(state.get("claims", []))),
            "hypotheses": float(len(state.get("hypotheses", []))),
            "recommendations": float(len(state.get("actions", []))),
        }
        r = await self.exec_summary.run(
            scope="fleet",
            timeframe_days=30,
            audience=state.get("persona", "engineer"),
            findings=findings,
            metrics=metrics,
        )
        return _merge(
            state, "executive_summary", r, {"executive_summary": (r.output or {}).get("summary", "")}
        )

    async def _node_evaluation(self, state: WarrantyState) -> dict[str, Any]:
        contexts = [c.get("text", "") for c in state.get("rag_contexts", [])]
        r = await self.evaluator.run(
            question=state["query"], answer=state.get("rag_answer", ""), contexts=contexts
        )
        out = r.output or {}
        return _merge(
            state,
            "evaluation_governance",
            r,
            {"evaluation": out.get("evaluation", {}), "governance": out.get("governance", {})},
        )


def _merge(state: WarrantyState, agent: str, result: Any, payload: dict[str, Any]) -> dict[str, Any]:
    invoked = list(state.get("agents_invoked", []))
    invoked.append(agent)
    errors = list(state.get("errors", []))
    if getattr(result, "success", True) is False and getattr(result, "error", None):
        errors.append(f"{agent}: {result.error}")
    return {**payload, "agents_invoked": invoked, "errors": errors}


_graph: WarrantyGraph | None = None


def get_warranty_graph() -> WarrantyGraph:
    global _graph
    if _graph is None:
        _graph = WarrantyGraph()
    return _graph


def reset_warranty_graph() -> None:
    global _graph
    _graph = None
