# Chunking & Embedding Strategy

## Chunking

Implemented in `app/rag/chunker.py`.

| Parameter | Default | Rationale |
|---|---|---|
| `chunk_size` | 500 tokens | Balances context window vs retrieval precision |
| `overlap` | 60 tokens (~12%) | Preserves cross-chunk continuity for procedures |
| Tokenizer | `tiktoken` (`cl100k_base`) | Matches OpenAI embedding tokenization |
| Fallback | character-based (size × 4, overlap × 4) | Used when `tiktoken` is missing |

### Splitting preferences

1. **Paragraph boundaries** preferred (sequences of blank lines).
2. **Sentence boundaries** within paragraphs.
3. **Token boundaries** as a last resort.

### Per-corpus tuning

| Corpus | Chunk size | Overlap | Why |
|---|---|---|---|
| Service manuals (default) | 500 / 60 | 500 / 60 | Procedures span sections; overlap helps |
| Warranty claims | 350 / 40 | Each claim is short; small chunks keep retrieval precise |
| Technician notes | 200 / 20 | Very short; smaller chunks improve recall |

To change per-corpus: pass overrides through `RAGPipeline.ingest_text` (or
extend its signature; PR welcome).

## Embedding

Implemented in `app/embeddings/embedder.py`.

### Models (production)

| Provider | Model | Dim | Cost (rough) | Notes |
|---|---|---|---|---|
| OpenAI | `text-embedding-3-small` | 1536 | $ | Default, balanced |
| OpenAI | `text-embedding-3-large` | 3072 | $$ | When recall matters |
| Vertex AI | `text-embedding-004` | 768 | $ | Default Vertex option |
| Local (vLLM/Triton serving an embedding model) | Varies | Varies | self-hosted | Configurable |

### Fallback (offline / no API key)

Deterministic SHA-256-derived embeddings (`Embedder._hash_embed`) in 1536 dims.
**Not semantically meaningful**, but ensures shape + determinism so the rest of
the pipeline runs end-to-end. Used in tests and CI.

### Batching

`InferenceBatcher` coalesces concurrent single-item calls into batches of up to
64 within a 20 ms window. This yields 5–10× throughput improvement against
rate-limited APIs without harming single-request latency in the common case.

## Vector index layout

| Index | Purpose | Backing dataset |
|---|---|---|
| `warranty-claims` (default name) | Per-claim retrieval | `data/synthetic/warranty_claims.csv` |
| `technical-docs` (default name) | Per-doc-chunk retrieval | `data/synthetic/technical_documents/*.md` |

Configure index names via:

- `PINECONE_INDEX_WARRANTY`
- `PINECONE_INDEX_DOCS`

Recommended Pinecone settings:

- Metric: `cosine`
- Pod / serverless: serverless for variable workloads
- Replicas: 1 for staging, 2+ for prod
- Namespaces: one per tenant if multi-tenant; per-environment otherwise

## Reindexing

When changing chunk size, overlap, or embedding model, you MUST reindex:

```bash
# 1. delete existing index (or rotate to a new name)
# 2. regenerate + re-ingest
make data-synth
make ingest
```

Track the active configuration via a `chunk_strategy_version` metadata field
(future enhancement) so consumers can detect mismatches.

## Quality knobs (recap)

| Symptom | Try |
|---|---|
| Low grounding | smaller chunks, more overlap, reranker, bigger embedding model |
| High latency | larger chunks (fewer vectors), smaller embedding model, batching |
| Off-topic recall | metadata filters, BM25 weighting |
| Inconsistent answers | force `temperature=0.0`, version + freeze prompts |
