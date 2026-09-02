# Latency run — provider-groq-2

- Target: `https://sarjy-tarek.duckdns.org`
- Prompt: `In one sentence, what is the capital of France?`
- Iterations: 5 (warm-up discarded)

| Segment | p50 (ms) | p95 (ms) |
|---|---:|---:|
| `db_read_ms` | 10.5 | 23.2 |
| `db_write_pre_ms` | 14.5 | 29.0 |
| `limiter_wait_ms` | 0.0 | 0.0 |
| `llm_ttft_ms` | 450.0 | 713.0 |
| `llm_total_ms` | — | — |
| `db_write_ms` | 8.4 | 9.0 |
| `total_ms` | 505.6 | 761.2 |
| `client_first_byte_ms` | 552.5 | 805.1 |
| `client_total_ms` | 599.9 | 875.3 |

Raw per-run values:

```json
[
  {
    "db_write_pre_ms": 15.2,
    "db_read_ms": 10.5,
    "limiter_wait_ms": 0.0,
    "llm_ttft_ms": 713.0,
    "db_write_ms": 9.0,
    "llm_total_ms": null,
    "total_ms": 761.2,
    "client_first_byte_ms": 805.1,
    "client_total_ms": 875.3
  },
  {
    "db_write_pre_ms": 14.5,
    "db_read_ms": 17.5,
    "limiter_wait_ms": 0.0,
    "llm_ttft_ms": 450.0,
    "db_write_ms": 7.8,
    "llm_total_ms": null,
    "total_ms": 505.6,
    "client_first_byte_ms": 552.5,
    "client_total_ms": 599.9
  },
  {
    "db_write_pre_ms": 29.0,
    "db_read_ms": 9.1,
    "limiter_wait_ms": 0.0,
    "llm_ttft_ms": 578.2,
    "db_write_ms": 8.0,
    "llm_total_ms": null,
    "total_ms": 617.7,
    "client_first_byte_ms": 681.8,
    "client_total_ms": 714.7
  },
  {
    "db_write_pre_ms": 14.1,
    "db_read_ms": 23.2,
    "limiter_wait_ms": 0.0,
    "llm_ttft_ms": 372.7,
    "db_write_ms": 8.4,
    "llm_total_ms": null,
    "total_ms": 416.9,
    "client_first_byte_ms": 503.4,
    "client_total_ms": 504.4
  },
  {
    "db_write_pre_ms": 12.6,
    "db_read_ms": 5.8,
    "limiter_wait_ms": 0.0,
    "llm_ttft_ms": 347.8,
    "db_write_ms": 8.4,
    "llm_total_ms": null,
    "total_ms": 392.9,
    "client_first_byte_ms": 439.9,
    "client_total_ms": 485.2
  }
]
```
