# Latency run — baseline

- Target: `https://sarjy-tarek.duckdns.org`
- Prompt: `In one sentence, what is the capital of France?`
- Iterations: 5 (warm-up discarded)
- Endpoint: `POST /api/chat (non-streaming)`
- Date: 2026-09-02 — re-measurement taken after the pooled runs; not one of the three
  invocations pooled into `baseline-pooled.md`.

| Segment | p50 (ms) | p95 (ms) |
|---|---:|---:|
| `db_read_ms` | 37.6 | 50.4 |
| `db_write_pre_ms` | — | — |
| `limiter_wait_ms` | 0.0 | 0.0 |
| `llm_ttft_ms` | — | — |
| `llm_total_ms` | 362.6 | 470.3 |
| `db_write_ms` | 11.7 | 18.9 |
| `total_ms` | 397.6 | 506.7 |
| `client_first_byte_ms` | 500.7 | 620.8 |
| `client_total_ms` | 500.7 | 620.8 |

Raw per-run values:

```json
[
  {
    "db_read_ms": 46.5,
    "limiter_wait_ms": 0.0,
    "llm_total_ms": 202.1,
    "db_write_ms": 10.3,
    "llm_ttft_ms": null,
    "total_ms": 261.2,
    "client_first_byte_ms": 362.1,
    "client_total_ms": 362.1
  },
  {
    "db_read_ms": 22.4,
    "limiter_wait_ms": 0.0,
    "llm_total_ms": 470.3,
    "db_write_ms": 12.7,
    "llm_ttft_ms": null,
    "total_ms": 506.7,
    "client_first_byte_ms": 620.8,
    "client_total_ms": 620.8
  },
  {
    "db_read_ms": 22.7,
    "limiter_wait_ms": 0.0,
    "llm_total_ms": 362.7,
    "db_write_ms": 10.9,
    "llm_ttft_ms": null,
    "total_ms": 397.6,
    "client_first_byte_ms": 500.7,
    "client_total_ms": 500.7
  },
  {
    "db_read_ms": 37.6,
    "limiter_wait_ms": 0.0,
    "llm_total_ms": 362.6,
    "db_write_ms": 11.7,
    "llm_ttft_ms": null,
    "total_ms": 413.7,
    "client_first_byte_ms": 522.3,
    "client_total_ms": 522.3
  },
  {
    "db_read_ms": 50.4,
    "limiter_wait_ms": 0.0,
    "llm_total_ms": 241.4,
    "db_write_ms": 18.9,
    "llm_ttft_ms": null,
    "total_ms": 312.2,
    "client_first_byte_ms": 445.2,
    "client_total_ms": 445.2
  }
]
```
