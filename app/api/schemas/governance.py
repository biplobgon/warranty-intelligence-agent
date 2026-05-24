"""Governance / policy reporting schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class GovernanceReport(BaseModel):
    blocked: bool
    reasons: list[str] = Field(default_factory=list)
    pii_findings: list[dict[str, Any]] = Field(default_factory=list)
    policy_version: str = "1.0.0"
    redacted_text: str | None = None
