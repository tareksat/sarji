import asyncio
import logging
import time

logger = logging.getLogger(__name__)


class RateLimitedError(Exception):
    """Raised when a caller would have to queue longer than the cap allows."""

    def __init__(self, retry_after_seconds: float):
        self.retry_after_seconds = retry_after_seconds
        super().__init__(f"Rate limited; retry in {retry_after_seconds:.1f}s")


class TokenBucketRateLimiter:
    """Caps calls to roughly `rate_per_minute` per rolling minute.

    Callers that would exceed the cap queue instead of failing, but only up to
    `max_wait_seconds` -- an unbounded queue is indistinguishable from a hung
    request from the user's side.

    Per process. With several workers or several containers the effective
    ceiling is that multiple of `rate_per_minute`, so this bounds a single
    process's burst rather than the account's spend; a shared bucket would need
    shared state (Redis).
    """

    def __init__(self, rate_per_minute: int, max_wait_seconds: float = 2.0):
        if rate_per_minute <= 0:
            raise ValueError("rate_per_minute must be positive")
        self.capacity = rate_per_minute
        self.tokens = float(rate_per_minute)
        self.refill_rate = rate_per_minute / 60.0  # tokens per second
        self.max_wait_seconds = max_wait_seconds
        self._updated_at = time.monotonic()
        self._lock = asyncio.Lock()
        # Callers already sleeping on this bucket. Their tokens are spoken for,
        # so a new arrival has to queue behind them rather than being quoted --
        # and admitted on -- a wait that only accounts for itself.
        self._waiting = 0

    async def acquire(self) -> float:
        """Take a token, waiting if necessary. Returns the ms spent waiting."""
        started = time.monotonic()
        queued = False
        try:
            while True:
                async with self._lock:
                    now = time.monotonic()
                    elapsed = now - self._updated_at
                    self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
                    self._updated_at = now

                    if self.tokens >= 1:
                        self.tokens -= 1
                        return (time.monotonic() - started) * 1000.0

                    # Ahead of this caller in the queue, plus the token it needs
                    # itself. Quoting the single-token wait to everyone tells N
                    # callers the same short delay, they all retry together, and
                    # none of them converges.
                    ahead = self._waiting if queued else self._waiting + 1
                    wait_time = (ahead - self.tokens) / self.refill_rate

                    if not queued:
                        queued = True
                        self._waiting += 1

                if (time.monotonic() - started) + wait_time > self.max_wait_seconds:
                    logger.warning(
                        "Rate limiter: refusing to queue %.2fs (cap %.2fs, %d waiting)",
                        wait_time, self.max_wait_seconds, self._waiting,
                    )
                    raise RateLimitedError(wait_time)

                logger.info("Rate limiter: waiting %.2fs for a token", wait_time)
                # Sleeping the whole estimate would overshoot when a token frees
                # up early, so re-check on a bounded tick.
                await asyncio.sleep(min(wait_time, 1.0 / self.refill_rate))
        finally:
            if queued:
                self._waiting -= 1
