# Sarjy backend latency — benchmark summary

Quick-reference pull of every headline number from [`REPORT.md`](REPORT.md). Full method, per-segment tables, analysis and caveats live there — this file is the numbers only, for fast lookup. Every figure below is copied verbatim from the committed run files in [`runs/`](runs/); none are retyped from memory.

- Target: `https://sarjy-tarek.duckdns.org` (deployed, network+TLS included in every number)
- Commit measured: `050dec0` · Date: 2026-09-02
- Percentiles recomputed 2026-09-02 after an off-by-one was fixed in the harness's `percentile`; p50s moved on the even-N pooled tables, p95s and means did not. See the note under Method in [`REPORT.md`](REPORT.md).

## 1. Short reply — non-streamed vs streamed (N=26 each)

Prompt: *"In one sentence, what is the capital of France?"*

| Segment | non-streamed p50 | p95 | streamed p50 | p95 |
|---|---:|---:|---:|---:|
| `llm_total_ms` / `llm_ttft_ms` | 360.9 | 529.6 | 363.6 | 1097.0 |
| `db_read_ms` | 14.6 | 46.8 | 5.8 | 18.1 |
| `total_ms` | 396.5 | 567.3 | 415.4 | 1136.2 |
| `client_first_byte_ms` | 511.2 | 689.1 | 475.1 | 1200.1 |

**Result:** streaming did not move time-to-first-byte (p=0.46, no detectable difference). The model call is 91% of the turn.

## 2. Long reply — non-streamed vs streamed (N=10 each)

Prompt: *"Describe Paris in exactly four sentences."*

| Segment | non-streamed p50 | p95 | streamed p50 | p95 |
|---|---:|---:|---:|---:|
| `llm_total_ms` / `llm_ttft_ms` | 591.2 | 1077.9 | 377.9 | 2165.0 |
| `client_first_byte_ms` | 723.7 | 1272.9 | 482.3 | 2266.8 |
| `client_total_ms` | 723.7 | 1272.9 | 873.1 | 2546.1 |

**Result:** streaming's fair test, and the p50 cannot settle it: the ten streamed first bytes split five and five around a 378ms gap, so the median lands in the gap and reports whichever cluster the rank convention picks. The statistics that are stable both say the win did not appear — the mean is 46.3ms **worse** streamed (878.2 vs 831.9) and p95 is 994ms worse (2266.8 vs 1272.9). The whole reply still arrived 149.4ms later at p50 on `client_total_ms`, 346.9ms later on the mean.

## 3. Provider — Groq vs Gemini, streamed short reply (N=10 each)

`LLM_MODEL` = `groq-oss` vs `gemini-flash`.

| Segment | Groq p50 | p95 | Gemini p50 | p95 |
|---|---:|---:|---:|---:|
| `llm_ttft_ms` | 401.2 | 714.5 | 1668.2 | 3211.9 |
| `client_first_byte_ms` | 535.7 | 824.5 | 1763.8 | 3313.9 |

**Result:** Groq is ~4.2x faster at p50 (1267.0ms gap), and the tail gap is even wider (2497.4ms at p95). The largest, clearest effect in the whole study.

## 4. Tool transport — MCP vs local, streamed weather prompt (N=10 each)

`USE_LOCAL_WEATHER_TOOL` = `false` (MCP, shipped) vs `true` (local).

| Segment | MCP p50 | p95 | local p50 | p95 |
|---|---:|---:|---:|---:|
| `llm_ttft_ms` | 910.3 | 2779.5 | 954.2 | 2305.0 |
| `client_first_byte_ms` | 1049.7 | 2884.1 | 1051.9 | 2416.7 |

**Result:** MCP was **faster** than the in-process local tool at p50 by 43.9ms (5% lower) — opposite of the assumed "transport tax," and small enough to be noise. Ranking reverses at p95 (one outlier per set); N=10 cannot resolve the true direction, but there is no measured cost to optimize away.

## Headline takeaways

1. **The model call dominates everything.** ~91% of a short-reply turn; database and rate-limiter costs net to zero.
2. **Streaming is a UX mechanism, not a latency win.** No first-byte improvement on either prompt length that survives scrutiny — the long reply's p50 is decided by a bimodal split, and its mean and p95 both favour the non-streamed path; total delivery time got slower.
3. **Provider choice is the one lever that matters.** Groq vs Gemini is a 4.2x gap — bigger than every other measured difference combined.
4. **MCP transport cost is unmeasurable at this sample size, and possibly negative.** Do not spend engineering effort clawing back an MCP "tax" — none was found.
5. **Network/TLS/Caddy overhead is stable at 91–143ms** regardless of prompt, provider, or transport — a hosting/placement decision, not a code one.

Full analysis, caveats, and per-segment breakdowns: [`REPORT.md`](REPORT.md). Raw and pooled data behind every cell: [`runs/`](runs/).
