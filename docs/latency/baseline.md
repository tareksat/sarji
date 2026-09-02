# Latency baseline — before any intervention

> **Status: not yet recorded.** The tables below are filled by running the
> harness against the deployed app. They cannot be reconstructed after the
> optimizations land, which is why this document exists before them.

- Target: `$SARJY_URL`
- Model: (the `LLM_MODEL` the deployed service was on)
- Date:
- Commit:

## How to record it

Server and network segments, from `sarjy-backend/`:

```bash
python scripts/measure.py --base-url $SARJY_URL --label baseline
```

Ten iterations of one fixed prompt, warm-up discarded. Writes
`docs/latency/runs/baseline.md`; paste its table below.

Client segments, by hand — the browser marks cannot be driven headlessly
without changing the thing being measured. In Chrome on `$SARJY_URL`, unmuted,
speak *"In one sentence, what is the capital of France?"* ten times, waiting for
each reply. Copy the `[sarjy-timing]` console lines into
`docs/latency/runs/baseline-client.txt`, then:

```bash
python scripts/summarize_client_timings.py ../docs/latency/runs/baseline-client.txt
```

## Server segments

| Segment | p50 (ms) | p95 (ms) |
|---|---:|---:|
| `db_read_ms` | | |
| `limiter_wait_ms` | | |
| `llm_ttft_ms` | — | — |
| `llm_total_ms` | | |
| `db_write_ms` | | |
| `total_ms` | | |
| `client_first_byte_ms` | | |
| `client_total_ms` | | |

`llm_ttft_ms` is empty by construction: the non-streaming `POST /api/chat` only
ever sees the whole response, so there is no first-token moment to measure. The
streaming endpoint is what fills that column in.

## Client segments (voice turns)

| Segment | p50 (ms) | p95 (ms) |
|---|---:|---:|
| `stt_tail_ms` | | |
| `first_byte_ms` | | |
| `reply_complete_ms` | | |
| `ttfa_ms` | | |

## What the numbers say

(One paragraph, written once the tables are filled: where the time sits before
anything is changed, and which segment dominates.)

Standing caveat, true regardless of what the numbers show: browser TTS is local,
so synthesis is not the bottleneck — the number being optimized is mostly the
LLM path plus the transcription tail.

## After

The before/after comparison lives in [`RESULTS.md`](RESULTS.md).
