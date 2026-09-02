# Latency run — streaming-pooled

- Target: `https://sarjy-tarek.duckdns.org`
- Endpoint: `POST /api/chat/stream`
- Prompt: `In one sentence, what is the capital of France?`
- Iterations: 26, pooled from four harness invocations (each one's warm-up discarded)
- Date: 2026-09-02 — three invocations of 5 + 8 + 8 taken around 10:24–10:28, alternating with
  the other condition and spaced 60 s apart, plus a fourth 5-iteration re-measurement at 11:01
  recorded in the sibling run file. Alternating the conditions rather than running each in one
  block keeps drift in the provider's own response time from loading onto one of them; the
  fourth invocation is the exception, taken after both conditions rather than between them.
  The deployed 20-per-minute token bucket never engaged (`limiter_wait_ms` is 0.0 in all 26).

At N=26 the p95 is a real order statistic rather than the maximum observation, so mean, min and max
are reported alongside it.

| Segment | p50 (ms) | p95 (ms) | mean (ms) | min (ms) | max (ms) |
|---|---:|---:|---:|---:|---:|
| `db_read_ms` | 5.8 | 18.1 | 7.6 | 4.7 | 18.5 |
| `db_write_pre_ms` | 13.9 | 24.6 | 15.2 | 9.4 | 44.6 |
| `limiter_wait_ms` | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| `llm_ttft_ms` | 375.0 | 1097.0 | 432.2 | 150.6 | 1421.3 |
| `llm_total_ms` | — | — | — | — | — |
| `db_write_ms` | 8.2 | 29.2 | 10.9 | 5.7 | 29.9 |
| `total_ms` | 425.1 | 1136.2 | 486.9 | 189.2 | 1473.0 |
| `client_first_byte_ms` | 483.1 | 1200.1 | 543.7 | 247.1 | 1544.3 |
| `client_total_ms` | 523.7 | 1260.9 | 594.3 | 281.0 | 1570.5 |

Raw per-run values (all 26 iterations):

```json
[
  {
    "db_write_pre_ms": 17.6,
    "db_read_ms": 7.1,
    "limiter_wait_ms": 0.0,
    "llm_ttft_ms": 193.6,
    "db_write_ms": 9.4,
    "llm_total_ms": null,
    "total_ms": 239.3,
    "client_first_byte_ms": 337.4,
    "client_total_ms": 340.0
  },
  {
    "db_write_pre_ms": 13.9,
    "db_read_ms": 18.1,
    "limiter_wait_ms": 0.0,
    "llm_ttft_ms": 206.8,
    "db_write_ms": 10.3,
    "llm_total_ms": null,
    "total_ms": 256.7,
    "client_first_byte_ms": 315.3,
    "client_total_ms": 360.8
  },
  {
    "db_write_pre_ms": 17.2,
    "db_read_ms": 6.6,
    "limiter_wait_ms": 0.0,
    "llm_ttft_ms": 404.2,
    "db_write_ms": 16.9,
    "llm_total_ms": null,
    "total_ms": 466.1,
    "client_first_byte_ms": 507.7,
    "client_total_ms": 557.8
  },
  {
    "db_write_pre_ms": 16.0,
    "db_read_ms": 9.6,
    "limiter_wait_ms": 0.0,
    "llm_ttft_ms": 150.6,
    "db_write_ms": 7.8,
    "llm_total_ms": null,
    "total_ms": 189.2,
    "client_first_byte_ms": 247.1,
    "client_total_ms": 281.0
  },
  {
    "db_write_pre_ms": 15.2,
    "db_read_ms": 5.8,
    "limiter_wait_ms": 0.0,
    "llm_ttft_ms": 392.6,
    "db_write_ms": 29.2,
    "llm_total_ms": null,
    "total_ms": 455.6,
    "client_first_byte_ms": 511.9,
    "client_total_ms": 548.5
  },
  {
    "db_write_pre_ms": 11.9,
    "db_read_ms": 5.4,
    "limiter_wait_ms": 0.0,
    "llm_ttft_ms": 358.5,
    "db_write_ms": 8.8,
    "llm_total_ms": null,
    "total_ms": 398.9,
    "client_first_byte_ms": 459.5,
    "client_total_ms": 499.2
  },
  {
    "db_write_pre_ms": 10.9,
    "db_read_ms": 5.3,
    "limiter_wait_ms": 0.0,
    "llm_ttft_ms": 225.6,
    "db_write_ms": 7.0,
    "llm_total_ms": null,
    "total_ms": 267.7,
    "client_first_byte_ms": 321.5,
    "client_total_ms": 378.9
  },
  {
    "db_write_pre_ms": 14.7,
    "db_read_ms": 6.4,
    "limiter_wait_ms": 0.0,
    "llm_ttft_ms": 361.6,
    "db_write_ms": 6.7,
    "llm_total_ms": null,
    "total_ms": 411.8,
    "client_first_byte_ms": 466.6,
    "client_total_ms": 516.7
  },
  {
    "db_write_pre_ms": 9.4,
    "db_read_ms": 5.2,
    "limiter_wait_ms": 0.0,
    "llm_ttft_ms": 700.4,
    "db_write_ms": 6.8,
    "llm_total_ms": null,
    "total_ms": 736.0,
    "client_first_byte_ms": 821.2,
    "client_total_ms": 848.5
  },
  {
    "db_write_pre_ms": 11.7,
    "db_read_ms": 5.1,
    "limiter_wait_ms": 0.0,
    "llm_ttft_ms": 375.0,
    "db_write_ms": 5.7,
    "llm_total_ms": null,
    "total_ms": 445.6,
    "client_first_byte_ms": 475.1,
    "client_total_ms": 641.7
  },
  {
    "db_write_pre_ms": 12.9,
    "db_read_ms": 4.7,
    "limiter_wait_ms": 0.0,
    "llm_ttft_ms": 589.2,
    "db_write_ms": 7.2,
    "llm_total_ms": null,
    "total_ms": 632.9,
    "client_first_byte_ms": 701.3,
    "client_total_ms": 761.2
  },
  {
    "db_write_pre_ms": 12.1,
    "db_read_ms": 5.8,
    "limiter_wait_ms": 0.0,
    "llm_ttft_ms": 191.9,
    "db_write_ms": 8.2,
    "llm_total_ms": null,
    "total_ms": 393.3,
    "client_first_byte_ms": 375.0,
    "client_total_ms": 499.2
  },
  {
    "db_write_pre_ms": 12.3,
    "db_read_ms": 5.2,
    "limiter_wait_ms": 0.0,
    "llm_ttft_ms": 363.6,
    "db_write_ms": 8.5,
    "llm_total_ms": null,
    "total_ms": 402.8,
    "client_first_byte_ms": 483.1,
    "client_total_ms": 502.2
  },
  {
    "db_write_pre_ms": 14.8,
    "db_read_ms": 7.3,
    "limiter_wait_ms": 0.0,
    "llm_ttft_ms": 250.6,
    "db_write_ms": 8.2,
    "llm_total_ms": null,
    "total_ms": 292.5,
    "client_first_byte_ms": 354.1,
    "client_total_ms": 400.9
  },
  {
    "db_write_pre_ms": 12.1,
    "db_read_ms": 5.1,
    "limiter_wait_ms": 0.0,
    "llm_ttft_ms": 168.5,
    "db_write_ms": 7.2,
    "llm_total_ms": null,
    "total_ms": 203.9,
    "client_first_byte_ms": 316.9,
    "client_total_ms": 347.2
  },
  {
    "db_write_pre_ms": 10.8,
    "db_read_ms": 5.5,
    "limiter_wait_ms": 0.0,
    "llm_ttft_ms": 382.1,
    "db_write_ms": 8.3,
    "llm_total_ms": null,
    "total_ms": 425.1,
    "client_first_byte_ms": 487.2,
    "client_total_ms": 523.7
  },
  {
    "db_write_pre_ms": 12.3,
    "db_read_ms": 7.7,
    "limiter_wait_ms": 0.0,
    "llm_ttft_ms": 1097.0,
    "db_write_ms": 7.2,
    "llm_total_ms": null,
    "total_ms": 1136.2,
    "client_first_byte_ms": 1200.1,
    "client_total_ms": 1260.9
  },
  {
    "db_write_pre_ms": 12.4,
    "db_read_ms": 5.0,
    "limiter_wait_ms": 0.0,
    "llm_ttft_ms": 387.6,
    "db_write_ms": 7.9,
    "llm_total_ms": null,
    "total_ms": 429.8,
    "client_first_byte_ms": 491.4,
    "client_total_ms": 529.5
  },
  {
    "db_write_pre_ms": 11.2,
    "db_read_ms": 5.0,
    "limiter_wait_ms": 0.0,
    "llm_ttft_ms": 613.7,
    "db_write_ms": 5.9,
    "llm_total_ms": null,
    "total_ms": 651.3,
    "client_first_byte_ms": 707.6,
    "client_total_ms": 742.5
  },
  {
    "db_write_pre_ms": 14.3,
    "db_read_ms": 5.3,
    "limiter_wait_ms": 0.0,
    "llm_ttft_ms": 341.8,
    "db_write_ms": 7.5,
    "llm_total_ms": null,
    "total_ms": 386.0,
    "client_first_byte_ms": 448.4,
    "client_total_ms": 481.4
  },
  {
    "db_write_pre_ms": 11.0,
    "db_read_ms": 5.5,
    "limiter_wait_ms": 0.0,
    "llm_ttft_ms": 358.1,
    "db_write_ms": 7.0,
    "llm_total_ms": null,
    "total_ms": 415.4,
    "client_first_byte_ms": 458.0,
    "client_total_ms": 514.5
  },
  {
    "db_write_pre_ms": 19.2,
    "db_read_ms": 8.2,
    "limiter_wait_ms": 0.0,
    "llm_ttft_ms": 1421.3,
    "db_write_ms": 13.7,
    "llm_total_ms": null,
    "total_ms": 1473.0,
    "client_first_byte_ms": 1544.3,
    "client_total_ms": 1570.5
  },
  {
    "db_write_pre_ms": 14.2,
    "db_read_ms": 18.5,
    "limiter_wait_ms": 0.0,
    "llm_ttft_ms": 537.3,
    "db_write_ms": 12.1,
    "llm_total_ms": null,
    "total_ms": 601.8,
    "client_first_byte_ms": 631.9,
    "client_total_ms": 702.9
  },
  {
    "db_write_pre_ms": 18.9,
    "db_read_ms": 10.8,
    "limiter_wait_ms": 0.0,
    "llm_ttft_ms": 462.5,
    "db_write_ms": 18.5,
    "llm_total_ms": null,
    "total_ms": 512.2,
    "client_first_byte_ms": 561.6,
    "client_total_ms": 605.1
  },
  {
    "db_write_pre_ms": 24.6,
    "db_read_ms": 12.2,
    "limiter_wait_ms": 0.0,
    "llm_ttft_ms": 440.7,
    "db_write_ms": 29.9,
    "llm_total_ms": null,
    "total_ms": 524.2,
    "client_first_byte_ms": 545.7,
    "client_total_ms": 626.9
  },
  {
    "db_write_pre_ms": 44.6,
    "db_read_ms": 12.0,
    "limiter_wait_ms": 0.0,
    "llm_ttft_ms": 263.7,
    "db_write_ms": 17.3,
    "llm_total_ms": null,
    "total_ms": 312.0,
    "client_first_byte_ms": 365.7,
    "client_total_ms": 410.2
  }
]
```
