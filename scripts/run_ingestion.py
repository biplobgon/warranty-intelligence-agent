"""End-to-end ingestion pipeline.

Reads:
    * data/synthetic/warranty_claims.csv     → warranty index
    * data/synthetic/technical_documents/*.md → docs index

Chunks, embeds, and upserts into the configured vector store.  Falls back to
the in-memory store when Pinecone is unavailable so the script is safe to run
locally without any credentials.
"""

from __future__ import annotations

import asyncio
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.rag.pipeline import get_rag_pipeline  # noqa: E402
from app.utils.logging import configure_logging, get_logger  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
CLAIMS_CSV = ROOT / "data" / "synthetic" / "warranty_claims.csv"
SAMPLE_CSV = ROOT / "data" / "synthetic" / "samples" / "sample_warranty_claims.csv"
DOCS_DIR = ROOT / "data" / "synthetic" / "technical_documents"


def _claims_to_text(row: dict[str, str]) -> str:
    return (
        f"Claim {row['claim_id']} | {row['make']} {row['model']} {row['model_year']}\n"
        f"Component: {row['component']} | Failure: {row['failure_mode']}\n"
        f"Status: {row['status']} | Cost: ${row['repair_cost_usd']} | Mileage: {row['mileage_km']} km\n"
        f"Description: {row['description']}\n"
        f"Resolution: {row['resolution']}\n"
        f"Technician notes: {row['technician_notes']}"
    )


async def ingest_claims(max_rows: int | None = 1000) -> int:
    log = get_logger("ingest.claims")
    rag = get_rag_pipeline()
    csv_path = CLAIMS_CSV if CLAIMS_CSV.exists() else SAMPLE_CSV
    if not csv_path.exists():
        log.warning("no_claims_csv_found", path=str(csv_path))
        return 0

    total = 0
    with csv_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    if max_rows is not None:
        rows = rows[:max_rows]

    for row in rows:
        text = _claims_to_text(row)
        meta = {
            "claim_id": row["claim_id"],
            "vin": row["vin"],
            "component": row["component"],
            "failure_mode": row["failure_mode"],
            "make": row["make"],
            "model": row["model"],
            "status": row["status"],
            "repair_cost_usd": float(row["repair_cost_usd"]),
        }
        res = await rag.ingest_text(
            text,
            document_id=row["claim_id"],
            source=f"warranty_claim:{row['claim_id']}",
            index=rag._settings.pinecone_index_warranty,
            metadata=meta,
        )
        total += res.chunks_indexed
    log.info("claims_ingested", rows=len(rows), chunks=total)
    return total


async def ingest_documents() -> int:
    log = get_logger("ingest.docs")
    rag = get_rag_pipeline()
    if not DOCS_DIR.exists():
        log.warning("no_documents_dir", path=str(DOCS_DIR))
        return 0
    total = 0
    for path in sorted(DOCS_DIR.glob("*.md")):
        res = await rag.ingest_file(path)
        total += res.chunks_indexed
    log.info("documents_ingested", chunks=total)
    return total


async def main() -> None:
    configure_logging()
    log = get_logger("ingest")
    log.info("ingestion_started")
    claims = await ingest_claims()
    docs = await ingest_documents()
    log.info("ingestion_complete", claim_chunks=claims, doc_chunks=docs)


if __name__ == "__main__":
    asyncio.run(main())
