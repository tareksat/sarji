---
name: latency-test
description: Use when measuring Sarjy's latency - recording a baseline, re-measuring after a change, comparing providers or MCP-vs-local tool calls, or filling in the docs/latency tables
---

# Latency test

Drives `sarjy-backend/scripts/measure.py` against a running Sarjy and writes a
p50/p95 table per run. Backend only - the server's own spans plus the harness's
wall-clock marks; browser-side timings are out of scope. Default target:
`https://sarjy-tarek.duckdns.org` (override with an argument). Numbers come from the deployed app, not localhost -
network and cold start are part of the real number.

## Before any run

1. **Probe the target.** `curl -s <base-url>/api/health/full` - every dependency
   must report `ok`. A half-up stack produces numbers that look fine and mean
   nothing.
2. **Run from `sarjy-backend/`.** `--out-dir` defaults to `../docs/latency/runs`
   and is cwd-relative (`measure.py:112`).
3. **Use the backend venv.** `.venv/Scripts/python.exe` - `httpx` lives there,
   not necessarily on PATH.

## Commands

```
cd sarjy-backend
.venv/Scripts/python.exe scripts/measure.py --base-url <URL> --label <LABEL> --iterations 5 [--stream] [--prompt "..."]
```

| Label | Flags | Needs first |
|---|---|---|
| `baseline-N` | none (non-streaming `/api/chat`) | - |
| `streaming-N` | `--stream` | - |
| `baseline-long-N` / `streaming-long-N` | as above, `--prompt "Describe Paris in exactly four sentences."` | - |
| `provider-gemini-N` / `provider-groq-N` | `--stream` | `LLM_MODEL` changed on the droplet, `litellm` and `backend` recreated, model read back |
| `tool-mcp-N` / `tool-local-N` | `--stream --prompt "What's the weather in Riyadh right now?"` | `USE_LOCAL_WEATHER_TOOL` false / true on the droplet, `backend` recreated, setting read back |

`N` is the invocation number. Pool with `scripts/pool_runs.py --label <label> <label>-1 <label>-2`, which writes `<label>-pooled.md`; that is the file the report cites.

**A run whose config was not actually changed is not a comparison.** For the
`provider-*` and `tool-*` labels, confirm the deployed env changed and the
service restarted before running the second half, and revert afterwards. Stop
and say so rather than reporting a difference that is really noise.

## Iterations vs the token bucket

`app/core/rate_limiter.py` throttles to `llm_rate_limit_per_minute` (default 20)
and refuses to queue past `llm_rate_limit_max_wait_seconds` (default 2.0),
raising a 429 - and `measure.py:50` calls `raise_for_status()`, so a 429 aborts
the run mid-way. Each run costs `iterations + 1` requests (the warm-up is
discarded).

Keep back-to-back runs under the bucket, or wait ~60 s between them. At
`--iterations 5`, two runs are 12 calls against a 20-token bucket refilling at
0.33/s - safe. At the documented 10, two runs are 22 and will trip it.

If a run does abort: re-run that label after a pause rather than salvaging a
partial file, and report the failure with the response body verbatim.

## Reading the output

`percentile()` indexes a sorted list, so at N=5 p50 is the 3rd value and p95 is
the max - a single observation, not a tail estimate. Always state the sample
size next to a p95.

Segments empty **by construction** - a `-` here is not a measured zero:

| Endpoint | Empty | Populated |
|---|---|---|
| `/api/chat` (no `--stream`) | `llm_ttft_ms` | `llm_total_ms` |
| `/api/chat/stream` | `llm_total_ms` | `llm_ttft_ms`, `db_write_pre_ms` |

A run showing the opposite pattern means the wrong endpoint was hit. Check this
before writing anything down.

## Filling docs/latency

`docs/latency/REPORT.md` is the one document: header, method, one measurement
table, analysis, recommendations. Raw run files live beside it in
`docs/latency/runs/` and the report cites them - keep every run file, and keep the
report short enough to read in one sitting.

`measure.py` overwrites `<label>.md` on every run, so raw invocations carry a
`-N` suffix and `pool_runs.py` writes the only hand-safe file, `<label>-pooled.md`.
Its header names the invocations pooled and their sizes, and its `json` block
carries every raw row so the table can be recomputed.

Update the header metadata each time (target, date, `git rev-parse --short HEAD`,
and the deployed `LLM_MODEL`, which nothing exposes over HTTP: ask, or record it
as unverified), then the table rows the new runs cover. Numbers go in from the
run files, never copied out of the report's own prose. Analysis and
recommendations are rewritten when a run changes what they say - a bullet that
the latest data no longer supports gets removed, not hedged.

**Honesty boundary.** For the `streaming` row the comparison is
`client_first_byte_ms` - when the caller can start using the reply - not
`total_ms`. A null or negative result is a row to write, not a problem to hide,
and a segment the endpoint never emits is `n/a`, never 0.

## Common mistakes

| Mistake | Result |
|---|---|
| Running from the repo root | Run file lands in the wrong directory |
| System `python` instead of the venv | `ModuleNotFoundError: httpx` |
| 10 iterations for two back-to-back runs | 429 aborts the second run |
| Reading `-` as a measured zero | Reports a segment that was never sampled |
| Expecting a seeded memory on a weather run | `measure.py:115` mints a fresh random `user_id` per invocation, so nothing was remembered |
| Flipping `USE_LOCAL_WEATHER_TOOL` before it was in the compose `environment` block | The container never sees it; both halves measure MCP |
