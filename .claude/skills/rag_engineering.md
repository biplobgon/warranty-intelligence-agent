# Skill — RAG Engineering

> Reusable playbook for evolving the retrieval-augmented generation pipeline.

## When to load this skill

- Adding a new corpus / index
- Tuning chunking, embeddings, retrieval, or grounding
- Wiring a reranker or compressor
- Diagnosing low grounding / high hallucination scores

## Mental model

```
ingest:  raw → parse → chunk → embed → upsert (+ sparse mirror)
query:   query → embed → dense + bm25 → RRF → (rerank?) → grounded prompt → answer + scores
```

## Key files

| File | Role |
|---|---|
| `app/rag/chunker.py` | Token-aware chunking (tiktoken + fallback) |
| `app/rag/retriever.py` | Hybrid: dense + BM25 + RRF |
| `app/rag/grounding.py` | Lexical grounding + per-sentence flagging |
| `app/rag/pipeline.py` | End-to-end `ingest_text`, `ingest_file`, `answer` |
| `app/embeddings/embedder.py` | Provider-backed + hash fallback |
| `app/services/vector_store.py` | Pinecone + in-memory backends |

## Standard tasks

### 1. Add a new index

```python
# 1. Add settings field in app/config/settings.py
pinecone_index_<name>: str = "<name>-index"

# 2. Add HybridRetriever in your agent
self._retriever = HybridRetriever(settings.pinecone_index_<name>)

# 3. Ingest via RAGPipeline.ingest_text(..., index="<name>-index")
```

### 2. Tune chunking

- Increase `chunk_size` for narrative docs (manuals: 500–700)
- Decrease for FAQs / Q&A (200–300)
- `overlap` ~10–15% of chunk_size
- Bump prompt version when changing chunking strategy

### 3. Add a reranker

- Gate behind `FEATURE_RERANKER` in `Settings`
- Implement in `app/rag/reranker.py` (new) with `async rerank(query, items) -> items`
- Call AFTER `HybridRetriever.retrieve` in `RAGPipeline.answer`
- Emit `warranty_rerank_latency_seconds` histogram

### 4. Improve grounding score

Symptoms: `warranty_grounding_score` p50 < 0.5
Try in order:
1. Increase `top_k` (default 6 → 8)
2. Tighten prompt to require `[doc_N]` citations
3. Lower chunk size (more focused contexts)
4. Add metadata filters
5. Introduce a reranker

## Pitfalls

- Don't bypass `HybridRetriever`; agents must not call the vector store directly.
- The in-process BM25 corpus only sees ingested chunks — backfill it after restart if you skip ingestion.
- `tiktoken` may be missing in slim images — chunker falls back to char-based; assert outputs match expected ranges in tests.

## Tests to add when changing RAG

- `tests/unit/test_chunker.py` — boundary + empty + short
- `tests/unit/test_grounding.py` — high-overlap / no-overlap
- `tests/unit/test_retriever.py` — in-memory store filter + top-k
- `tests/integration/test_workflow.py` — full graph with `fake_llm`
