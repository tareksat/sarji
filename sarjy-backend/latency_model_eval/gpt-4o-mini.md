# Latency run — gpt-4o-mini

- Target: `https://sarjy-tarek.duckdns.org/`
- Prompt: `In one sentence, what is the capital of France?`
- Iterations: 5 (warm-up discarded)

Valid: 5/5 turns

| Segment | p50 (ms) | p95 (ms) |
|---|---:|---:|
| `db_read_ms` | 11.9 | 15.6 |
| `db_write_pre_ms` | — | — |
| `limiter_wait_ms` | 0.0 | 0.0 |
| `llm_ttft_ms` | — | — |
| `llm_total_ms` | 384.5 | 604.6 |
| `db_write_ms` | 7.2 | 17.4 |
| `total_ms` | 414.4 | 624.1 |
| `client_first_byte_ms` | 545.0 | 725.3 |
| `client_total_ms` | 545.0 | 725.3 |

Raw per-run values:

```json
[
  {
    "limiter_wait_ms": 0.0,
    "db_read_ms": 15.6,
    "llm_total_ms": 416.5,
    "db_write_ms": 6.2,
    "llm_ttft_ms": null,
    "total_ms": 439.2,
    "client_first_byte_ms": 578.6,
    "client_total_ms": 578.6,
    "ok": true
  },
  {
    "limiter_wait_ms": 0.0,
    "db_read_ms": 11.9,
    "llm_total_ms": 179.2,
    "db_write_ms": 6.2,
    "llm_ttft_ms": null,
    "total_ms": 198.4,
    "client_first_byte_ms": 322.5,
    "client_total_ms": 322.5,
    "ok": true
  },
  {
    "limiter_wait_ms": 0.0,
    "db_read_ms": 11.6,
    "llm_total_ms": 384.5,
    "db_write_ms": 17.4,
    "llm_ttft_ms": null,
    "total_ms": 414.4,
    "client_first_byte_ms": 545.0,
    "client_total_ms": 545.0,
    "ok": true
  },
  {
    "limiter_wait_ms": 0.0,
    "db_read_ms": 10.6,
    "llm_total_ms": 604.6,
    "db_write_ms": 7.9,
    "llm_ttft_ms": null,
    "total_ms": 624.1,
    "client_first_byte_ms": 725.3,
    "client_total_ms": 725.3,
    "ok": true
  },
  {
    "limiter_wait_ms": 0.0,
    "db_read_ms": 12.5,
    "llm_total_ms": 376.6,
    "db_write_ms": 7.2,
    "llm_ttft_ms": null,
    "total_ms": 397.3,
    "client_first_byte_ms": 494.6,
    "client_total_ms": 494.6,
    "ok": true
  }
]
```
