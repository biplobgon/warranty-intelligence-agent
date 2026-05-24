"""Input + output guardrails.

Layered checks:
1. Input policy   (prompt injection, off-topic abuse, oversized payloads)
2. Output policy  (PII leakage, hallucination threshold, policy-banned phrases)

Each check returns a structured ``GovernanceReport`` so the API can surface
the reasoning to downstream systems / auditors.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.api.schemas.governance import GovernanceReport
from app.config import get_settings
from app.governance.pii import PIIScrubber, to_dict_list
from app.observability.metrics import GOVERNANCE_BLOCKS
from app.utils.logging import get_logger

log = get_logger(__name__)


# Patterns that strongly indicate prompt-injection or jailbreak attempts.
_INJECTION_PATTERNS = [
    re.compile(r"ignore (?:all )?previous (?:instructions|rules)", re.I),
    re.compile(r"disregard (?:the )?system prompt", re.I),
    re.compile(r"reveal (?:your )?system prompt", re.I),
    re.compile(r"act as (?:dan|jailbreak)", re.I),
    re.compile(r"developer mode", re.I),
]

# Phrases that should never appear in customer-facing output.
_BANNED_OUTPUT = [
    re.compile(r"\bI am an AI language model\b", re.I),
    re.compile(r"\bas an AI\b", re.I),
]


@dataclass
class GuardrailContext:
    persona: str = "engineer"
    is_internal: bool = False
    additional_reasons: list[str] = field(default_factory=list)


class Guardrails:
    def __init__(self) -> None:
        self._settings = get_settings()
        self._pii = PIIScrubber()
        self.policy_version = "1.0.0"

    # ---------- INPUT ----------
    def check_input(self, text: str, ctx: GuardrailContext | None = None) -> GovernanceReport:
        reasons: list[str] = []
        if len(text) > 8000:
            reasons.append("input_too_long")
        if any(p.search(text) for p in _INJECTION_PATTERNS):
            reasons.append("prompt_injection_suspected")
        pii_findings = self._pii.detect(text) if self._settings.enable_pii_redaction else []
        redacted = None
        if pii_findings and self._settings.enable_pii_redaction:
            redacted, _ = self._pii.redact(text)
        blocked = "prompt_injection_suspected" in reasons or "input_too_long" in reasons
        if blocked:
            for r in reasons:
                GOVERNANCE_BLOCKS.labels(reason=r).inc()
            log.warning("input_blocked", reasons=reasons)
        return GovernanceReport(
            blocked=blocked,
            reasons=reasons,
            pii_findings=to_dict_list(pii_findings),
            policy_version=self.policy_version,
            redacted_text=redacted,
        )

    # ---------- OUTPUT ----------
    def check_output(
        self,
        text: str,
        *,
        hallucination_score: float | None = None,
        grounding_score: float | None = None,
        ctx: GuardrailContext | None = None,
    ) -> GovernanceReport:
        reasons: list[str] = []
        if not self._settings.enable_guardrails:
            return GovernanceReport(blocked=False, reasons=[], policy_version=self.policy_version)

        if hallucination_score is not None and hallucination_score >= self._settings.hallucination_threshold:
            reasons.append(f"hallucination>={self._settings.hallucination_threshold:.2f}")
        if grounding_score is not None and grounding_score < self._settings.grounding_threshold:
            reasons.append(f"grounding<{self._settings.grounding_threshold:.2f}")

        for pattern in _BANNED_OUTPUT:
            if pattern.search(text):
                reasons.append("banned_phrase")
                break

        pii_findings = self._pii.detect(text) if self._settings.enable_pii_redaction else []
        redacted = None
        if pii_findings:
            redacted, _ = self._pii.redact(text)

        # Output is *flagged* (not blocked) for hallucination — let the API decide.
        blocked = "banned_phrase" in reasons
        if blocked:
            GOVERNANCE_BLOCKS.labels(reason="banned_phrase").inc()
            log.warning("output_blocked", reasons=reasons)
        return GovernanceReport(
            blocked=blocked,
            reasons=reasons,
            pii_findings=to_dict_list(pii_findings),
            policy_version=self.policy_version,
            redacted_text=redacted,
        )


_guardrails: Guardrails | None = None


def get_guardrails() -> Guardrails:
    global _guardrails
    if _guardrails is None:
        _guardrails = Guardrails()
    return _guardrails
