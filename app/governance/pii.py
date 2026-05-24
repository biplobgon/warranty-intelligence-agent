"""PII detection and redaction.

Uses Microsoft Presidio when available; falls back to regex-based detection
so the pipeline works in lightweight test environments.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from app.utils.logging import get_logger

log = get_logger(__name__)

# Reasonable VIN regex (17 chars, no I/O/Q).
_VIN_RE = re.compile(r"\b[A-HJ-NPR-Z0-9]{17}\b")
_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
_PHONE_RE = re.compile(r"\b(?:\+?\d{1,3}[\s-]?)?(?:\(?\d{3}\)?[\s.-]?)?\d{3}[\s.-]?\d{4}\b")
_SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
_CC_RE = re.compile(r"\b(?:\d[ -]*?){13,16}\b")


@dataclass
class PIIFinding:
    type: str
    start: int
    end: int
    value: str


class PIIScrubber:
    """Detect and redact PII in text."""

    def __init__(self) -> None:
        self._presidio_analyzer = None
        self._presidio_anonymizer = None
        try:
            from presidio_analyzer import AnalyzerEngine
            from presidio_anonymizer import AnonymizerEngine

            self._presidio_analyzer = AnalyzerEngine()
            self._presidio_anonymizer = AnonymizerEngine()
            log.info("pii_scrubber_initialized", backend="presidio")
        except Exception as exc:
            log.info("pii_scrubber_initialized", backend="regex_fallback", error=str(exc))

    def detect(self, text: str) -> list[PIIFinding]:
        if self._presidio_analyzer is not None:
            try:
                results = self._presidio_analyzer.analyze(text=text, language="en")
                return [
                    PIIFinding(type=r.entity_type, start=r.start, end=r.end, value=text[r.start : r.end])
                    for r in results
                ]
            except Exception as exc:  # pragma: no cover
                log.warning("presidio_failed_using_regex", error=str(exc))
        return self._regex_detect(text)

    def redact(self, text: str) -> tuple[str, list[PIIFinding]]:
        findings = self.detect(text)
        if not findings:
            return text, []
        # Replace from end to start to keep offsets stable.
        redacted = text
        for f in sorted(findings, key=lambda x: x.start, reverse=True):
            placeholder = f"[{f.type}]"
            redacted = redacted[: f.start] + placeholder + redacted[f.end :]
        return redacted, findings

    @staticmethod
    def _regex_detect(text: str) -> list[PIIFinding]:
        findings: list[PIIFinding] = []
        for pattern, kind in (
            (_EMAIL_RE, "EMAIL"),
            (_PHONE_RE, "PHONE_NUMBER"),
            (_SSN_RE, "US_SSN"),
            (_CC_RE, "CREDIT_CARD"),
            (_VIN_RE, "VIN"),
        ):
            for m in pattern.finditer(text):
                findings.append(PIIFinding(type=kind, start=m.start(), end=m.end(), value=m.group()))
        return findings


def to_dict_list(findings: list[PIIFinding]) -> list[dict[str, Any]]:
    return [{"type": f.type, "start": f.start, "end": f.end, "value": f.value} for f in findings]
