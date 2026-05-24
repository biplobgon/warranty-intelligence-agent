# Skill — Async Python Workflows

## When to load

- Adding new I/O on the hot path
- Diagnosing slow / blocked event loops
- Coordinating concurrent agent calls

## Mental model

The hot path is **fully async**. Sync libraries (Pinecone v5 SDK, some Vertex
calls) are wrapped via `loop.run_in_executor(None, ...)`.

## Standard patterns

### 1. Concurrent fan-out

```python
import asyncio
results = await asyncio.gather(agent1.run(...), agent2.run(...), return_exceptions=True)
```

`return_exceptions=True` so one failure doesn't take everyone down.
`BaseAgent.run` already returns an `AgentResult` (never raises), so usually omit.

### 2. Bounded concurrency

```python
sem = asyncio.Semaphore(8)
async def bounded(x):
    async with sem:
        return await call(x)
results = await asyncio.gather(*(bounded(x) for x in items))
```

### 3. Time-bounded

```python
try:
    result = await asyncio.wait_for(work(), timeout=10.0)
except asyncio.TimeoutError:
    ...
```

### 4. Wrap a sync API

```python
loop = asyncio.get_event_loop()
result = await loop.run_in_executor(None, lambda: sync_lib.call(args))
```

See `app/services/vector_store.py::PineconeVectorStore` for a real example.

### 5. Micro-batching

`app/inference/batcher.py` — coalesces concurrent single-item embed requests
into batches of up to N within a small window. Use it when:

- Many concurrent callers issue 1-item calls
- The downstream API benefits from batching (most embedding APIs do)
- Item latency budget can tolerate ~20 ms

## Hard rules

- Never call `time.sleep` on the hot path; use `await asyncio.sleep`.
- Never call sync HTTP clients (`requests`) on the hot path; use `httpx.AsyncClient`.
- Don't `asyncio.run()` inside a request handler — you're already in a loop.
- Don't share mutable state across requests without an `asyncio.Lock`.

## Debugging

- Set `PYTHONASYNCIODEBUG=1` to surface long-running tasks.
- Use `asyncio.current_task()` + `asyncio.all_tasks()` for snapshots.
- OTel spans show where time is actually spent.
