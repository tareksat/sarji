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

    def set(self, name: str, value: float | None) -> None:
        self._spans[name] = None if value is None else round(value, 1)

    def add(self, name: str, value: float) -> None:
        """Accumulate into a span that is entered more than once per turn."""
        self._spans[name] = round((self._spans.get(name) or 0.0) + value, 1)

    def as_dict(self) -> dict[str, float | None]:
        return {**self._spans, "total_ms": round((time.perf_counter() - self._started) * MS, 1)}

    def as_log_line(self) -> str:
        return " ".join(f"{k}={v}" for k, v in self.as_dict().items())
