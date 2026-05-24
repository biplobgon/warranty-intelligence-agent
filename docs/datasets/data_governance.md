# Data Governance

Mirrors and operationalizes `.github/instructions/ai_governance.md` for the
data plane specifically.

## Data classification

| Tier | Examples | Storage | Access |
|---|---|---|---|
| Public | Synthetic data, NHTSA public datasets | Repo / unrestricted bucket | Anyone |
| Internal | Real (anonymized) warranty claims | Cloud bucket (KMS) + Pinecone | Engineering only |
| Restricted | Raw VINs, customer PII, dealer notes | Encrypted store; ABAC | Need-to-know |
| Secret | API keys, signing keys | Secret manager (Vault / GCP SM / AWS SM) | Service accounts only |

## Quality validation (recommended pipeline additions)

- **Schema validation** at ingest: pandera or pydantic at the row level
- **Range checks**: `repair_cost_usd >= 0`, `mileage_km >= 0`, plausible date ranges
- **Cardinality checks**: e.g. component values in a known set
- **Duplicate detection** by `claim_id`
- **Embedding drift**: monitor mean / std of vector norms over time

## PII handling

- Detect with `app/governance/pii.py` (Presidio + regex fallback).
- Redact BEFORE upserting into a vector index. Per-token redaction is preferable
  to whole-record dropping.
- Never embed raw VINs / emails / phone numbers / SSNs unless the downstream
  use case explicitly requires re-identification and access is audited.

## Retention

| Data | Default retention | Reason |
|---|---|---|
| Raw datasets in `data/raw/` | per source license | Compliance |
| Processed parquet in `data/processed/` | 90 days unless production | Cost / hygiene |
| Vector index | indefinite while in use; rotate on schema change | Operability |
| MLflow runs | 1 year | Audit |
| Prometheus metrics | 14 days | Standard scrape retention |
| Structured logs | 30 days hot, 1 year cold | Audit |
| Traces | 7 days | Cost |

## Lineage

Capture lineage by tagging each ingested record with:

- `source`: original file path / URL
- `document_id`: stable identifier
- `chunk_index`: 0-based
- `chunk_strategy_version`: (future) version of chunking config
- `embedding_model`: provider + model name

## Right-to-be-forgotten / deletion

- Vector store: `VectorStore.delete(index, ids=[...])` — implement a lookup
  table from `subject_id` → `chunk_ids` when handling real PII.
- Logs: depend on aggregator support; structlog records carry `request_id`
  but should not carry PII (see observability standards).

## Cross-border / residency

- Pinecone offers per-region indexes — pin to your data residency requirement.
- Vertex AI region (`VERTEX_LOCATION`) controls where Gemini calls execute.
- For EU residency: prefer `europe-west*` regions and EU Pinecone tier.

## Audit trail

- Every `GovernanceReport` carries `policy_version`.
- Structured logs include `request_id`, `route`, `policy_version`, and
  governance decision reasons.
- MLflow run tags include `component`, prompt version (when relevant), and
  dataset snapshot id.

## Reviews

Quarterly review of:

- [ ] PII regex coverage (new patterns to add?)
- [ ] Banned phrase list
- [ ] Retention policy still appropriate
- [ ] Embedding model + chunk strategy still optimal
- [ ] Access control on all storage tiers
