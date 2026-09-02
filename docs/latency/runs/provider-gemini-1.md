# Latency run — provider-gemini-1

- Target: `https://sarjy-tarek.duckdns.org`
- Prompt: `In one sentence, what is the capital of France?`
- Iterations: 5 (warm-up discarded)

| Segment | p50 (ms) | p95 (ms) |
|---|---:|---:|
| `db_read_ms` | 6.3 | 10.9 |
| `db_write_pre_ms` | 14.7 | 15.5 |
| `limiter_wait_ms` | 0.0 | 0.0 |
| `llm_ttft_ms` | 1657.7 | 3211.9 |
| `llm_total_ms` | — | — |
| `db_write_ms` | 9.0 | 33.2 |
| `total_ms` | 1668.6 | 3249.3 |
| `client_first_byte_ms` | 1763.8 | 3313.9 |
| `client_total_ms` | 1774.7 | 3342.6 |

Raw per-run values:

```json
[
  {
    "db_write_pre_ms": 15.5,
    "db_read_ms": 10.9,
    "limiter_wait_ms": 0.0,
    "llm_ttft_ms": 1730.5,
    "db_write_ms": 9.1,
    "llm_total_ms": null,
    "total_ms": 1743.8,
    "client_first_byte_ms": 1846.0,
    "client_total_ms": 1847.6
  },
  {
    "db_write_pre_ms": 13.7,
    "db_read_ms": 5.6,
    "limiter_wait_ms": 0.0,
    "llm_ttft_ms": 3211.9,
    "db_write_ms": 33.2,
    "llm_total_ms": null,
    "total_ms": 3249.3,
    "client_first_byte_ms": 3313.9,
    "client_total_ms": 3342.6
  },
  {
    "db_write_pre_ms": 14.7,
    "db_read_ms": 6.3,
    "limiter_wait_ms": 0.0,
    "llm_ttft_ms": 1518.2,
    "db_write_ms": 5.6,
    "llm_total_ms": null,
    "total_ms": 1527.2,
    "client_first_byte_ms": 1612.8,
    "client_total_ms": 1624.7
  },
  {
    "db_write_pre_ms": 12.4,
    "db_read_ms": 5.9,
    "limiter_wait_ms": 0.0,
    "llm_ttft_ms": 1296.3,
    "db_write_ms": 9.0,
    "llm_total_ms": null,
    "total_ms": 1309.4,
    "client_first_byte_ms": 1399.4,
    "client_total_ms": 1408.8
  },
  {
    "db_write_pre_ms": 15.5,
    "db_read_ms": 6.5,
    "limiter_wait_ms": 0.0,
    "llm_ttft_ms": 1657.7,
    "db_write_ms": 7.4,
    "llm_total_ms": null,
    "total_ms": 1668.6,
    "client_first_byte_ms": 1763.8,
    "client_total_ms": 1774.7
  }
]
```
