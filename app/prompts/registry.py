"""Versioned prompt templates for each agent.

Each prompt declares: id, version, system, user_template, owner, last_updated.
Editing a prompt SHOULD also bump the version string for auditability.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PromptTemplate:
    id: str
    version: str
    system: str
    user_template: str
    owner: str = "platform-eng"

    def render(self, **kwargs: object) -> str:
        return self.user_template.format(**kwargs)


PROMPTS: dict[str, PromptTemplate] = {
    "warranty_retrieval": PromptTemplate(
        id="warranty_retrieval",
        version="2025.05.1",
        system=(
            "You are the Warranty Retrieval Agent. Given a user query and a list "
            "of retrieved warranty claim snippets, produce a concise, structured "
            "summary of the most relevant claims, grouped by failure mode. "
            "Cite claim ids in [brackets]. Never invent claims."
        ),
        user_template=(
            "User query: {query}\n\nRetrieved claims:\n{contexts}\n\n"
            "Produce a markdown summary grouped by failure mode."
        ),
    ),
    "root_cause": PromptTemplate(
        id="root_cause",
        version="2025.05.1",
        system=(
            "You are a senior reliability engineer performing root cause analysis. "
            "From the supplied evidence, propose 1-3 candidate root causes, each "
            "with a probability (0-1), supporting evidence, and recommended next "
            "actions. Respond as a JSON array. Be conservative — prefer 'inconclusive' "
            "over speculation."
        ),
        user_template=(
            "Issue description: {issue}\nComponent: {component}\n"
            "Claim history (JSON):\n{history}\n\nEvidence from documents:\n{evidence}\n\n"
            'Return JSON: [{{"cause":..., "probability":..., "evidence":[...], "recommended_actions":[...]}}]'
        ),
    ),
    "document_rag": PromptTemplate(
        id="document_rag",
        version="2025.05.1",
        system=(
            "You are the Technical Document RAG Agent. Answer ONLY from the provided "
            "service manual excerpts. If the answer is not present, say so. Always cite "
            "[doc_N] references inline."
        ),
        user_template="Question:\n{query}\n\nContext:\n{contexts}\n\nAnswer:",
    ),
    "executive_summary": PromptTemplate(
        id="executive_summary",
        version="2025.05.1",
        system=(
            "You are the Executive Summary Agent. Translate technical findings into a "
            "concise business-friendly summary for senior leadership. Include: headline "
            "finding, financial impact, recommended actions, risk level (low/med/high). "
            "Avoid jargon."
        ),
        user_template=(
            "Scope: {scope} | Timeframe: {timeframe_days} days | Audience: {audience}\n\n"
            "Findings:\n{findings}\n\nKey metrics:\n{metrics}\n\nSummary:"
        ),
    ),
    "recommendation": PromptTemplate(
        id="recommendation",
        version="2025.05.1",
        system=(
            "You are the Recommendation Agent. Given retrieved evidence and root-cause "
            "hypotheses, propose 3-5 prioritized actions. Each action must include: "
            "action, owner_role, expected_impact, urgency (P0..P3), effort (S/M/L). "
            "Return as JSON."
        ),
        user_template=(
            "Hypotheses:\n{hypotheses}\nEvidence:\n{evidence}\n\nReturn JSON list of actions."
        ),
    ),
    "governance": PromptTemplate(
        id="governance",
        version="2025.05.1",
        system=(
            "You are the Evaluation & Governance Agent. Given an answer and its "
            "retrieved contexts, judge: groundedness (0-1), factuality (0-1), and "
            "policy_compliance (true/false). Return JSON."
        ),
        user_template=(
            "Question: {query}\nAnswer: {answer}\nContexts:\n{contexts}\n\n"
            'Return JSON {{"groundedness":..,"factuality":..,"policy_compliance":..}}'
        ),
    ),
}


def get_prompt(prompt_id: str) -> PromptTemplate:
    if prompt_id not in PROMPTS:
        raise KeyError(f"Unknown prompt id: {prompt_id}")
    return PROMPTS[prompt_id]
