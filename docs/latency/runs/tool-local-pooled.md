# Latency run — tool-local (pooled)

- Target: `https://sarjy-tarek.duckdns.org`
- Prompt: `What's the weather in Riyadh right now?`
- Pooled from: `tool-local-1` (5), `tool-local-2` (5)
- Iterations: 10 (warm-ups discarded per invocation)

| Segment | p50 (ms) | p95 (ms) |
|---|---:|---:|
| `db_read_ms` | 5.8 | 11.8 |
| `db_write_pre_ms` | 13.2 | 17.6 |
| `limiter_wait_ms` | 0.0 | 0.0 |
| `llm_ttft_ms` | 1255.9 | 2305.0 |
| `llm_total_ms` | — | — |
| `db_write_ms` | 8.6 | 11.1 |
| `total_ms` | 1359.1 | 2367.9 |
| `client_first_byte_ms` | 1383.8 | 2416.7 |
| `client_total_ms` | 1489.4 | 2492.1 |

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
  },
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
