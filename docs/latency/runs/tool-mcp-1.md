# Latency run — tool-mcp-1

- Target: `https://sarjy-tarek.duckdns.org`
- Prompt: `What's the weather in Riyadh right now?`
- Iterations: 5 (warm-up discarded)

| Segment | p50 (ms) | p95 (ms) |
|---|---:|---:|
| `db_read_ms` | 6.0 | 10.0 |
| `db_write_pre_ms` | 12.3 | 29.9 |
| `limiter_wait_ms` | 0.0 | 0.0 |
| `llm_ttft_ms` | 1020.1 | 1058.0 |
| `llm_total_ms` | — | — |
| `db_write_ms` | 8.2 | 8.9 |
| `total_ms` | 1084.7 | 1125.0 |
| `client_first_byte_ms` | 1119.1 | 1157.3 |
| `client_total_ms` | 1229.9 | 1249.1 |

Raw per-run values:

```json
[
  {
    "db_write_pre_ms": 11.7,
    "db_read_ms": 6.1,
    "limiter_wait_ms": 0.0,
    "llm_ttft_ms": 910.3,
    "db_write_ms": 8.5,
    "llm_total_ms": null,
    "total_ms": 973.1,
    "client_first_byte_ms": 1049.7,
    "client_total_ms": 1152.0
  },
  {
    "db_write_pre_ms": 14.0,
    "db_read_ms": 5.5,
    "limiter_wait_ms": 0.0,
    "llm_ttft_ms": 1020.1,
    "db_write_ms": 6.3,
    "llm_total_ms": null,
    "total_ms": 1084.7,
    "client_first_byte_ms": 1119.1,
    "client_total_ms": 1229.9
  },
  {
    "db_write_pre_ms": 11.8,
    "db_read_ms": 5.7,
    "limiter_wait_ms": 0.0,
    "llm_ttft_ms": 846.6,
    "db_write_ms": 8.2,
    "llm_total_ms": null,
    "total_ms": 909.8,
    "client_first_byte_ms": 954.1,
    "client_total_ms": 1047.8
  },
  {
    "db_write_pre_ms": 12.3,
    "db_read_ms": 6.0,
    "limiter_wait_ms": 0.0,
    "llm_ttft_ms": 1037.0,
    "db_write_ms": 7.8,
    "llm_total_ms": null,
    "total_ms": 1113.1,
    "client_first_byte_ms": 1137.4,
    "client_total_ms": 1239.5
  },
  {
    "db_write_pre_ms": 29.9,
    "db_read_ms": 10.0,
    "limiter_wait_ms": 0.0,
    "llm_ttft_ms": 1058.0,
    "db_write_ms": 8.9,
    "llm_total_ms": null,
    "total_ms": 1125.0,
    "client_first_byte_ms": 1157.3,
    "client_total_ms": 1249.1
  }
]
```
