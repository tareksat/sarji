# Latency run — provider-gemini-2

- Target: `https://sarjy-tarek.duckdns.org`
- Prompt: `In one sentence, what is the capital of France?`
- Iterations: 5 (warm-up discarded)

| Segment | p50 (ms) | p95 (ms) |
|---|---:|---:|
| `db_read_ms` | 5.7 | 6.4 |
| `db_write_pre_ms` | 12.8 | 14.6 |
| `limiter_wait_ms` | 0.0 | 0.0 |
| `llm_ttft_ms` | 1676.9 | 2357.3 |
| `llm_total_ms` | — | — |
| `db_write_ms` | 7.1 | 9.4 |
| `total_ms` | 1687.6 | 2370.3 |
| `client_first_byte_ms` | 1772.0 | 2453.1 |
| `client_total_ms` | 1775.7 | 2466.4 |

Raw per-run values:

```json
[
  {
    "db_write_pre_ms": 11.9,
    "db_read_ms": 5.5,
    "limiter_wait_ms": 0.0,
    "llm_ttft_ms": 1668.2,
    "db_write_ms": 6.6,
    "llm_total_ms": null,
    "total_ms": 1678.5,
    "client_first_byte_ms": 1762.5,
    "client_total_ms": 1772.2
  },
  {
    "db_write_pre_ms": 12.8,
    "db_read_ms": 5.5,
    "limiter_wait_ms": 0.0,
    "llm_ttft_ms": 1676.9,
    "db_write_ms": 6.9,
    "llm_total_ms": null,
    "total_ms": 1687.6,
    "client_first_byte_ms": 1772.0,
    "client_total_ms": 1775.7
  },
  {
    "db_write_pre_ms": 12.7,
    "db_read_ms": 5.7,
    "limiter_wait_ms": 0.0,
    "llm_ttft_ms": 1827.8,
    "db_write_ms": 7.9,
    "llm_total_ms": null,
    "total_ms": 1839.6,
    "client_first_byte_ms": 1918.3,
    "client_total_ms": 1927.0
  },
  {
    "db_write_pre_ms": 13.9,
    "db_read_ms": 6.3,
    "limiter_wait_ms": 0.0,
    "llm_ttft_ms": 2357.3,
    "db_write_ms": 9.4,
    "llm_total_ms": null,
    "total_ms": 2370.3,
    "client_first_byte_ms": 2453.1,
    "client_total_ms": 2466.4
  },
  {
    "db_write_pre_ms": 14.6,
    "db_read_ms": 6.4,
    "limiter_wait_ms": 0.0,
    "llm_ttft_ms": 1368.5,
    "db_write_ms": 7.1,
    "llm_total_ms": null,
    "total_ms": 1379.2,
    "client_first_byte_ms": 1463.5,
    "client_total_ms": 1480.4
  }
]
```
