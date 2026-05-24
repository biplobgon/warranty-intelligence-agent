import pytest

from app.governance.pii import PIIScrubber


@pytest.mark.unit
def test_pii_detects_email_and_phone():
    text = "Contact John at john.doe@example.com or 555-123-4567 for warranty."
    scrubber = PIIScrubber()
    findings = scrubber.detect(text)
    kinds = {f.type for f in findings}
    assert "EMAIL" in kinds or "EMAIL_ADDRESS" in kinds
    assert any("PHONE" in k for k in kinds)


@pytest.mark.unit
def test_pii_redacts_in_place():
    text = "Email me at jane.smith@test.org for claim CLM-2025-000123."
    scrubber = PIIScrubber()
    redacted, findings = scrubber.redact(text)
    assert "jane.smith@test.org" not in redacted
    assert findings, "expected at least one PII finding"
