# Latency — before and after

> **Status: awaiting numbers.** Every code change below is implemented and
> verified working; none of the measurements have been taken, because they must
> come from the deployed app rather than localhost. Fill this in by running the
> harness at each labelled step (see [`baseline.md`](baseline.md)).

- Target: `$SARJY_URL`
- Model:
- Date:

## Headline

| | p50 | p95 |
|---|---:|---:|
| Time to first audio, before | | |
| Time to first audio, after | | |

## Per segment

| Segment | Baseline p50 | Baseline p95 | Final p50 | Final p95 | Δ p50 |
|---|---:|---:|---:|---:|---:|
| Speech end → request sent | | | | | |
| Request → first byte | | | | | |
| Server: db read | | | | | |
| Server: limiter wait | | | | | |
| Server: model TTFT | | | | | |
| **Speech end → first audio (TTFA)** | | | | | |

## Per intervention

Each row is one labelled harness run. A null result is a row, not a failure to
hide — the interventions that bought nothing are the more interesting half.

| # | Intervention | Run label | Segment moved | Δ p50 | Verdict |
|---|---|---|---|---:|---|
| 1 | SSE streaming, speak at first sentence | `streaming` | TTFA | | |
| 2 | Cap the limiter's queue wait | `limiter-capped` | `limiter_wait_ms` | | |
| 3 | Parallel reads, deferred writes | `db-parallel` | `db_read_ms` | | |
| 4 | Bound memory facts and history | `prompt-trimmed`, `history-10` | model TTFT | | |
| 5 | STT endpointing | `stt-tuned-client` | `stt_tail_ms` | | |
| 6 | Warm the TTS voice list | first-turn TTFA | first-turn TTFA | | |
| 7 | Gemini vs Groq | `provider-gemini`, `provider-groq` | model TTFT | | |
| 8 | MCP vs local function tool | `tool-mcp`, `tool-local` | tool turn total | | |

## What did not help

(Written from the rows above once they are filled: which interventions moved
nothing, and why the hypothesis was wrong.)

## Caveats

- Browser TTS is local, so synthesis is not the bottleneck — the number being
  optimized is mostly the LLM path plus the transcription tail.
- The client-side segments come from ten hand-driven turns rather than a
  headless harness; driving the browser marks automatically would change the
  thing being measured.
- The voice-warming row has a smaller sample: it only shows up on a cold page,
  so it is five hard-reload-then-one-turn runs rather than ten consecutive
  turns.
- Capping the injected memory facts is a real tradeoff, not a free win: past the
  cap, the oldest facts stop being recalled.
- Every number comes from the deployed app. A cold start on a sleeping free-tier
  instance is not included in any of them.
