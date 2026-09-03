# Latency run — groq-oss

- Target: `https://sarjy-tarek.duckdns.org/`
- Prompt: `In one sentence, what is the capital of France?`
- Iterations: 5 (warm-up discarded)

Valid: 5/5 turns

| Segment | p50 (ms) | p95 (ms) |
|---|---:|---:|
| `db_read_ms` | 12.8 | 14.0 |
| `db_write_pre_ms` | — | — |
| `limiter_wait_ms` | 0.0 | 0.0 |
| `llm_ttft_ms` | — | — |
| `llm_total_ms` | 611.1 | 2647.5 |
| `db_write_ms` | 7.7 | 8.2 |
| `total_ms` | 633.3 | 2669.5 |
| `client_first_byte_ms` | 760.5 | 2800.7 |
| `client_total_ms` | 760.5 | 2800.7 |

Raw per-run values:

```json
[
  {
    "limiter_wait_ms": 0.0,
    "db_read_ms": 14.0,
    "llm_total_ms": 2647.5,
    "db_write_ms": 7.2,
    "llm_ttft_ms": null,
    "total_ms": 2669.5,
    "client_first_byte_ms": 2800.7,
    "client_total_ms": 2800.7,
    "ok": true
  },
  {
    "limiter_wait_ms": 0.0,
    "db_read_ms": 11.6,
    "llm_total_ms": 1879.8,
    "db_write_ms": 7.7,
    "llm_ttft_ms": null,
    "total_ms": 1900.2,
    "client_first_byte_ms": 1997.4,
    "client_total_ms": 1997.4,
    "ok": true
  },
  {
    "limiter_wait_ms": 0.0,
    "db_read_ms": 13.5,
    "llm_total_ms": 611.1,
    "db_write_ms": 7.8,
    "llm_ttft_ms": null,
    "total_ms": 633.3,
    "client_first_byte_ms": 760.5,
    "client_total_ms": 760.5,
    "ok": true
  },
  {
    "limiter_wait_ms": 0.0,
    "db_read_ms": 12.8,
    "llm_total_ms": 205.0,
    "db_write_ms": 8.2,
    "llm_ttft_ms": null,
    "total_ms": 227.0,
    "client_first_byte_ms": 359.7,
    "client_total_ms": 359.7,
    "ok": true
  },
  {
    "limiter_wait_ms": 0.0,
    "db_read_ms": 12.6,
    "llm_total_ms": 187.3,
    "db_write_ms": 7.1,
    "llm_ttft_ms": null,
    "total_ms": 208.1,
    "client_first_byte_ms": 305.6,
    "client_total_ms": 305.6,
    "ok": true
  }
]
```
