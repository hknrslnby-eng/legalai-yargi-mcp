import time

import pytest

from legalai.packages.aihm.rate_limiter import RateLimiter


@pytest.mark.asyncio
async def test_rate_limiter_allows_burst_up_to_max():
    limiter = RateLimiter(max_requests=3, period_seconds=3600)

    start = time.monotonic()
    for _ in range(3):
        await limiter.acquire()
    elapsed = time.monotonic() - start

    assert elapsed < 0.5  # ilk 3 istek anında geçmeli


@pytest.mark.asyncio
async def test_rate_limiter_throttles_beyond_max():
    limiter = RateLimiter(max_requests=2, period_seconds=0.2)

    for _ in range(2):
        await limiter.acquire()

    start = time.monotonic()
    await limiter.acquire()
    elapsed = time.monotonic() - start

    assert elapsed > 0.05  # bir sonraki token'ı beklemesi gerekiyor
