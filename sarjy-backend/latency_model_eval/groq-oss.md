# Latency run — groq-oss

- Target: `https://sarjy-tarek.duckdns.org/`
- Prompt: `In one sentence, what is the capital of France?`
- Iterations: 5 (warm-up discarded)

Valid: 5/5 turns

| Segment | p50 (ms) | p95 (ms) |
|---|---:|---:|
| `db_read_ms` | 20.4 | 22.1 |
| `db_write_pre_ms` | — | — |
| `limiter_wait_ms` | 0.0 | 0.0 |
| `llm_ttft_ms` | — | — |
| `llm_total_ms` | 431.7 | 816.3 |
| `db_write_ms` | 9.9 | 31.2 |
| `total_ms` | 485.4 | 840.0 |
| `client_first_byte_ms` | 608.3 | 974.0 |
| `client_total_ms` | 608.3 | 974.0 |

Raw per-run values:

```json
[
  {
    "limiter_wait_ms": 0.0,
    "db_read_ms": 12.8,
    "llm_total_ms": 816.3,
    "db_write_ms": 9.9,
    "llm_ttft_ms": null,
    "total_ms": 840.0,
    "client_first_byte_ms": 974.0,
    "client_total_ms": 974.0,
    "ok": true
  },
  {
    "limiter_wait_ms": 0.0,
    "db_read_ms": 18.3,
    "llm_total_ms": 321.8,
    "db_write_ms": 8.0,
    "llm_ttft_ms": null,
    "total_ms": 349.2,
    "client_first_byte_ms": 456.5,
    "client_total_ms": 456.5,
    "ok": true
  },
  {
    "limiter_wait_ms": 0.0,
    "db_read_ms": 22.1,
    "llm_total_ms": 305.2,
    "db_write_ms": 21.7,
    "llm_ttft_ms": null,
    "total_ms": 350.2,
    "client_first_byte_ms": 487.4,
    "client_total_ms": 487.4,
    "ok": true
  },
  {
    "limiter_wait_ms": 0.0,
    "db_read_ms": 20.4,
    "llm_total_ms": 590.0,
    "db_write_ms": 7.9,
    "llm_ttft_ms": null,
    "total_ms": 619.3,
    "client_first_byte_ms": 766.9,
    "client_total_ms": 766.9,
    "ok": true
  },
  {
    "limiter_wait_ms": 0.0,
    "db_read_ms": 21.7,
    "llm_total_ms": 431.7,
    "db_write_ms": 31.2,
    "llm_ttft_ms": null,
    "total_ms": 485.4,
    "client_first_byte_ms": 608.3,
    "client_total_ms": 608.3,
    "ok": true
  }
]
```
