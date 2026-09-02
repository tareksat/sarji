# Latency run — provider-gemini (pooled)

- Target: `https://sarjy-tarek.duckdns.org`
- Prompt: `In one sentence, what is the capital of France?`
- Pooled from: `provider-gemini-1` (5), `provider-gemini-2` (5)
- Iterations: 10 (warm-ups discarded per invocation)

| Segment | p50 (ms) | p95 (ms) |
|---|---:|---:|
| `db_read_ms` | 6.3 | 10.9 |
| `db_write_pre_ms` | 13.9 | 15.5 |
| `limiter_wait_ms` | 0.0 | 0.0 |
| `llm_ttft_ms` | 1676.9 | 3211.9 |
| `llm_total_ms` | — | — |
| `db_write_ms` | 7.9 | 33.2 |
| `total_ms` | 1687.6 | 3249.3 |
| `client_first_byte_ms` | 1772.0 | 3313.9 |
| `client_total_ms` | 1775.7 | 3342.6 |

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
  },
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
