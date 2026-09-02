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
| `db_write_pre_ms` | n/a | n/a | n/a | 13.9 | 24.6 | 15.2 |
| `limiter_wait_ms` | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| `llm_ttft_ms` | n/a | n/a | n/a | 375.0 | 1097.0 | 432.2 |
| `llm_total_ms` | 362.6 | 529.6 | 351.7 | n/a | n/a | n/a |
| `db_write_ms` | 8.3 | 18.9 | 9.7 | 8.2 | 29.2 | 10.9 |
| `total_ms` | 397.6 | 567.3 | 384.2 | 425.1 | 1136.2 | 486.9 |
| `client_first_byte_ms` | 514.1 | 689.1 | 498.4 | 483.1 | 1200.1 | 543.7 |

### Table 2 — long reply, non-streamed against streamed (N=10 each)

`POST /api/chat` against `POST /api/chat/stream`, four-sentence prompt. Sources:
[`runs/baseline-long-pooled.md`](runs/baseline-long-pooled.md),
[`runs/streaming-long-pooled.md`](runs/streaming-long-pooled.md).

| Segment | non-streamed p50 | p95 | mean | streamed p50 | p95 | mean |
|---|---:|---:|---:|---:|---:|---:|
| `db_read_ms` | 19.8 | 57.2 | 23.5 | 5.7 | 6.9 | 5.6 |
| `db_write_pre_ms` | n/a | n/a | n/a | 13.6 | 16.0 | 13.9 |
| `limiter_wait_ms` | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| `llm_ttft_ms` | n/a | n/a | n/a | 750.3 | 2165.0 | 775.1 |
| `llm_total_ms` | 613.5 | 1077.9 | 681.2 | n/a | n/a | n/a |
| `db_write_ms` | 9.3 | 26.9 | 10.7 | 9.0 | 12.4 | 9.0 |
| `total_ms` | 640.1 | 1122.3 | 716.6 | 1042.7 | 2444.2 | 1061.2 |
| `client_first_byte_ms` | 750.8 | 1272.9 | 831.9 | 860.6 | 2266.8 | 878.2 |
| `client_total_ms` | 750.8 | 1272.9 | 831.9 | 1158.8 | 2546.1 | 1178.8 |

### Table 3 — provider, Groq against Gemini, streamed, short reply (N=10 each)

`POST /api/chat/stream` with `LLM_MODEL` set to `groq-oss` against `gemini-flash`. Sources:
[`runs/provider-groq-pooled.md`](runs/provider-groq-pooled.md),
[`runs/provider-gemini-pooled.md`](runs/provider-gemini-pooled.md).

| Segment | Groq p50 | p95 | mean | Gemini p50 | p95 | mean |
|---|---:|---:|---:|---:|---:|---:|
| `db_read_ms` | 6.3 | 23.2 | 9.6 | 6.3 | 10.9 | 6.5 |
| `db_write_pre_ms` | 15.0 | 29.0 | 16.6 | 13.9 | 15.5 | 13.8 |
| `llm_ttft_ms` | 450.0 | 714.5 | 465.6 | 1676.9 | 3211.9 | 1831.3 |
| `db_write_ms` | 8.4 | 9.3 | 8.1 | 7.9 | 33.2 | 10.2 |
| `total_ms` | 505.6 | 761.2 | 509.7 | 1687.6 | 3249.3 | 1845.3 |
| `client_first_byte_ms` | 552.5 | 824.5 | 577.2 | 1772.0 | 3313.9 | 1930.5 |
| `client_total_ms` | 599.9 | 875.3 | 611.8 | 1775.7 | 3342.6 | 1942.0 |

### Table 4 — tool transport, MCP against local, streamed, weather prompt (N=10 each)

`POST /api/chat/stream` with `USE_LOCAL_WEATHER_TOOL` false against true. Sources:
[`runs/tool-mcp-pooled.md`](runs/tool-mcp-pooled.md),
[`runs/tool-local-pooled.md`](runs/tool-local-pooled.md).

| Segment | MCP p50 | p95 | mean | local p50 | p95 | mean |
|---|---:|---:|---:|---:|---:|---:|
| `db_read_ms` | 6.1 | 10.0 | 6.4 | 5.8 | 11.8 | 7.0 |
| `db_write_pre_ms` | 14.0 | 32.4 | 16.8 | 13.2 | 17.6 | 13.6 |
| `llm_ttft_ms` | 950.1 | 2779.5 | 1121.7 | 1255.9 | 2305.0 | 1258.8 |
| `db_write_ms` | 8.2 | 9.0 | 8.1 | 8.6 | 11.1 | 8.6 |
| `total_ms` | 1022.9 | 2844.5 | 1190.0 | 1359.1 | 2367.9 | 1338.4 |
| `client_first_byte_ms` | 1055.4 | 2884.1 | 1229.0 | 1383.8 | 2416.7 | 1365.4 |
| `client_total_ms` | 1152.0 | 3022.7 | 1328.7 | 1489.4 | 2492.1 | 1489.3 |

The per-call MCP cost is the difference in `llm_ttft_ms` p50, because the tool round-trip sits
between the model's tool call and its first text token. That difference is **−305.8 ms**: MCP was
*faster* than the in-process tool, not slower. See the analysis below — the sign is not the point,
the magnitude is.

## Analysis

**Short reply (Table 1)**

- **The model is the turn.** `llm_total_ms` is 362.6 ms of a 397.6 ms non-streamed turn at
  p50 — 91%. It is also all the variance: 161 ms to 595 ms across 26 turns.
- **Streaming does not move time to first byte, and there is no generation tail to overlap.**
  Its `client_first_byte_ms` mean is 45.2 ms *worse*, and a two-sided permutation test
  (20,000 reshuffles) puts that at p = 0.46 — no detectable difference either way. `llm_ttft_ms`
  at p50 is 375.0 ms, *above* the non-streamed `llm_total_ms` p50 of 362.6 ms: on a one-sentence
  reply the first token and the whole completion arrive at nearly the same moment, so there is
  nothing for the streamed path to start work under.
- **The database is ~6% and nets to zero.** Parallel reads are real — `db_read_ms` is 13.7 ms
  lower on the streamed path, p < 0.0001 — but the streamed path's extra pre-LLM commit hands
  it back: 22.8 ms of Postgres before the model against 21.3 ms (means).
- **Network, TLS and the Caddy hop cost 99–117 ms.** That is `client_total_ms` minus
  `total_ms` at p50: 116.5 ms non-streamed, 98.6 ms streamed. `client_total_ms` is the right
  mark on both sides — on the streamed path `total_ms` runs past the first byte to the end of
  generation, so subtracting it from `client_first_byte_ms` understates the hop. The streamed
  `client_total_ms` p50 of 523.7 ms is in [`runs/streaming-pooled.md`](runs/streaming-pooled.md);
  on the non-streamed path `client_total_ms` equals `client_first_byte_ms`. No code in this
  repo touches it.

**Long reply (Table 2) — the streaming mechanism's fair test**

- **It did not pay.** `client_first_byte_ms` p50 went *up* 109.8 ms on the streamed path
  (860.6 against 750.8), and the mean agrees in direction (878.2 against 831.9). A four-sentence
  reply is where the overlap should have shown, and on this evidence it did not.
- **`llm_ttft_ms` still sits above `llm_total_ms`, and by more than before.** 750.3 ms to first
  token against 613.5 ms for the whole non-streamed completion at p50 — a 136.8 ms gap, wider
  than the 12.4 ms gap on the short prompt. Whatever the streamed path pays for its first token,
  the longer reply did not shrink it.
- **The streamed set is bimodal, and N=10 cannot separate the two conditions.** Five of the ten
  streamed first bytes landed between 260.2 ms and 482.3 ms — below *every* non-streamed turn,
  whose fastest was 658.4 ms — and the other five between 860.6 ms and 2266.8 ms, so the median
  falls in the upper cluster. The honest reading is that streaming did not reduce first byte in
  this measurement, not that it cannot; a larger sample is what would settle it.
- **Streaming still costs on `client_total_ms`.** 1158.8 ms against 750.8 ms at p50 — the whole
  reply arrives 408.0 ms later. Only the first token can arrive earlier, and here it did not.

**Provider (Table 3)**

- **Groq is the faster provider by a wide margin.** `llm_ttft_ms` p50 is 450.0 ms against
  Gemini's 1676.9 ms — 1226.9 ms lower, a factor of 3.7. This is the largest single effect
  measured anywhere in this study, and the only one that clears run-to-run noise without argument.
- **The tail separates them more than the median does.** p95 is 714.5 ms against 3211.9 ms — a
  2497.4 ms gap, twice the median gap. On this prompt Gemini is not just slower, it is slower
  *and* less predictable.
- **It is not an outlier artifact.** Each condition's two invocations agree: Groq's per-invocation
  `llm_ttft_ms` p50 is 401.2 ms and 450.0 ms, Gemini's 1657.7 ms and 1676.9 ms.
- **Everything outside the model is identical between them.** `db_read_ms` p50 is 6.3 ms in both
  columns; `db_write_pre_ms`, `db_write_ms` and the network hop are within a few ms. The provider
  choice moves the turn; nothing else about the provider run does.

**Tool transport (Table 4)**

- **The measurement did not find an MCP tax — it found the opposite sign at p50.** MCP's
  `llm_ttft_ms` p50 is 950.1 ms against local's 1255.9 ms: MCP is 305.8 ms *faster*, 24% below
  local, and the means agree in direction (1121.7 against 1258.8). Going out over Streamable HTTP
  to a separate container beat calling the same function in process.
- **The ranking reverses at p95.** MCP 2779.5 ms against local 2305.0 ms. Each pooled set carries
  one high outlier — a single 2779.5 ms MCP turn and a single 2305.0 ms local turn out of ten —
  and at N=10 those single observations *are* the p95.
- **The conclusion is about magnitude, not sign.** Whatever the MCP hop costs is smaller than the
  turn-to-turn spread of the model's own time to first token on a tool call, which runs from
  758.7 ms to 2305.0 ms on the local path alone. A 305.8 ms swing in MCP's favour is not evidence
  that the transport is free; it is evidence that N=10 on this prompt cannot resolve it in either
  direction. There is no measured cost here to optimize away.

**Across Tables 2 to 4**

- **The limiter never engaged.** `limiter_wait_ms` is 0.0 in all 112 turns behind this report.
- **The network hop is stable at 88–130 ms.** `client_total_ms` minus `total_ms` at p50:
  116.1 ms (streamed long), 94.3 ms (Groq), 88.1 ms (Gemini), 129.1 ms (MCP), 130.3 ms (local).
  It does not vary with prompt, provider or transport.

## Recommendations

1. **Keep streaming for the UI, not for latency.** Neither reply length showed a first-byte win
   (Tables 1 and 2), and the long reply cost 408.0 ms on `client_total_ms` p50. Its value is that
   the UI can start speaking at the first sentence; that is a user-experience mechanism and should
   be justified as one, not as a latency optimization.
2. **Provider choice is the only lever with a measured effect. Stay on Groq.** 1226.9 ms at p50
   (Table 3) is larger than every other difference in this report combined. Future latency work
   should start by re-running Table 3 against candidate models, not by touching this code.
3. **Do not spend anything on the MCP hop.** Keeping the MCP session warm, caching the tool list
   or co-locating the server would each claw back part of a cost that Table 4 could not detect at
   all — MCP was 305.8 ms *faster* at p50. None of it is justified on this evidence. Revisit only
   if a run with a real sample size (N≥30, interleaved) shows a consistent gap.
4. **Stop optimizing the database and the limiter.** Both are below the noise floor of the model's
   own spread, and `limiter_wait_ms` is 0.0 in all 112 turns. Keep the limiter as tail protection
   under concurrent load — but that case needs a concurrency test this harness does not have.
5. **Treat the 88–130 ms network overhead as a placement decision, not a code one.** It moves by
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
