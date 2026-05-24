# AI Governance Standards

> Mandatory policies for safe, auditable AI behavior in this platform.

## Scope

These standards apply to every code path that:

- Invokes an LLM (any provider)
- Returns LLM-generated content to a caller
- Stores or transmits user-supplied content
- Computes quality / safety scores

## Policy version

The current active policy version is exposed at `GET /governance/policy` and
embedded in every `GovernanceReport`. Bump the version (`Guardrails.policy_version`)
when adding / removing rules. Document changes in `CHANGELOG.md`.

## Inputs

Every user input MUST be checked via `Guardrails.check_input(text)` BEFORE
the LLM sees it. Required checks:

- **Length** — refuse inputs > 8 000 chars (configurable).
- **Prompt injection** — regex set in `app/governance/guardrails.py::_INJECTION_PATTERNS`.
- **PII detection** — Presidio if available, regex fallback otherwise.
  - When `ENABLE_PII_REDACTION=true`, redact before LLM exposure.

Blocking inputs return HTTP 400 with `{"error": "input_blocked", "reasons": [...]}`.

## Outputs

Every LLM output that leaves the platform MUST be checked via
`Guardrails.check_output(text, hallucination_score, grounding_score)`.

Required checks:

- **Banned phrases** — set in `_BANNED_OUTPUT`. Blocks the response.
- **Hallucination threshold** — `hallucination_score >= settings.hallucination_threshold`
  ⇒ FLAG (do not auto-block; surface in `GovernanceReport`).
- **Grounding threshold** — `grounding_score < settings.grounding_threshold` ⇒ FLAG.
- **Output-side PII** — detect leakage of upstream PII into LLM responses.

## Logging & metrics (mandatory)

Every governance decision MUST:

1. Bump `warranty_governance_blocks_total{reason}` (or `_flags_total` if added).
2. Emit a structured log entry with: `request_id`, `policy_version`, `reasons`,
   `pii_findings` (types only, no values).
3. Include `policy_version` in the returned `GovernanceReport`.

## Data handling

- **No persistence of raw user content** by default. If needed for evaluation /
  fine-tuning, gate behind explicit opt-in + redaction.
- **No raw PII in logs.** Log `{"type": "EMAIL", "count": 1}`, never the value.
- **No raw PII in metrics labels.** Use `reason="pii_detected"`, not `email="…"`.

## Provider behavior

- Disable provider-side logging that leaks prompts where possible
  (e.g. OpenAI `data_sharing` settings, Vertex `dataResidency`).
- Use organization-scoped API keys, not personal keys.
- Rotate keys ≥ every 90 days.

## Prompt safety

- Every prompt has a versioned entry in `app/prompts/registry.py`.
- System prompts MUST include:
  - Clear role
  - Explicit "answer only from context" / "do not invent" boundaries (for RAG)
  - Output format spec (JSON schema, citations, etc.)
- Never inject untrusted user content into the `system` field. User input goes
  into the rendered `user_template` only.

## Evaluation expectations

- Production responses are scored deterministically (grounding + hallucination)
  on EVERY call. Scores are histogrammed in Prometheus.
- Quality regression in CI gates merges (`pytest -m evaluation`).
- Periodic LLM-as-judge runs (e.g. nightly) compare against thresholds and
  emit alerts when distributions shift.

## Incident response

If a governance failure is detected in production:

1. Open an incident in the standard tracker.
2. Set `ENABLE_GUARDRAILS=true` and increase `HALLUCINATION_THRESHOLD` / lower
   `GROUNDING_THRESHOLD` temporarily via ConfigMap (no rebuild required).
3. Roll back the offending prompt version if applicable.
4. File a post-mortem within 5 business days.

## Audit

- All `GovernanceReport` events are exportable as Prometheus counters.
- Structured logs ship to the central log aggregator (Loki / ELK / Cloud Logging).
- The `policy_version` field on every report enables historical replay.
- Quarterly review of:
  - Banned phrases list
  - Injection patterns
  - PII regex coverage
  - Threshold appropriateness

## Forbidden practices

- ❌ Disabling guardrails in production (`ENABLE_GUARDRAILS=false`).
- ❌ Logging full prompts / responses to non-secured storage.
- ❌ Embedding raw PII into vector indexes.
- ❌ Returning LLM output that fails banned-phrase check.
- ❌ Removing the `policy_version` field from `GovernanceReport`.
