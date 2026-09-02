# Latency run — streaming

- Target: `https://sarjy-tarek.duckdns.org`
- Prompt: `In one sentence, what is the capital of France?`
- Iterations: 5 (warm-up discarded)
- Endpoint: `POST /api/chat/stream`
- Date: 2026-09-02 — re-measurement taken after the pooled runs; not one of the three
  invocations pooled into `streaming-pooled.md`.

| Segment | p50 (ms) | p95 (ms) |
|---|---:|---:|
| `db_read_ms` | 12.0 | 18.5 |
| `db_write_pre_ms` | 19.2 | 44.6 |
| `limiter_wait_ms` | 0.0 | 0.0 |
| `llm_ttft_ms` | 462.5 | 1421.3 |
| `llm_total_ms` | — | — |
| `db_write_ms` | 17.3 | 29.9 |
| `total_ms` | 524.2 | 1473.0 |
| `client_first_byte_ms` | 561.6 | 1544.3 |
| `client_total_ms` | 626.9 | 1570.5 |

Raw per-run values:

```json
[
  {
    "db_write_pre_ms": 19.2,
    "db_read_ms": 8.2,
    "limiter_wait_ms": 0.0,
    "llm_ttft_ms": 1421.3,
    "db_write_ms": 13.7,
    "llm_total_ms": null,
    "total_ms": 1473.0,
    "client_first_byte_ms": 1544.3,
    "client_total_ms": 1570.5
  },
  {
    "db_write_pre_ms": 14.2,
    "db_read_ms": 18.5,
    "limiter_wait_ms": 0.0,
    "llm_ttft_ms": 537.3,
    "db_write_ms": 12.1,
    "llm_total_ms": null,
    "total_ms": 601.8,
    "client_first_byte_ms": 631.9,
    "client_total_ms": 702.9
  },
  {
    "db_write_pre_ms": 18.9,
    "db_read_ms": 10.8,
    "limiter_wait_ms": 0.0,
    "llm_ttft_ms": 462.5,
    "db_write_ms": 18.5,
    "llm_total_ms": null,
    "total_ms": 512.2,
    "client_first_byte_ms": 561.6,
    "client_total_ms": 605.1
  },
  {
    "db_write_pre_ms": 24.6,
    "db_read_ms": 12.2,
    "limiter_wait_ms": 0.0,
    "llm_ttft_ms": 440.7,
    "db_write_ms": 29.9,
    "llm_total_ms": null,
    "total_ms": 524.2,
    "client_first_byte_ms": 545.7,
    "client_total_ms": 626.9
  },
  {
    "db_write_pre_ms": 44.6,
    "db_read_ms": 12.0,
    "limiter_wait_ms": 0.0,
    "llm_ttft_ms": 263.7,
    "db_write_ms": 17.3,
    "llm_total_ms": null,
    "total_ms": 312.0,
    "client_first_byte_ms": 365.7,
    "client_total_ms": 410.2
  }
]
```
