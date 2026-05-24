import asyncio

import pytest

from app.inference.batcher import InferenceBatcher


@pytest.mark.unit
async def test_batcher_coalesces_concurrent_calls():
    batches_seen: list[int] = []

    async def batch_fn(payloads):
        batches_seen.append(len(payloads))
        return [p * 2 for p in payloads]

    batcher = InferenceBatcher(batch_fn, max_batch=8, max_wait_ms=20)
    results = await asyncio.gather(*(batcher.submit(i) for i in range(5)))
    assert results == [0, 2, 4, 6, 8]
    assert sum(batches_seen) == 5
    assert max(batches_seen) >= 2  # at least some coalescing occurred
