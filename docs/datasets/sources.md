# Dataset Sources

The platform ships with **synthetic** datasets out of the box (see `synthetic_data.md`)
so that anyone can reproduce the demo end-to-end. For higher-fidelity demos and
research, the following public sources are recommended.

> ⚠️ **License compliance**: verify the license of any external dataset before
> ingesting. The platform itself is MIT; embedded data may carry stricter terms.

## Warranty / claims

| Dataset | Where | License | Notes |
|---|---|---|---|
| NHTSA Vehicle Complaints | https://www.nhtsa.gov/nhtsa-datasets-and-apis | Public domain (US Gov) | Free-text consumer complaints; great for retrieval realism |
| NHTSA Investigations / Recalls | https://www.nhtsa.gov/recalls | Public domain | Structured + free text |
| AutoMPG / UCI ML | https://archive.ics.uci.edu/dataset/9/auto+mpg | CC0 / UCI | Vehicle attributes (small) |
| Carvana Image / Tabular sets (Kaggle) | https://www.kaggle.com/ | Varies | Vehicle metadata |

## Predictive maintenance / failure analysis

| Dataset | Where | License | Notes |
|---|---|---|---|
| NASA C-MAPSS Turbofan Degradation | NASA Prognostics CoE | NASA Open Data | Classic predictive maintenance benchmark |
| AI4I 2020 Predictive Maintenance | UCI ML | CC BY 4.0 | Synthetic-ish machine sensor / failure data |
| Backblaze Hard Drive Stats | https://www.backblaze.com/cloud-storage/resources/hard-drive-test-data | CC BY 4.0 | Long-running operational data |

## Technical documents / RAG corpora

| Dataset | Where | License | Notes |
|---|---|---|---|
| Wikipedia automotive subset | Wikimedia dumps | CC BY-SA 3.0 | Generic automotive knowledge |
| OEM Service Manuals (public excerpts) | Manufacturer websites | Varies (often "internal only") | Use with care; prefer synthetic |
| arXiv (RAG / agents papers) | arxiv.org | arXiv non-exclusive | Useful for "research mode" demos |

## Vehicle telemetry

Real telemetry datasets are rarely public. Use:

| Dataset | Where | License | Notes |
|---|---|---|---|
| OpenXC traces | https://openxcplatform.com/ | BSD | Sparse, CAN-bus excerpts |
| FleetDM datasets | Various Kaggle competitions | Varies | Often anonymized fleet data |

## Loading external datasets

The ingestion pipeline accepts:

- CSV (claims-style): see `scripts/run_ingestion.py::ingest_claims`
- Markdown / TXT / PDF (documents): see `scripts/run_ingestion.py::ingest_documents`

Adapt the `_claims_to_text` builder for your source's columns. Place raw data in
`data/raw/` (gitignored).

## Ethical / legal notes

- Never ingest customer PII into a vector index unless it's been redacted.
  Use `app/governance/pii.py` *before* ingestion.
- Verify dataset license before redistribution. Some datasets allow research use
  but forbid commercial use.
- For OEM-internal data, follow your organization's data classification policy.
