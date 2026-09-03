# Latency run — gemini-flash

- Target: `https://sarjy-tarek.duckdns.org/`
- Prompt: `In one sentence, what is the capital of France?`
- Iterations: 5 (warm-up discarded)

Valid: 5/5 turns

| Segment | p50 (ms) | p95 (ms) |
|---|---:|---:|
| `db_read_ms` | 12.6 | 51.5 |
| `db_write_pre_ms` | — | — |
| `limiter_wait_ms` | 0.0 | 0.0 |
| `llm_ttft_ms` | — | — |
| `llm_total_ms` | 325.7 | 1250.1 |
| `db_write_ms` | 6.9 | 8.4 |
| `total_ms` | 343.8 | 1270.4 |
| `client_first_byte_ms` | 462.2 | 1393.0 |
| `client_total_ms` | 462.2 | 1393.0 |

Raw per-run values:

```json
[
  {
    "limiter_wait_ms": 0.0,
    "db_read_ms": 12.6,
    "llm_total_ms": 1250.1,
    "db_write_ms": 6.8,
    "llm_ttft_ms": null,
    "total_ms": 1270.4,
    "client_first_byte_ms": 1393.0,
    "client_total_ms": 1393.0,
    "ok": true
  },
  {
    "limiter_wait_ms": 0.0,
    "db_read_ms": 12.6,
    "llm_total_ms": 240.6,
    "db_write_ms": 7.7,
    "llm_ttft_ms": null,
    "total_ms": 261.9,
    "client_first_byte_ms": 451.8,
    "client_total_ms": 451.8,
    "ok": true
  },
  {
    "limiter_wait_ms": 0.0,
    "db_read_ms": 10.3,
    "llm_total_ms": 325.7,
    "db_write_ms": 6.9,
    "llm_ttft_ms": null,
    "total_ms": 343.8,
    "client_first_byte_ms": 462.2,
    "client_total_ms": 462.2,
    "ok": true
  },
  {
    "limiter_wait_ms": 0.0,
    "db_read_ms": 51.5,
    "llm_total_ms": 514.9,
    "db_write_ms": 6.7,
    "llm_ttft_ms": null,
    "total_ms": 574.1,
    "client_first_byte_ms": 717.1,
    "client_total_ms": 717.1,
    "ok": true
  },
  {
    "limiter_wait_ms": 0.0,
    "db_read_ms": 11.2,
    "llm_total_ms": 223.8,
    "db_write_ms": 8.4,
    "llm_ttft_ms": null,
    "total_ms": 244.3,
    "client_first_byte_ms": 363.4,
    "client_total_ms": 363.4,
    "ok": true
  }
]
```
