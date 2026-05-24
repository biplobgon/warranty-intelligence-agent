# Skill — Governance & Guardrails

## When to load

- Tightening / loosening policy
- Adding a new banned phrase / injection pattern
- Wiring an external policy engine
- Auditing governance behavior

## Mental model

Two paths, single policy version.

```
INPUT path:  user_text → check_input → block? → continue or 4xx
OUTPUT path: llm_text  → check_output → flag? → return with governance report
```

## Key files

| File | Role |
|---|---|
| `app/governance/guardrails.py` | `Guardrails.check_input` / `check_output` |
| `app/governance/pii.py` | Presidio + regex fallback |
| `app/api/routes/governance.py` | `/governance/check`, `/governance/policy` |
| `app/api/schemas/governance.py` | `GovernanceReport` |

## Standard tasks

### 1. Add a banned output phrase

```python
# app/governance/guardrails.py
_BANNED_OUTPUT.append(re.compile(r"\bnew banned phrase\b", re.I))
```

Add a unit test in `tests/unit/test_guardrails.py`.

### 2. Add a prompt-injection pattern

```python
_INJECTION_PATTERNS.append(re.compile(r"override safety", re.I))
```

### 3. Add a PII type

If Presidio supports it: no code change needed. Otherwise extend `_regex_detect`
in `app/governance/pii.py` with a new pattern + entity type.

### 4. Block (rather than flag) hallucinations

```python
# app/governance/guardrails.py — check_output
if hallucination_score >= settings.hallucination_threshold:
    reasons.append(...)
    blocked = True   # ← currently False (flag-only)
```

⚠️ Test thoroughly — this changes API behavior. Document in `CHANGELOG.md`.

### 5. Bump policy version

```python
self.policy_version = "1.1.0"
```

Every `GovernanceReport` now carries `policy_version="1.1.0"` for audit logs.

## Hard rules

- Every governance decision MUST bump `warranty_governance_blocks_total{reason}`.
- Every `GovernanceReport` carries a `policy_version` for SIEM.
- PII detection is best-effort; never assume 100% recall. Combine with output-side
  detection as defense in depth.
- Don't disable governance in production (`ENABLE_GUARDRAILS=false` is dev-only).

## Audit checklist (for compliance)

- [ ] All policy decisions logged structurally
- [ ] All policy versions tracked in CHANGELOG
- [ ] PII regex set documented (see `docs/datasets/data_governance.md`)
- [ ] Thresholds documented in `app/config/settings.py`
- [ ] Banned phrase list reviewed quarterly
