# Latency run — tool-mcp-2

- Target: `https://sarjy-tarek.duckdns.org`
- Prompt: `What's the weather in Riyadh right now?`
- Iterations: 5 (warm-up discarded)

| Segment | p50 (ms) | p95 (ms) |
|---|---:|---:|
| `db_read_ms` | 6.2 | 7.2 |
| `db_write_pre_ms` | 15.7 | 32.4 |
| `limiter_wait_ms` | 0.0 | 0.0 |
| `llm_ttft_ms` | 909.8 | 2779.5 |
| `llm_total_ms` | — | — |
| `db_write_ms` | 8.1 | 9.0 |
| `total_ms` | 984.6 | 2844.5 |
| `client_first_byte_ms` | 1003.3 | 2884.1 |
| `client_total_ms` | 1127.1 | 3022.7 |

Raw per-run values:

```json
[
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
