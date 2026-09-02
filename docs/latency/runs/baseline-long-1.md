# Latency run — baseline-long-1

- Target: `https://sarjy-tarek.duckdns.org`
- Prompt: `Describe Paris in exactly four sentences.`
- Iterations: 5 (warm-up discarded)

| Segment | p50 (ms) | p95 (ms) |
|---|---:|---:|
| `db_read_ms` | 15.1 | 15.6 |
| `db_write_pre_ms` | — | — |
| `limiter_wait_ms` | 0.0 | 0.0 |
| `llm_ttft_ms` | — | — |
| `llm_total_ms` | 591.2 | 820.9 |
| `db_write_ms` | 7.1 | 9.9 |
| `total_ms` | 614.6 | 845.1 |
| `client_first_byte_ms` | 722.8 | 948.7 |
| `client_total_ms` | 722.8 | 948.7 |

Raw per-run values:

```json
[
  {
    "db_read_ms": 15.6,
    "limiter_wait_ms": 0.0,
    "llm_total_ms": 569.4,
    "db_write_ms": 6.3,
    "llm_ttft_ms": null,
    "total_ms": 592.3,
    "client_first_byte_ms": 681.0,
    "client_total_ms": 681.0
  },
  {
    "db_read_ms": 13.9,
    "limiter_wait_ms": 0.0,
    "llm_total_ms": 551.4,
    "db_write_ms": 9.9,
    "llm_ttft_ms": null,
    "total_ms": 576.4,
    "client_first_byte_ms": 674.3,
    "client_total_ms": 674.3
  },
  {
    "db_read_ms": 15.2,
    "limiter_wait_ms": 0.0,
    "llm_total_ms": 617.2,
    "db_write_ms": 6.6,
    "llm_ttft_ms": null,
    "total_ms": 640.1,
    "client_first_byte_ms": 750.8,
    "client_total_ms": 750.8
  },
  {
    "db_read_ms": 15.1,
    "limiter_wait_ms": 0.0,
    "llm_total_ms": 591.2,
    "db_write_ms": 7.1,
    "llm_ttft_ms": null,
    "total_ms": 614.6,
    "client_first_byte_ms": 722.8,
    "client_total_ms": 722.8
  },
  {
    "db_read_ms": 13.7,
    "limiter_wait_ms": 0.0,
    "llm_total_ms": 820.9,
    "db_write_ms": 9.2,
    "llm_ttft_ms": null,
    "total_ms": 845.1,
    "client_first_byte_ms": 948.7,
    "client_total_ms": 948.7
  }
]
```
