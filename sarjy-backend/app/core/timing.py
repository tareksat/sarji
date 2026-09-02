import time
from contextlib import contextmanager

MS = 1000.0


class Timings:
    """Per-turn wall-clock spans, in milliseconds.

    Returned with the response and logged, so a slow turn on the deployed app
    can be attributed without a profiler attached.
    """

    def __init__(self) -> None:
        self._started = time.perf_counter()
        self._spans: dict[str, float | None] = {}

    @contextmanager
    def span(self, name: str):
        started = time.perf_counter()
        try:
            yield
        finally:
            self._spans[name] = round((time.perf_counter() - started) * MS, 1)

    def mark(self, name: str) -> None:
        """Record the time from the start of the turn to now."""
        self._spans[name] = round((time.perf_counter() - self._started) * MS, 1)

    def mark_from(self, name: str, started: float) -> None:
        """Record the time from an explicit `time.perf_counter()` origin to now.

        Time-to-first-token has to be measured from the model call, not from the
        start of the turn: measured from the turn it silently includes the
        database reads and whatever the rate limiter queued, and stops being
        comparable to the whole-response duration reported beside it.
        """
        self._spans[name] = round((time.perf_counter() - started) * MS, 1)

    def set(self, name: str, value: float | None) -> None:
        self._spans[name] = None if value is None else round(value, 1)

    def add(self, name: str, value: float) -> None:
        """Accumulate into a span that is entered more than once per turn."""
        self._spans[name] = round((self._spans.get(name) or 0.0) + value, 1)

    def as_dict(self) -> dict[str, float | None]:
        return {**self._spans, "total_ms": round((time.perf_counter() - self._started) * MS, 1)}

    def as_log_line(self, snapshot: dict[str, float | None] | None = None) -> str:
        """Format a snapshot for the log.

        Pass the same dict that goes on the wire. `as_dict` recomputes
        `total_ms` on every call, so logging one and sending another makes the
        two disagree by the cost of the logging itself -- confusing during
        exactly the latency work this instrumentation exists for.
        """
        return " ".join(f"{k}={v}" for k, v in (snapshot or self.as_dict()).items())
