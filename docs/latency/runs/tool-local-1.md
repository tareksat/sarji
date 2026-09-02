# Latency run — tool-local-1

- Target: `https://sarjy-tarek.duckdns.org`
- Prompt: `What's the weather in Riyadh right now?`
- Iterations: 5 (warm-up discarded)

| Segment | p50 (ms) | p95 (ms) |
|---|---:|---:|
| `db_read_ms` | 5.7 | 7.9 |
| `db_write_pre_ms` | 12.5 | 13.7 |
| `limiter_wait_ms` | 0.0 | 0.0 |
| `llm_ttft_ms` | 1255.9 | 1654.0 |
| `llm_total_ms` | — | — |
| `db_write_ms` | 7.5 | 10.5 |
| `total_ms` | 1359.1 | 1706.8 |
| `client_first_byte_ms` | 1383.8 | 1762.9 |
| `client_total_ms` | 1489.4 | 1881.6 |

Raw per-run values:

```json
[
  {
    "db_write_pre_ms": 13.7,
    "db_read_ms": 7.9,
    "limiter_wait_ms": 0.0,
    "llm_ttft_ms": 1654.0,
    "db_write_ms": 7.4,
    "llm_total_ms": null,
    "total_ms": 1706.8,
    "client_first_byte_ms": 1762.9,
    "client_total_ms": 1881.6
  },
  {
    "db_write_pre_ms": 11.3,
    "db_read_ms": 5.4,
    "limiter_wait_ms": 0.0,
    "llm_ttft_ms": 793.2,
    "db_write_ms": 7.3,
    "llm_total_ms": null,
    "total_ms": 920.6,
    "client_first_byte_ms": 907.0,
    "client_total_ms": 1025.7
  },
  {
    "db_write_pre_ms": 12.5,
    "db_read_ms": 5.7,
    "limiter_wait_ms": 0.0,
    "llm_ttft_ms": 929.0,
    "db_write_ms": 10.5,
    "llm_total_ms": null,
    "total_ms": 1020.5,
    "client_first_byte_ms": 1036.9,
    "client_total_ms": 1128.0
  },
  {
    "db_write_pre_ms": 12.9,
    "db_read_ms": 5.7,
    "limiter_wait_ms": 0.0,
    "llm_ttft_ms": 1457.5,
    "db_write_ms": 8.5,
    "llm_total_ms": null,
    "total_ms": 1533.0,
    "client_first_byte_ms": 1567.2,
    "client_total_ms": 1658.4
  },
  {
    "db_write_pre_ms": 11.4,
    "db_read_ms": 5.8,
    "limiter_wait_ms": 0.0,
    "llm_ttft_ms": 1255.9,
    "db_write_ms": 7.5,
    "llm_total_ms": null,
    "total_ms": 1359.1,
    "client_first_byte_ms": 1383.8,
    "client_total_ms": 1489.4
  }
]
```
