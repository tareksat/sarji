# Latency run — streaming-long (pooled)

- Target: `https://sarjy-tarek.duckdns.org`
- Prompt: `Describe Paris in exactly four sentences.`
- Pooled from: `streaming-long-1` (5), `streaming-long-2` (5)
- Iterations: 10 (warm-ups discarded per invocation)

| Segment | p50 (ms) | p95 (ms) |
|---|---:|---:|
| `db_read_ms` | 5.7 | 6.9 |
| `db_write_pre_ms` | 13.6 | 16.0 |
| `limiter_wait_ms` | 0.0 | 0.0 |
| `llm_ttft_ms` | 750.3 | 2165.0 |
| `llm_total_ms` | — | — |
| `db_write_ms` | 9.0 | 12.4 |
| `total_ms` | 1042.7 | 2444.2 |
| `client_first_byte_ms` | 860.6 | 2266.8 |
| `client_total_ms` | 1158.8 | 2546.1 |

Raw per-run values:

```json
[
  {
    "db_write_pre_ms": 15.2,
    "db_read_ms": 5.7,
    "limiter_wait_ms": 0.0,
    "llm_ttft_ms": 750.3,
    "db_write_ms": 9.0,
    "llm_total_ms": null,
    "total_ms": 1042.7,
    "client_first_byte_ms": 860.6,
    "client_total_ms": 1158.8
  },
  {
    "db_write_pre_ms": 13.5,
    "db_read_ms": 5.7,
    "limiter_wait_ms": 0.0,
    "llm_ttft_ms": 990.9,
    "db_write_ms": 8.6,
    "llm_total_ms": null,
    "total_ms": 1298.0,
    "client_first_byte_ms": 1109.6,
    "client_total_ms": 1397.1
  },
  {
    "db_write_pre_ms": 13.6,
    "db_read_ms": 5.0,
    "limiter_wait_ms": 0.0,
    "llm_ttft_ms": 165.0,
    "db_write_ms": 8.3,
    "llm_total_ms": null,
    "total_ms": 426.0,
    "client_first_byte_ms": 260.2,
    "client_total_ms": 563.9
  },
  {
    "db_write_pre_ms": 12.6,
    "db_read_ms": 4.8,
    "limiter_wait_ms": 0.0,
    "llm_ttft_ms": 377.9,
    "db_write_ms": 9.5,
    "llm_total_ms": null,
    "total_ms": 628.2,
    "client_first_byte_ms": 482.3,
    "client_total_ms": 804.1
  },
  {
    "db_write_pre_ms": 13.2,
    "db_read_ms": 5.3,
    "limiter_wait_ms": 0.0,
    "llm_ttft_ms": 332.3,
    "db_write_ms": 9.0,
    "llm_total_ms": null,
    "total_ms": 594.3,
    "client_first_byte_ms": 422.6,
    "client_total_ms": 685.2
  },
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
