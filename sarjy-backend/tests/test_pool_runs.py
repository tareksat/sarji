import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from pool_runs import parse_run, pool  # noqa: E402

RAW = """# Latency run — streaming-1

- Target: `https://example.test`
- Prompt: `In one sentence, what is the capital of France?`
- Iterations: 2 (warm-up discarded)

| Segment | p50 (ms) | p95 (ms) |
|---|---:|---:|
| `total_ms` | 10.0 | 20.0 |

Raw per-run values:

```json
[
  {"total_ms": 10.0, "llm_ttft_ms": 5.0},
  {"total_ms": 20.0, "llm_ttft_ms": 15.0}
]
```
"""


def test_parse_run_extracts_header_and_rows():
    base_url, prompt, rows = parse_run(RAW)
    assert base_url == "https://example.test"
    assert prompt == "In one sentence, what is the capital of France?"
    assert rows == [
        {"total_ms": 10.0, "llm_ttft_ms": 5.0},
        {"total_ms": 20.0, "llm_ttft_ms": 15.0},
    ]


def test_pool_concatenates_rows_and_names_sources():
    rows_a = [{"total_ms": 10.0}, {"total_ms": 30.0}]
    rows_b = [{"total_ms": 20.0}]
    text = pool("streaming", "https://example.test", "p", [("streaming-1", rows_a), ("streaming-2", rows_b)])
    assert "# Latency run — streaming (pooled)" in text
    assert "- Pooled from: `streaming-1` (2), `streaming-2` (1)" in text
    assert "- Iterations: 3" in text
    # p50 of [10, 20, 30] under measure.py's percentile() is the 2nd value.
    assert "| `total_ms` | 20.0 | 30.0 |" in text
    assert '"total_ms": 30.0' in text
