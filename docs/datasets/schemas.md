# Canonical Schemas

The platform uses three canonical entities, modeled as Pydantic v2 classes in
`app/models/domain.py` and reflected in the synthetic CSVs.

## Claim

```python
class Claim(BaseModel):
    claim_id: str
    vin: str | None
    component: str
    failure_mode: str
    description: str
    repair_cost_usd: float       # ≥ 0
    status: Literal["open", "in_progress", "closed", "denied"]
    opened_at: datetime
    closed_at: datetime | None
    resolution: str | None
    technician_notes: str | None
    mileage_km: float | None
```

CSV columns (`data/synthetic/warranty_claims.csv`):

```
claim_id, vin, make, model, model_year, fleet_id,
component, failure_mode, description,
repair_cost_usd, status, opened_at, closed_at,
mileage_km, resolution, technician_notes
```

## Telemetry point

```python
class TelemetryPoint(BaseModel):
    vin: str
    timestamp: datetime
    metric: str                  # e.g. "battery_voltage", "engine_temp_c"
    value: float
    diagnostic_code: str | None  # OBD-II DTC if anomalous
    anomaly_flag: bool
```

CSV columns (`data/synthetic/vehicle_telemetry.csv`):

```
vin, timestamp, metric, value, diagnostic_code, anomaly_flag
```

## Document

```python
class Document(BaseModel):
    document_id: str
    title: str
    source: str
    kind: Literal["service_manual", "tsb", "sop", "troubleshooting_guide", "engineering_doc"]
    content: str
    component_tags: list[str]
    published_at: datetime | None
```

Markdown files under `data/synthetic/technical_documents/*.md` follow the
9-section template described in `synthetic_data.md`.

## Vector index metadata (Pinecone)

Per record metadata stored alongside the embedding:

### `warranty-claims` index

```jsonc
{
  "text": "<chunk text>",
  "claim_id": "CLM-2025-000123",
  "vin": "1HGCM82633A123456",
  "component": "Alternator",
  "failure_mode": "voltage regulator failure",
  "make": "Apex",
  "model": "Apex S200",
  "status": "closed",
  "repair_cost_usd": 412.50,
  "chunk_index": 0
}
```

### `technical-docs` index

```jsonc
{
  "text": "<chunk text>",
  "source": "data/synthetic/technical_documents/sm-001_alternator.md",
  "filename": "sm-001_alternator.md",
  "document_id": "sm-001_alternator",
  "chunk_index": 3
}
```

## Filter conventions

When calling `/retrieve` or agent-level retrieval, pass exact-match filters:

```jsonc
{ "component": "Alternator", "status": "closed" }
```

Range / fuzzy filters require a vector store that supports them (Pinecone v2+).
Don't rely on free-text in metadata for ranking; use the BM25 path instead.

## Stability guarantees

- Schemas in `app/models/domain.py` are public contracts. Field renames are
  breaking changes and require a `BREAKING CHANGE` footer in the commit.
- Adding optional fields with defaults is non-breaking.
- Vector metadata layout changes require a re-indexing migration plan.
