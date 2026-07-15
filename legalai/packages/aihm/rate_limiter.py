"""Basit token-bucket hız sınırlayıcı.

HUDOC'a nezaket kuralı: FORK-KAPSAMLI-PLAN.md §4.3 — saatte 60 istekten
fazla değil. Bu sınıf herhangi bir dış istemci için genel amaçlı kullanılabilir.
"""
from __future__ import annotations

import asyncio
import time


class RateLimiter:
    def __init__(self, max_requests: int = 60, period_seconds: float = 3600.0) -> None:
        self._max_requests = float(max_requests)
        self._period = period_seconds
        self._tokens = float(max_requests)
        self._updated_at = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        async with self._lock:
            while True:
                now = time.monotonic()
                elapsed = now - self._updated_at
                self._updated_at = now
                refill_rate = self._max_requests / self._period
                self._tokens = min(self._max_requests, self._tokens + elapsed * refill_rate)

                if self._tokens >= 1:
                    self._tokens -= 1
                    return

                wait_for = (1 - self._tokens) / refill_rate
                await asyncio.sleep(wait_for)
