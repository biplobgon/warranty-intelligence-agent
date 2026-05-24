# Synthetic Data — Methodology

The platform ships with a deterministic synthetic data generator
(`scripts/generate_synthetic_data.py`) that produces realistic warranty data
without using any restricted or proprietary sources.

## Why synthetic

- **Reproducibility** — same seed produces same data.
- **Privacy** — no real customer data, no real VINs.
- **License clean** — generator output is MIT-licensed alongside the code.
- **Composable** — claims, telemetry, and docs share VIN / component pools so
  realistic joins exist for demo purposes.

## What gets generated

```
data/synthetic/
├── warranty_claims.csv         ~10 000 rows
├── vehicle_telemetry.csv       ~50 000 rows
├── technical_documents/        ~15 markdown manuals
└── samples/
    ├── sample_warranty_claims.csv      first 50 rows (kept in git)
    └── sample_vehicle_telemetry.csv    first 50 rows (kept in git)
```

The full CSVs are `.gitignore`d (large); the samples preserve the schema in git
for first-impression repository navigation.

## Generation parameters

`scripts/generate_synthetic_data.py`:

| Knob | Default | Notes |
|---|---|---|
| `RNG_SEED` | 7 | Determinism |
| Claims count | 10 000 | `generate_claims(n_rows=...)` |
| Telemetry count | 50 000 | `generate_telemetry(n_rows=...)` |
| Documents count | 15 | `generate_documents(n_docs=...)` |
| VIN pool for telemetry | 2 000 | Smaller than total VINs so joins are dense |

## Distributions

- **Components**: 25 representative powertrain / chassis / infotainment components.
- **Failure modes**: 3–4 plausible modes per component.
- **Makes / models**: 7 fictional makes × 6 models each (no real OEMs).
- **Status mix**: ~50% closed, ~17% in_progress / open / denied each.
- **Repair cost**: uniform $50–$4 500.
- **Mileage**: uniform 1 000–220 000 km.
- **Telemetry anomaly rate**: ~4% of points carry a DTC + anomaly flag.
- **Document template**: 9-section service manual (purpose, applicable vehicles,
  symptoms, diagnostic procedure, repair procedure, verification, warranty
  coding, related bulletins, revision history).

## VIN generation

`_vin()` produces 17-char strings from `{A–Z, 0–9}` excluding `I O Q`, matching
the standard VIN alphabet. They are syntactically valid VINs but check-digit
(position 9) is NOT computed — these are clearly fake VINs by design.

## Realism vs. fidelity

The synthetic data is **structurally realistic** but does not capture:

- Long-tail technician notes (real notes have abbreviations, typos, mixed languages)
- Seasonal claim patterns
- Dealer / region biases
- Correlated failure modes (e.g. battery failures clustered in cold climates)

For research use, blend the synthetic baseline with a subset of NHTSA complaints
(see `sources.md`).

## Regeneration

```bash
make data-synth      # generates everything
make ingest          # chunks + embeds + upserts into vector store
```

The ingestion script auto-falls back to `data/synthetic/samples/sample_*.csv`
if the full file is missing — useful in CI and minimal-data environments.
