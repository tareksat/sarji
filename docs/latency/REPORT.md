# Sarjy backend latency — measurements, analysis, recommendations

**Scope.** The backend segment of a turn: from the request reaching the API to the first usable byte leaving it, plus the harness's own view of that from outside the deployment. The browser's speech endpointing before the request and its synthesis after the reply are outside the code and outside this study; the UI's live waterfall shows their share on every turn. Reasoning in [`../PRD.md`](../PRD.md), section 5.

- Target: `https://sarjy-tarek.duckdns.org` (deployed; network and TLS are in every number)
- Model: `groq-oss`, the LiteLLM alias for `groq/openai/gpt-oss-120b`, read back from the backend container before each run. The provider comparison flips this to `gemini-flash` for its second half.
- Date: 2026-09-02 · Commit: `050dec0`
- Samples: stated per table. Server-side spans plus the harness's first-byte and last-byte marks.

## Method

Three fixed prompts, a fresh session per turn so history length stays constant, warm-up discarded. Numbers come from `sarjy-backend/scripts/measure.py`; because the deployed limiter allows 20 requests a minute and a 429 aborts a run, each condition is pooled from invocations spaced 60 s apart — five turns each for Tables 2 to 4, pooled with `scripts/pool_runs.py`, and 5 + 8 + 8 + 5 for Table 1, whose pooled files were assembled by hand before that script existed. Raw invocations and pooled tables are in [`runs/`](runs/).

| Prompt | Used by |
|---|---|
| `In one sentence, what is the capital of France?` | short-reply comparison, provider comparison |
| `Describe Paris in exactly four sentences.` | long-reply comparison |
| `What's the weather in Riyadh right now?` | tool transport comparison |

The city is in the weather prompt because the harness mints a fresh user per invocation, so nothing is remembered.

**All percentiles in this report were recomputed on 2026-09-02 from the same raw observations, after a
defect was found in the harness's `percentile`.** It computed `round(p/100*n + 0.5) - 1`, which lands
one rank high, and — through banker's rounding — did so only for *even* sample counts, so p50s from
runs of different lengths were not comparable with each other. It is now nearest-rank,
`ceil(p/100*n) - 1`, with a unit test. Only p50s moved, and only on the pooled even-N tables: every
per-invocation table, every p95, and every mean, min and max is unchanged, because means and extremes
do not go through that function and the N=5 invocations were already correct. Two readings changed
with the numbers and are called out where they appear — the Table 2 first-byte comparison and the
size of the Table 4 tool-transport difference. No measurement was re-run; the raw per-turn values in
[`runs/`](runs/) are the originals.

## Measurements

`n/a` is structural throughout, not a measured zero: the non-streamed path never emits
`llm_ttft_ms` or `db_write_pre_ms`, the streamed path never emits `llm_total_ms`.

### Table 1 — short reply, non-streamed against streamed (N=26 each)

`POST /api/chat` against `POST /api/chat/stream`. Sources:
[`runs/baseline-pooled.md`](runs/baseline-pooled.md),
[`runs/streaming-pooled.md`](runs/streaming-pooled.md).

| Segment | non-streamed p50 | p95 | mean | streamed p50 | p95 | mean |
|---|---:|---:|---:|---:|---:|---:|
| `db_read_ms` | 14.6 | 46.8 | 21.3 | 5.8 | 18.1 | 7.6 |
| `db_write_pre_ms` | n/a | n/a | n/a | 12.9 | 24.6 | 15.2 |
| `limiter_wait_ms` | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| `llm_ttft_ms` | n/a | n/a | n/a | 363.6 | 1097.0 | 432.2 |
| `llm_total_ms` | 360.9 | 529.6 | 351.7 | n/a | n/a | n/a |
| `db_write_ms` | 8.1 | 18.9 | 9.7 | 8.2 | 29.2 | 10.9 |
| `total_ms` | 396.5 | 567.3 | 384.2 | 415.4 | 1136.2 | 486.9 |
| `client_first_byte_ms` | 511.2 | 689.1 | 498.4 | 475.1 | 1200.1 | 543.7 |

### Table 2 — long reply, non-streamed against streamed (N=10 each)

`POST /api/chat` against `POST /api/chat/stream`, four-sentence prompt. Sources:
[`runs/baseline-long-pooled.md`](runs/baseline-long-pooled.md),
[`runs/streaming-long-pooled.md`](runs/streaming-long-pooled.md).

| Segment | non-streamed p50 | p95 | mean | streamed p50 | p95 | mean |
|---|---:|---:|---:|---:|---:|---:|
| `db_read_ms` | 15.6 | 57.2 | 23.5 | 5.5 | 6.9 | 5.6 |
| `db_write_pre_ms` | n/a | n/a | n/a | 13.5 | 16.0 | 13.9 |
| `limiter_wait_ms` | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| `llm_ttft_ms` | n/a | n/a | n/a | 377.9 | 2165.0 | 775.1 |
| `llm_total_ms` | 591.2 | 1077.9 | 681.2 | n/a | n/a | n/a |
| `db_write_ms` | 9.2 | 26.9 | 10.7 | 8.6 | 12.4 | 9.0 |
| `total_ms` | 614.6 | 1122.3 | 716.6 | 743.2 | 2444.2 | 1061.2 |
| `client_first_byte_ms` | 723.7 | 1272.9 | 831.9 | 482.3 | 2266.8 | 878.2 |
| `client_total_ms` | 723.7 | 1272.9 | 831.9 | 873.1 | 2546.1 | 1178.8 |

### Table 3 — provider, Groq against Gemini, streamed, short reply (N=10 each)

`POST /api/chat/stream` with `LLM_MODEL` set to `groq-oss` against `gemini-flash`. Sources:
[`runs/provider-groq-pooled.md`](runs/provider-groq-pooled.md),
[`runs/provider-gemini-pooled.md`](runs/provider-gemini-pooled.md).

| Segment | Groq p50 | p95 | mean | Gemini p50 | p95 | mean |
|---|---:|---:|---:|---:|---:|---:|
| `db_read_ms` | 6.2 | 23.2 | 9.6 | 5.9 | 10.9 | 6.5 |
| `db_write_pre_ms` | 14.5 | 29.0 | 16.6 | 13.7 | 15.5 | 13.8 |
| `llm_ttft_ms` | 401.2 | 714.5 | 465.6 | 1668.2 | 3211.9 | 1831.3 |
| `db_write_ms` | 8.0 | 9.3 | 8.1 | 7.4 | 33.2 | 10.2 |
| `total_ms` | 445.0 | 761.2 | 509.7 | 1678.5 | 3249.3 | 1845.3 |
| `client_first_byte_ms` | 535.7 | 824.5 | 577.2 | 1763.8 | 3313.9 | 1930.5 |
| `client_total_ms` | 536.2 | 875.3 | 611.8 | 1774.7 | 3342.6 | 1942.0 |

### Table 4 — tool transport, MCP against local, streamed, weather prompt (N=10 each)

`POST /api/chat/stream` with `USE_LOCAL_WEATHER_TOOL` false against true. Sources:
[`runs/tool-mcp-pooled.md`](runs/tool-mcp-pooled.md),
[`runs/tool-local-pooled.md`](runs/tool-local-pooled.md).

| Segment | MCP p50 | p95 | mean | local p50 | p95 | mean |
|---|---:|---:|---:|---:|---:|---:|
| `db_read_ms` | 6.0 | 10.0 | 6.4 | 5.7 | 11.8 | 7.0 |
| `db_write_pre_ms` | 13.3 | 32.4 | 16.8 | 13.1 | 17.6 | 13.6 |
| `llm_ttft_ms` | 910.3 | 2779.5 | 1121.7 | 954.2 | 2305.0 | 1258.8 |
| `db_write_ms` | 8.1 | 9.0 | 8.1 | 8.5 | 11.1 | 8.6 |
| `total_ms` | 984.6 | 2844.5 | 1190.0 | 1022.8 | 2367.9 | 1338.4 |
| `client_first_byte_ms` | 1049.7 | 2884.1 | 1229.0 | 1051.9 | 2416.7 | 1365.4 |
| `client_total_ms` | 1127.1 | 3022.7 | 1328.7 | 1136.7 | 2492.1 | 1489.3 |

The per-call MCP cost is the difference in `llm_ttft_ms` p50, because the tool round-trip sits
between the model's tool call and its first text token. That difference is **-43.9 ms**: MCP was
*faster* than the in-process tool, not slower. See the analysis below — the sign is not the point,
the magnitude is.

## Analysis

**Short reply (Table 1)**

- **The model is the turn.** `llm_total_ms` is 360.9 ms of a 396.5 ms non-streamed turn at
  p50 — 91%. It is also all the variance: 161 ms to 595 ms across 26 turns.
- **Streaming does not move time to first byte, and there is no generation tail to overlap.**
  Its `client_first_byte_ms` mean is 45.2 ms *worse*, and a two-sided permutation test
  (20,000 reshuffles) puts that at p = 0.46 — no detectable difference either way. `llm_ttft_ms`
  at p50 is 363.6 ms, *above* the non-streamed `llm_total_ms` p50 of 360.9 ms: on a one-sentence
  reply the first token and the whole completion arrive at nearly the same moment, so there is
  nothing for the streamed path to start work under.
- **The database is ~6% and nets to zero.** Parallel reads are real — `db_read_ms` is 13.7 ms
  lower on the streamed path, p < 0.0001 — but the streamed path's extra pre-LLM commit hands
  it back: 22.8 ms of Postgres before the model against 21.3 ms (means).
- **Network, TLS and the Caddy hop cost 101–115 ms.** That is `client_total_ms` minus
  `total_ms` at p50: 114.7 ms non-streamed, 101.3 ms streamed. `client_total_ms` is the right
  mark on both sides — on the streamed path `total_ms` runs past the first byte to the end of
  generation, so subtracting it from `client_first_byte_ms` understates the hop. The streamed
  `client_total_ms` p50 of 516.7 ms is in [`runs/streaming-pooled.md`](runs/streaming-pooled.md);
  on the non-streamed path `client_total_ms` equals `client_first_byte_ms`. No code in this
  repo touches it.

**Long reply (Table 2) — the streaming mechanism's fair test**

- **The p50 first-byte comparison on this table is not usable, in either direction.** The ten
  streamed observations split exactly five and five around a 378 ms gap: five between 260.2 ms and
  482.3 ms — below *every* non-streamed turn, whose fastest was 658.4 ms — and five between
  860.6 ms and 2266.8 ms. At N=10 the median falls precisely in that gap, so which cluster the p50
  reports is decided by the rank convention rather than by the data. It read 860.6 ms under the
  harness's old off-by-one and reads 482.3 ms under the corrected nearest-rank. Neither number
  means anything, and an earlier draft's "first byte got worse by 109.8 ms" was reporting that
  arbitrariness rather than a result.
- **On the statistics that survive, streaming still did not reduce first byte.** The mean is
  46.3 ms *worse* on the streamed path (878.2 against 831.9), and p95 is 994 ms worse (2266.8
  against 1272.9). Neither goes through the percentile function's defect. A four-sentence reply is
  where the overlap should have shown; on the summaries that hold up, it did not. That is the same
  conclusion the earlier draft reached, now resting on evidence that supports it.
- **`llm_ttft_ms` is bimodal for the same reason, and carries the same caveat.** Its p50 reads
  377.9 ms against 591.2 ms for the whole non-streamed completion, but its ten observations split
  five and five the same way (165.0–377.9 ms, then 750.3–2165.0 ms). The mean, 775.1 ms, is above
  the non-streamed `llm_total_ms` mean of 681.2 ms — so on the stable summary, the streamed path
  still reaches its first token later than the non-streamed path finishes entirely.
- **Streaming still costs on `client_total_ms`.** 873.1 ms against 723.7 ms at p50, and 1178.8 ms
  against 831.9 ms on the mean: the whole reply arrives 150–350 ms later depending on which you
  read. Only the first token can arrive earlier, and this sample cannot show that it did.

**Provider (Table 3)**

- **Groq is the faster provider by a wide margin.** `llm_ttft_ms` p50 is 401.2 ms against
  Gemini's 1668.2 ms — 1267.0 ms lower, a factor of 4.2. This is the largest single effect
  measured anywhere in this study, and the only one that clears run-to-run noise without argument.
- **The tail separates them more than the median does.** p95 is 714.5 ms against 3211.9 ms — a
  2497.4 ms gap, twice the median gap. On this prompt Gemini is not just slower, it is slower
  *and* less predictable.
- **It is not an outlier artifact.** Each condition's two invocations agree: Groq's per-invocation
  `llm_ttft_ms` p50 is 401.2 ms and 450.0 ms, Gemini's 1657.7 ms and 1676.9 ms. Those are N=5
  invocations, which the percentile defect never touched.
- **Everything outside the model is identical between them.** `db_read_ms` p50 is 6.2 ms against
  5.9 ms; `db_write_pre_ms`, `db_write_ms` and the network hop are within a few ms. The provider
  choice moves the turn; nothing else about the provider run does.

**Tool transport (Table 4)**

- **The measurement did not find an MCP tax — it found the opposite sign at p50.** MCP's
  `llm_ttft_ms` p50 is 910.3 ms against local's 954.2 ms: MCP is 43.9 ms *faster*, 5% below local,
  and the means agree in direction (1121.7 against 1258.8). Going out over Streamable HTTP to a
  separate container beat calling the same function in process. The gap read 305.8 ms before the
  percentile correction; the corrected figure is seven times smaller, which strengthens the
  conclusion below rather than weakening it.
- **The ranking reverses at p95.** MCP 2779.5 ms against local 2305.0 ms. Each pooled set carries
  one high outlier — a single 2779.5 ms MCP turn and a single 2305.0 ms local turn out of ten —
  and at N=10 those single observations *are* the p95.
- **The conclusion is about magnitude, not sign.** Whatever the MCP hop costs is smaller than the
  turn-to-turn spread of the model's own time to first token on a tool call, which runs from
  758.7 ms to 2305.0 ms on the local path alone. A 43.9 ms swing in MCP's favour is not evidence
  that the transport is free; it is evidence that N=10 on this prompt cannot resolve it in either
  direction. There is no measured cost here to optimize away.

**Across Tables 2 to 4**

- **The limiter never engaged.** `limiter_wait_ms` is 0.0 in all 112 turns behind this report.
- **The network hop is stable at 91–143 ms.** `client_total_ms` minus `total_ms` at p50:
  129.9 ms (streamed long), 91.2 ms (Groq), 96.2 ms (Gemini), 142.5 ms (MCP), 113.9 ms (local).
  It does not vary with prompt, provider or transport.

## Recommendations

1. **Keep streaming for the UI, not for latency.** Neither reply length showed a first-byte win on
   any statistic that survives scrutiny — Table 2's p50 is unusable, and its mean and p95 both
   favour the non-streamed path — and the long reply cost 149.4 ms on `client_total_ms` p50 and
   346.9 ms on the mean. Its value is that
   the UI can start speaking at the first sentence; that is a user-experience mechanism and should
   be justified as one, not as a latency optimization.
2. **Provider choice is the only lever with a measured effect. Stay on Groq.** 1267.0 ms at p50
   (Table 3) is larger than every other difference in this report combined. Future latency work
   should start by re-running Table 3 against candidate models, not by touching this code.
3. **Do not spend anything on the MCP hop.** Keeping the MCP session warm or co-locating the
   server would each claw back part of a cost that Table 4 could not detect at all — MCP was
   43.9 ms *faster* at p50. Neither is justified on this evidence. Revisit only if a run with a
   real sample size (N≥30, interleaved) shows a consistent gap. Note that `cache_tools_list` has
   since been turned on for the MCP client, for correctness reasons unrelated to this study; every
   number in Table 4 was taken with it off, so a re-run would not be comparable to these.
4. **Stop optimizing the database and the limiter.** Both are below the noise floor of the model's
   own spread, and `limiter_wait_ms` is 0.0 in all 112 turns. Keep the limiter as tail protection
   under concurrent load — but that case needs a concurrency test this harness does not have.
5. **Treat the 91–143 ms network overhead as a placement decision, not a code one.** It moves by
   moving the droplet, nothing else. Separately, raise `LLM_RATE_LIMIT_PER_MINUTE` on the droplet
   while benchmarking: the 20/min bucket is why every condition here is pooled from separate
   invocations, and it caps sample size more than time does.

## Caveats

- Every condition is pooled from invocations minutes apart, not one continuous stretch.
- No cold start is included in any number.
- Single-client, sequential turns throughout; nothing here says how the stack behaves under
  concurrency.
- The provider runs were taken on different minutes of the same day, not interleaved, so drift in
  either provider's own load is not controlled for.
- The weather prompt names the city, so the memory lookup is not inside the tool turn.
- The permutation tests behind the Table 1 bullets were run as a one-off, not from the harness.
  They were computed from the raw observations rather than from percentiles, so the percentile
  correction does not affect them.
- Percentiles are nearest-rank. At N=10 that makes the p50 the fifth of ten observations — a real
  observation rather than an interpolated one, and on a bimodal set like Table 2's, an arbitrary
  one. Where that matters it is said in the analysis rather than left for the reader to find.
