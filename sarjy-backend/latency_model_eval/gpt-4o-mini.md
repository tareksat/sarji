# Latency run — gpt-4o-mini

- Target: `https://sarjy-tarek.duckdns.org/`
- Prompt: `In one sentence, what is the capital of France?`
- Iterations: 5 (warm-up discarded)

Valid: 5/5 turns

| Segment | p50 (ms) | p95 (ms) |
|---|---:|---:|
| `db_read_ms` | 13.3 | 17.5 |
| `db_write_pre_ms` | — | — |
| `limiter_wait_ms` | 0.0 | 0.0 |
| `llm_ttft_ms` | — | — |
| `llm_total_ms` | 539.1 | 3411.8 |
| `db_write_ms` | 9.2 | 14.9 |
| `total_ms` | 560.8 | 3432.6 |
| `client_first_byte_ms` | 684.1 | 3537.3 |
| `client_total_ms` | 684.1 | 3537.3 |

Raw per-run values:

```json
[
  {
    "limiter_wait_ms": 0.0,
    "db_read_ms": 11.9,
    "llm_total_ms": 539.1,
    "db_write_ms": 8.8,
    "llm_ttft_ms": null,
    "total_ms": 560.8,
    "client_first_byte_ms": 684.1,
    "client_total_ms": 684.1,
    "ok": true
  },
  {
    "limiter_wait_ms": 0.0,
    "db_read_ms": 11.9,
    "llm_total_ms": 3411.8,
    "db_write_ms": 8.0,
    "llm_ttft_ms": null,
    "total_ms": 3432.6,
    "client_first_byte_ms": 3537.3,
    "client_total_ms": 3537.3,
    "ok": true
  },
  {
    "limiter_wait_ms": 0.0,
    "db_read_ms": 17.5,
    "llm_total_ms": 251.1,
    "db_write_ms": 9.2,
    "llm_ttft_ms": null,
    "total_ms": 278.9,
    "client_first_byte_ms": 431.9,
    "client_total_ms": 431.9,
    "ok": true
  },
  {
    "limiter_wait_ms": 0.0,
    "db_read_ms": 13.3,
    "llm_total_ms": 2686.4,
    "db_write_ms": 14.0,
    "llm_ttft_ms": null,
    "total_ms": 2714.7,
    "client_first_byte_ms": 2838.0,
    "client_total_ms": 2838.0,
    "ok": true
  },
  {
    "limiter_wait_ms": 0.0,
    "db_read_ms": 14.9,
    "llm_total_ms": 525.0,
    "db_write_ms": 14.9,
    "llm_ttft_ms": null,
    "total_ms": 555.9,
    "client_first_byte_ms": 659.2,
    "client_total_ms": 659.2,
    "ok": true
  }
]
```
