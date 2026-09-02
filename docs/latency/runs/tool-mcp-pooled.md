# Latency run — tool-mcp (pooled)

- Target: `https://sarjy-tarek.duckdns.org`
- Prompt: `What's the weather in Riyadh right now?`
- Pooled from: `tool-mcp-1` (5), `tool-mcp-2` (5)
- Iterations: 10 (warm-ups discarded per invocation)

| Segment | p50 (ms) | p95 (ms) |
|---|---:|---:|
| `db_read_ms` | 6.1 | 10.0 |
| `db_write_pre_ms` | 14.0 | 32.4 |
| `limiter_wait_ms` | 0.0 | 0.0 |
| `llm_ttft_ms` | 950.1 | 2779.5 |
| `llm_total_ms` | — | — |
| `db_write_ms` | 8.2 | 9.0 |
| `total_ms` | 1022.9 | 2844.5 |
| `client_first_byte_ms` | 1055.4 | 2884.1 |
| `client_total_ms` | 1152.0 | 3022.7 |

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
  },
  {
    "db_write_pre_ms": 11.4,
    "db_read_ms": 5.3,
    "limiter_wait_ms": 0.0,
    "llm_ttft_ms": 2779.5,
    "db_write_ms": 8.1,
    "llm_total_ms": null,
    "total_ms": 2844.5,
    "client_first_byte_ms": 2884.1,
    "client_total_ms": 3022.7
  },
  {
    "db_write_pre_ms": 32.4,
    "db_read_ms": 6.5,
    "limiter_wait_ms": 0.0,
    "llm_ttft_ms": 950.1,
    "db_write_ms": 7.3,
    "llm_total_ms": null,
    "total_ms": 1022.9,
    "client_first_byte_ms": 1055.4,
    "client_total_ms": 1127.1
  },
  {
    "db_write_pre_ms": 13.3,
    "db_read_ms": 5.8,
    "limiter_wait_ms": 0.0,
    "llm_ttft_ms": 909.8,
    "db_write_ms": 9.0,
    "llm_total_ms": null,
    "total_ms": 984.6,
    "client_first_byte_ms": 1003.3,
    "client_total_ms": 1127.1
  },
  {
    "db_write_pre_ms": 15.7,
    "db_read_ms": 6.2,
    "limiter_wait_ms": 0.0,
    "llm_ttft_ms": 842.2,
    "db_write_ms": 8.8,
    "llm_total_ms": null,
    "total_ms": 900.2,
    "client_first_byte_ms": 931.0,
    "client_total_ms": 1010.8
  },
  {
    "db_write_pre_ms": 15.7,
    "db_read_ms": 7.2,
    "limiter_wait_ms": 0.0,
    "llm_ttft_ms": 863.7,
    "db_write_ms": 7.7,
    "llm_total_ms": null,
    "total_ms": 942.4,
    "client_first_byte_ms": 998.8,
    "client_total_ms": 1080.8
  }
]
```
