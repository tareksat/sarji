# Latency run — gemini-flash

- Target: `https://sarjy-tarek.duckdns.org/`
- Prompt: `In one sentence, what is the capital of France?`
- Iterations: 5 (warm-up discarded)

Valid: 5/5 turns

| Segment | p50 (ms) | p95 (ms) |
|---|---:|---:|
| `db_read_ms` | 14.5 | 17.7 |
| `db_write_pre_ms` | — | — |
| `limiter_wait_ms` | 0.0 | 0.0 |
| `llm_ttft_ms` | — | — |
| `llm_total_ms` | 954.9 | 4176.4 |
| `db_write_ms` | 8.3 | 10.2 |
| `total_ms` | 981.1 | 4205.3 |
| `client_first_byte_ms` | 1100.6 | 4303.0 |
| `client_total_ms` | 1100.6 | 4303.0 |

Raw per-run values:

```json
[
  {
    "limiter_wait_ms": 0.0,
    "db_read_ms": 17.7,
    "llm_total_ms": 4176.4,
    "db_write_ms": 10.2,
    "llm_ttft_ms": null,
    "total_ms": 4205.3,
    "client_first_byte_ms": 4303.0,
    "client_total_ms": 4303.0,
    "ok": true
  },
  {
    "limiter_wait_ms": 0.0,
    "db_read_ms": 14.5,
    "llm_total_ms": 583.3,
    "db_write_ms": 8.3,
    "llm_ttft_ms": null,
    "total_ms": 607.1,
    "client_first_byte_ms": 751.9,
    "client_total_ms": 751.9,
    "ok": true
  },
  {
    "limiter_wait_ms": 0.0,
    "db_read_ms": 13.4,
    "llm_total_ms": 567.0,
    "db_write_ms": 9.1,
    "llm_ttft_ms": null,
    "total_ms": 590.5,
    "client_first_byte_ms": 703.3,
    "client_total_ms": 703.3,
    "ok": true
  },
  {
    "limiter_wait_ms": 0.0,
    "db_read_ms": 17.7,
    "llm_total_ms": 954.9,
    "db_write_ms": 7.5,
    "llm_ttft_ms": null,
    "total_ms": 981.1,
    "client_first_byte_ms": 1100.6,
    "client_total_ms": 1100.6,
    "ok": true
  },
  {
    "limiter_wait_ms": 0.0,
    "db_read_ms": 13.2,
    "llm_total_ms": 1692.5,
    "db_write_ms": 6.4,
    "llm_ttft_ms": null,
    "total_ms": 1712.8,
    "client_first_byte_ms": 1860.0,
    "client_total_ms": 1860.0,
    "ok": true
  }
]
```
