# Latency run — baseline-long (pooled)

- Target: `https://sarjy-tarek.duckdns.org`
- Prompt: `Describe Paris in exactly four sentences.`
- Pooled from: `baseline-long-1` (5), `baseline-long-2` (5)
- Iterations: 10 (warm-ups discarded per invocation)

| Segment | p50 (ms) | p95 (ms) |
|---|---:|---:|
| `db_read_ms` | 15.6 | 57.2 |
| `db_write_pre_ms` | — | — |
| `limiter_wait_ms` | 0.0 | 0.0 |
| `llm_ttft_ms` | — | — |
| `llm_total_ms` | 591.2 | 1077.9 |
| `db_write_ms` | 9.2 | 26.9 |
| `total_ms` | 614.6 | 1122.3 |
| `client_first_byte_ms` | 723.7 | 1272.9 |
| `client_total_ms` | 723.7 | 1272.9 |

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
  },
  {
    "db_read_ms": 33.7,
    "limiter_wait_ms": 0.0,
    "llm_total_ms": 1077.9,
    "db_write_ms": 9.3,
    "llm_ttft_ms": null,
    "total_ms": 1122.3,
    "client_first_byte_ms": 1272.9,
    "client_total_ms": 1272.9
  },
  {
    "db_read_ms": 19.8,
    "limiter_wait_ms": 0.0,
    "llm_total_ms": 943.7,
    "db_write_ms": 26.9,
    "llm_ttft_ms": null,
    "total_ms": 991.7,
    "client_first_byte_ms": 1132.5,
    "client_total_ms": 1132.5
  },
  {
    "db_read_ms": 57.2,
    "limiter_wait_ms": 0.0,
    "llm_total_ms": 462.7,
    "db_write_ms": 14.1,
    "llm_ttft_ms": null,
    "total_ms": 535.5,
    "client_first_byte_ms": 658.4,
    "client_total_ms": 658.4
  },
  {
    "db_read_ms": 23.5,
    "limiter_wait_ms": 0.0,
    "llm_total_ms": 563.8,
    "db_write_ms": 9.6,
    "llm_ttft_ms": null,
    "total_ms": 598.3,
    "client_first_byte_ms": 723.7,
    "client_total_ms": 723.7
  },
  {
    "db_read_ms": 27.4,
    "limiter_wait_ms": 0.0,
    "llm_total_ms": 613.5,
    "db_write_ms": 7.7,
    "llm_ttft_ms": null,
    "total_ms": 649.9,
    "client_first_byte_ms": 754.2,
    "client_total_ms": 754.2
  }
]
```
