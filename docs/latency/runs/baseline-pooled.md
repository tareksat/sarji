# Latency run — baseline-pooled

- Target: `https://sarjy-tarek.duckdns.org`
- Endpoint: `POST /api/chat` (non-streaming)
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
| `db_read_ms` | 14.6 | 46.8 | 21.3 | 12.0 | 50.4 |
| `db_write_pre_ms` | — | — | — | — | — |
| `limiter_wait_ms` | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| `llm_ttft_ms` | — | — | — | — | — |
| `llm_total_ms` | 360.9 | 529.6 | 351.7 | 161.1 | 595.2 |
| `db_write_ms` | 8.1 | 18.9 | 9.7 | 5.3 | 22.0 |
| `total_ms` | 396.5 | 567.3 | 384.2 | 191.1 | 616.1 |
| `client_first_byte_ms` | 511.2 | 689.1 | 498.4 | 291.5 | 741.7 |
| `client_total_ms` | 511.2 | 689.1 | 498.4 | 291.5 | 741.7 |

Raw per-run values (all 26 iterations):

```json
[
  {
    "db_read_ms": 13.0,
    "limiter_wait_ms": 0.0,
    "llm_total_ms": 381.2,
    "db_write_ms": 8.3,
    "llm_ttft_ms": null,
    "total_ms": 403.7,
    "client_first_byte_ms": 492.9,
    "client_total_ms": 492.9
  },
  {
    "db_read_ms": 15.6,
    "limiter_wait_ms": 0.0,
    "llm_total_ms": 360.9,
    "db_write_ms": 7.8,
    "llm_ttft_ms": null,
    "total_ms": 385.5,
    "client_first_byte_ms": 487.2,
    "client_total_ms": 487.2
  },
  {
    "db_read_ms": 14.1,
    "limiter_wait_ms": 0.0,
    "llm_total_ms": 161.1,
    "db_write_ms": 22.0,
    "llm_ttft_ms": null,
    "total_ms": 198.3,
    "client_first_byte_ms": 299.2,
    "client_total_ms": 299.2
  },
  {
    "db_read_ms": 30.6,
    "limiter_wait_ms": 0.0,
    "llm_total_ms": 356.7,
    "db_write_ms": 7.7,
    "llm_ttft_ms": null,
    "total_ms": 396.5,
    "client_first_byte_ms": 522.3,
    "client_total_ms": 522.3
  },
  {
    "db_read_ms": 13.4,
    "limiter_wait_ms": 0.0,
    "llm_total_ms": 417.6,
    "db_write_ms": 9.1,
    "llm_ttft_ms": null,
    "total_ms": 441.3,
    "client_first_byte_ms": 533.4,
    "client_total_ms": 533.4
  },
  {
    "db_read_ms": 23.7,
    "limiter_wait_ms": 0.0,
    "llm_total_ms": 436.1,
    "db_write_ms": 6.9,
    "llm_ttft_ms": null,
    "total_ms": 468.4,
    "client_first_byte_ms": 609.8,
    "client_total_ms": 609.8
  },
  {
    "db_read_ms": 13.8,
    "limiter_wait_ms": 0.0,
    "llm_total_ms": 384.5,
    "db_write_ms": 10.1,
    "llm_ttft_ms": null,
    "total_ms": 410.1,
    "client_first_byte_ms": 524.1,
    "client_total_ms": 524.1
  },
  {
    "db_read_ms": 17.4,
    "limiter_wait_ms": 0.0,
    "llm_total_ms": 529.6,
    "db_write_ms": 18.6,
    "llm_ttft_ms": null,
    "total_ms": 567.3,
    "client_first_byte_ms": 689.1,
    "client_total_ms": 689.1
  },
  {
    "db_read_ms": 46.8,
    "limiter_wait_ms": 0.0,
    "llm_total_ms": 347.6,
    "db_write_ms": 13.0,
    "llm_ttft_ms": null,
    "total_ms": 409.0,
    "client_first_byte_ms": 538.9,
    "client_total_ms": 538.9
  },
  {
    "db_read_ms": 35.1,
    "limiter_wait_ms": 0.0,
    "llm_total_ms": 388.2,
    "db_write_ms": 8.1,
    "llm_ttft_ms": null,
    "total_ms": 433.2,
    "client_first_byte_ms": 537.3,
    "client_total_ms": 537.3
  },
  {
    "db_read_ms": 14.6,
    "limiter_wait_ms": 0.0,
    "llm_total_ms": 395.5,
    "db_write_ms": 7.8,
    "llm_ttft_ms": null,
    "total_ms": 419.2,
    "client_first_byte_ms": 539.5,
    "client_total_ms": 539.5
  },
  {
    "db_read_ms": 18.9,
    "limiter_wait_ms": 0.0,
    "llm_total_ms": 368.2,
    "db_write_ms": 7.6,
    "llm_ttft_ms": null,
    "total_ms": 396.1,
    "client_first_byte_ms": 511.2,
    "client_total_ms": 511.2
  },
  {
    "db_read_ms": 13.7,
    "limiter_wait_ms": 0.0,
    "llm_total_ms": 341.0,
    "db_write_ms": 6.5,
    "llm_ttft_ms": null,
    "total_ms": 362.3,
    "client_first_byte_ms": 561.7,
    "client_total_ms": 561.7
  },
  {
    "db_read_ms": 14.6,
    "limiter_wait_ms": 0.0,
    "llm_total_ms": 169.8,
    "db_write_ms": 5.4,
    "llm_ttft_ms": null,
    "total_ms": 191.1,
    "client_first_byte_ms": 291.5,
    "client_total_ms": 291.5
  },
  {
    "db_read_ms": 12.0,
    "limiter_wait_ms": 0.0,
    "llm_total_ms": 237.0,
    "db_write_ms": 7.8,
    "llm_ttft_ms": null,
    "total_ms": 258.1,
    "client_first_byte_ms": 358.8,
    "client_total_ms": 358.8
  },
  {
    "db_read_ms": 12.3,
    "limiter_wait_ms": 0.0,
    "llm_total_ms": 595.2,
    "db_write_ms": 7.4,
    "llm_ttft_ms": null,
    "total_ms": 616.1,
    "client_first_byte_ms": 741.7,
    "client_total_ms": 741.7
  },
  {
    "db_read_ms": 13.2,
    "limiter_wait_ms": 0.0,
    "llm_total_ms": 323.6,
    "db_write_ms": 8.7,
    "llm_ttft_ms": null,
    "total_ms": 346.8,
    "client_first_byte_ms": 446.1,
    "client_total_ms": 446.1
  },
  {
    "db_read_ms": 13.3,
    "limiter_wait_ms": 0.0,
    "llm_total_ms": 399.0,
    "db_write_ms": 8.5,
    "llm_ttft_ms": null,
    "total_ms": 422.0,
    "client_first_byte_ms": 514.1,
    "client_total_ms": 514.1
  },
  {
    "db_read_ms": 13.3,
    "limiter_wait_ms": 0.0,
    "llm_total_ms": 323.7,
    "db_write_ms": 6.3,
    "llm_ttft_ms": null,
    "total_ms": 344.4,
    "client_first_byte_ms": 453.9,
    "client_total_ms": 453.9
  },
  {
    "db_read_ms": 12.3,
    "limiter_wait_ms": 0.0,
    "llm_total_ms": 284.2,
    "db_write_ms": 5.3,
    "llm_ttft_ms": null,
    "total_ms": 303.0,
    "client_first_byte_ms": 410.3,
    "client_total_ms": 410.3
  },
  {
    "db_read_ms": 13.5,
    "limiter_wait_ms": 0.0,
    "llm_total_ms": 303.9,
    "db_write_ms": 6.0,
    "llm_ttft_ms": null,
    "total_ms": 324.7,
    "client_first_byte_ms": 445.5,
    "client_total_ms": 445.5
  },
  {
    "db_read_ms": 46.5,
    "limiter_wait_ms": 0.0,
    "llm_total_ms": 202.1,
    "db_write_ms": 10.3,
    "llm_ttft_ms": null,
    "total_ms": 261.2,
    "client_first_byte_ms": 362.1,
    "client_total_ms": 362.1
  },
  {
    "db_read_ms": 22.4,
    "limiter_wait_ms": 0.0,
    "llm_total_ms": 470.3,
    "db_write_ms": 12.7,
    "llm_ttft_ms": null,
    "total_ms": 506.7,
    "client_first_byte_ms": 620.8,
    "client_total_ms": 620.8
  },
  {
    "db_read_ms": 22.7,
    "limiter_wait_ms": 0.0,
    "llm_total_ms": 362.7,
    "db_write_ms": 10.9,
    "llm_ttft_ms": null,
    "total_ms": 397.6,
    "client_first_byte_ms": 500.7,
    "client_total_ms": 500.7
  },
  {
    "db_read_ms": 37.6,
    "limiter_wait_ms": 0.0,
    "llm_total_ms": 362.6,
    "db_write_ms": 11.7,
    "llm_ttft_ms": null,
    "total_ms": 413.7,
    "client_first_byte_ms": 522.3,
    "client_total_ms": 522.3
  },
  {
    "db_read_ms": 50.4,
    "limiter_wait_ms": 0.0,
    "llm_total_ms": 241.4,
    "db_write_ms": 18.9,
    "llm_ttft_ms": null,
    "total_ms": 312.2,
    "client_first_byte_ms": 445.2,
    "client_total_ms": 445.2
  }
]
```
