# Latency run — tool-local-2

- Target: `https://sarjy-tarek.duckdns.org`
- Prompt: `What's the weather in Riyadh right now?`
- Iterations: 5 (warm-up discarded)

| Segment | p50 (ms) | p95 (ms) |
|---|---:|---:|
| `db_read_ms` | 6.4 | 11.8 |
| `db_write_pre_ms` | 13.3 | 17.6 |
| `limiter_wait_ms` | 0.0 | 0.0 |
| `llm_ttft_ms` | 954.2 | 2305.0 |
| `llm_total_ms` | — | — |
| `db_write_ms` | 8.8 | 11.1 |
| `total_ms` | 1022.8 | 2367.9 |
| `client_first_byte_ms` | 1051.9 | 2416.7 |
| `client_total_ms` | 1136.7 | 2492.1 |

Raw per-run values:

```json
[
  {
    "db_write_pre_ms": 17.6,
    "db_read_ms": 11.8,
    "limiter_wait_ms": 0.0,
    "llm_ttft_ms": 1617.0,
    "db_write_ms": 8.8,
    "llm_total_ms": null,
    "total_ms": 1684.0,
    "client_first_byte_ms": 1708.8,
    "client_total_ms": 2073.7
  },
  {
    "db_write_pre_ms": 13.1,
    "db_read_ms": 5.5,
    "limiter_wait_ms": 0.0,
    "llm_ttft_ms": 758.7,
    "db_write_ms": 9.4,
    "llm_total_ms": null,
    "total_ms": 834.9,
    "client_first_byte_ms": 850.2,
    "client_total_ms": 932.0
  },
  {
    "db_write_pre_ms": 17.1,
    "db_read_ms": 10.5,
    "limiter_wait_ms": 0.0,
    "llm_ttft_ms": 2305.0,
    "db_write_ms": 11.1,
    "llm_total_ms": null,
    "total_ms": 2367.9,
    "client_first_byte_ms": 2416.7,
    "client_total_ms": 2492.1
  },
  {
    "db_write_pre_ms": 13.3,
    "db_read_ms": 5.7,
    "limiter_wait_ms": 0.0,
    "llm_ttft_ms": 954.2,
    "db_write_ms": 6.9,
    "llm_total_ms": null,
    "total_ms": 1022.8,
    "client_first_byte_ms": 1051.9,
    "client_total_ms": 1136.7
  },
  {
    "db_write_pre_ms": 13.2,
    "db_read_ms": 6.4,
    "limiter_wait_ms": 0.0,
    "llm_ttft_ms": 863.5,
    "db_write_ms": 8.6,
    "llm_total_ms": null,
    "total_ms": 934.0,
    "client_first_byte_ms": 968.7,
    "client_total_ms": 1075.4
  }
]
```
