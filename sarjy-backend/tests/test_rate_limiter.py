import asyncio

import pytest

from app.core.rate_limiter import RateLimitedError, TokenBucketRateLimiter


def test_a_zero_rate_is_rejected_at_construction():
    # It used to be accepted and then divide by zero on the first queued
    # caller -- an unhandled 500 on the plain endpoint, and on the streamed one
    # a response that simply stopped, with no frame at all.
    with pytest.raises(ValueError):
        TokenBucketRateLimiter(0)


def test_an_available_token_costs_no_wait():
    limiter = TokenBucketRateLimiter(60, max_wait_seconds=0.5)
    waited = asyncio.run(limiter.acquire())
    assert waited < 50.0


def test_the_bucket_empties_after_its_capacity():
    limiter = TokenBucketRateLimiter(1, max_wait_seconds=0.05)

    async def scenario():
        await limiter.acquire()  # the one token
        with pytest.raises(RateLimitedError) as excinfo:
            await limiter.acquire()
        return excinfo.value

    error = asyncio.run(scenario())
    assert error.retry_after_seconds > 0


def test_retry_after_grows_with_the_queue():
    """Every waiter used to be quoted the wait for a single token.

    Told the same short delay, N callers retry together and none of them gets
    through, so the client-visible retry storm never converges.
    """
    limiter = TokenBucketRateLimiter(60, max_wait_seconds=0.0)

    async def scenario():
        for _ in range(60):
            await limiter.acquire()  # drain the bucket

        alone = None
        try:
            await limiter.acquire()
        except RateLimitedError as exc:
            alone = exc.retry_after_seconds

        limiter._waiting = 5  # five callers already queued
        crowded = None
        try:
            await limiter.acquire()
        except RateLimitedError as exc:
            crowded = exc.retry_after_seconds
        return alone, crowded

    alone, crowded = asyncio.run(scenario())
    assert alone is not None and crowded is not None
    assert crowded > alone
