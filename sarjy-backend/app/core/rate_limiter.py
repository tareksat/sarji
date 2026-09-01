import asyncio
import logging
import time

logger = logging.getLogger(__name__)


class TokenBucketRateLimiter:
    """Caps calls to roughly `rate_per_minute` per rolling minute.
    Callers that would exceed the cap wait (queue) instead of failing."""

    def __init__(self, rate_per_minute: int):
        self.capacity = rate_per_minute
        self.tokens = float(rate_per_minute)
        self.refill_rate = rate_per_minute / 60.0  # tokens per second
        self._updated_at = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        while True:
            async with self._lock:
                now = time.monotonic()
                elapsed = now - self._updated_at
                self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
                self._updated_at = now

                if self.tokens >= 1:
                    self.tokens -= 1
                    return

                wait_time = (1 - self.tokens) / self.refill_rate

            logger.info("Rate limiter: waiting %.2fs for a token", wait_time)
            await asyncio.sleep(wait_time)
