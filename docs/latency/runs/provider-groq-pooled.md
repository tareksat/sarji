# Latency run — provider-groq (pooled)

- Target: `https://sarjy-tarek.duckdns.org`
- Prompt: `In one sentence, what is the capital of France?`
- Pooled from: `provider-groq-1` (5), `provider-groq-2` (5)
- Iterations: 10 (warm-ups discarded per invocation)

| Segment | p50 (ms) | p95 (ms) |
|---|---:|---:|
| `db_read_ms` | 6.2 | 23.2 |
| `db_write_pre_ms` | 14.5 | 29.0 |
| `limiter_wait_ms` | 0.0 | 0.0 |
| `llm_ttft_ms` | 401.2 | 714.5 |
| `llm_total_ms` | — | — |
| `db_write_ms` | 8.0 | 9.3 |
| `total_ms` | 445.0 | 761.2 |
| `client_first_byte_ms` | 535.7 | 824.5 |
| `client_total_ms` | 536.2 | 875.3 |

Raw per-run values:

```json
[
  {
    "db_write_pre_ms": 26.3,
    "db_read_ms": 6.0,
    "limiter_wait_ms": 0.0,
    "llm_ttft_ms": 401.2,
    "db_write_ms": 7.8,
    "llm_total_ms": null,
    "total_ms": 445.0,
    "client_first_byte_ms": 535.7,
    "client_total_ms": 536.2
  },
  {
    "db_write_pre_ms": 12.4,
    "db_read_ms": 6.3,
    "limiter_wait_ms": 0.0,
    "llm_ttft_ms": 498.8,
    "db_write_ms": 9.3,
    "llm_total_ms": null,
    "total_ms": 541.6,
    "client_first_byte_ms": 650.6,
    "client_total_ms": 697.2
  },
  {
    "db_write_pre_ms": 15.0,
    "db_read_ms": 5.6,
    "limiter_wait_ms": 0.0,
    "llm_ttft_ms": 192.6,
    "db_write_ms": 8.4,
    "llm_total_ms": null,
    "total_ms": 236.0,
    "client_first_byte_ms": 291.5,
    "client_total_ms": 326.7
  },
  {
    "db_write_pre_ms": 12.0,
    "db_read_ms": 6.2,
    "limiter_wait_ms": 0.0,
    "llm_ttft_ms": 714.5,
    "db_write_ms": 7.0,
    "llm_total_ms": null,
    "total_ms": 759.0,
    "client_first_byte_ms": 824.5,
    "client_total_ms": 859.4
  },
  {
    "db_write_pre_ms": 15.0,
    "db_read_ms": 5.5,
    "limiter_wait_ms": 0.0,
    "llm_ttft_ms": 387.4,
    "db_write_ms": 7.3,
    "llm_total_ms": null,
    "total_ms": 420.9,
    "client_first_byte_ms": 487.5,
    "client_total_ms": 519.3
  },
  {
    "db_write_pre_ms": 15.2,
    "db_read_ms": 10.5,
    "limiter_wait_ms": 0.0,
    "llm_ttft_ms": 713.0,
    "db_write_ms": 9.0,
    "llm_total_ms": null,
    "total_ms": 761.2,
    "client_first_byte_ms": 805.1,
    "client_total_ms": 875.3
  },
  {
    "db_write_pre_ms": 14.5,
    "db_read_ms": 17.5,
    "limiter_wait_ms": 0.0,
    "llm_ttft_ms": 450.0,
    "db_write_ms": 7.8,
    "llm_total_ms": null,
    "total_ms": 505.6,
    "client_first_byte_ms": 552.5,
    "client_total_ms": 599.9
  },
  {
    "db_write_pre_ms": 29.0,
    "db_read_ms": 9.1,
    "limiter_wait_ms": 0.0,
    "llm_ttft_ms": 578.2,
    "db_write_ms": 8.0,
    "llm_total_ms": null,
    "total_ms": 617.7,
    "client_first_byte_ms": 681.8,
    "client_total_ms": 714.7
  },
  {
    "db_write_pre_ms": 14.1,
    "db_read_ms": 23.2,
    "limiter_wait_ms": 0.0,
    "llm_ttft_ms": 372.7,
    "db_write_ms": 8.4,
    "llm_total_ms": null,
    "total_ms": 416.9,
    "client_first_byte_ms": 503.4,
    "client_total_ms": 504.4
  },
  {
    "db_write_pre_ms": 12.6,
    "db_read_ms": 5.8,
    "limiter_wait_ms": 0.0,
    "llm_ttft_ms": 347.8,
    "db_write_ms": 8.4,
    "llm_total_ms": null,
    "total_ms": 392.9,
    "client_first_byte_ms": 439.9,
    "client_total_ms": 485.2
  }
]
```
