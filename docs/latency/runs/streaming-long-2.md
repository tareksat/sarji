# Latency run — streaming-long-2

- Target: `https://sarjy-tarek.duckdns.org`
- Prompt: `Describe Paris in exactly four sentences.`
- Iterations: 5 (warm-up discarded)

| Segment | p50 (ms) | p95 (ms) |
|---|---:|---:|
| `db_read_ms` | 5.8 | 6.9 |
| `db_write_pre_ms` | 14.7 | 16.0 |
| `limiter_wait_ms` | 0.0 | 0.0 |
| `llm_ttft_ms` | 843.6 | 2165.0 |
| `llm_total_ms` | — | — |
| `db_write_ms` | 8.5 | 12.4 |
| `total_ms` | 1144.5 | 2444.2 |
| `client_first_byte_ms` | 938.6 | 2266.8 |
| `client_total_ms` | 1237.6 | 2546.1 |

Raw per-run values:

```json
[
  {
    "db_write_pre_ms": 13.2,
    "db_read_ms": 5.8,
    "limiter_wait_ms": 0.0,
    "llm_ttft_ms": 337.9,
    "db_write_ms": 8.5,
    "llm_total_ms": null,
    "total_ms": 582.7,
    "client_first_byte_ms": 440.1,
    "client_total_ms": 681.8
  },
  {
    "db_write_pre_ms": 15.0,
    "db_read_ms": 5.5,
    "limiter_wait_ms": 0.0,
    "llm_ttft_ms": 2165.0,
    "db_write_ms": 9.2,
    "llm_total_ms": null,
    "total_ms": 2444.2,
    "client_first_byte_ms": 2266.8,
    "client_total_ms": 2546.1
  },
  {
    "db_write_pre_ms": 12.5,
    "db_read_ms": 5.3,
    "limiter_wait_ms": 0.0,
    "llm_ttft_ms": 1412.0,
    "db_write_ms": 8.5,
    "llm_total_ms": null,
    "total_ms": 1708.5,
    "client_first_byte_ms": 1533.6,
    "client_total_ms": 1839.9
  },
  {
    "db_write_pre_ms": 14.7,
    "db_read_ms": 6.9,
    "limiter_wait_ms": 0.0,
    "llm_ttft_ms": 843.6,
    "db_write_ms": 12.4,
    "llm_total_ms": null,
    "total_ms": 1144.5,
    "client_first_byte_ms": 938.6,
    "client_total_ms": 1237.6
  },
  {
    "db_write_pre_ms": 16.0,
    "db_read_ms": 5.8,
    "limiter_wait_ms": 0.0,
    "llm_ttft_ms": 376.4,
    "db_write_ms": 7.0,
    "llm_total_ms": null,
    "total_ms": 743.2,
    "client_first_byte_ms": 467.2,
    "client_total_ms": 873.1
  }
]
```
