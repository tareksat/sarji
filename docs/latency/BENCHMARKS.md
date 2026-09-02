# Sarjy backend latency — benchmark summary

Quick-reference pull of every headline number from [`REPORT.md`](REPORT.md). Full method, per-segment tables, analysis and caveats live there — this file is the numbers only, for fast lookup. Every figure below is copied verbatim from the committed run files in [`runs/`](runs/); none are retyped from memory.

- Target: `https://sarjy-tarek.duckdns.org` (deployed, network+TLS included in every number)
- Commit measured: `050dec0` · Date: 2026-09-02

## 1. Short reply — non-streamed vs streamed (N=26 each)

Prompt: *"In one sentence, what is the capital of France?"*

| Segment | non-streamed p50 | p95 | streamed p50 | p95 |
|---|---:|---:|---:|---:|
| `llm_total_ms` / `llm_ttft_ms` | 362.6 | 529.6 | 375.0 | 1097.0 |
| `db_read_ms` | 14.6 | 46.8 | 5.8 | 18.1 |
| `total_ms` | 397.6 | 567.3 | 425.1 | 1136.2 |
| `client_first_byte_ms` | 514.1 | 689.1 | 483.1 | 1200.1 |

**Result:** streaming did not move time-to-first-byte (p=0.46, no detectable difference). The model call is 91% of the turn.

## 2. Long reply — non-streamed vs streamed (N=10 each)

Prompt: *"Describe Paris in exactly four sentences."*

| Segment | non-streamed p50 | p95 | streamed p50 | p95 |
|---|---:|---:|---:|---:|
| `llm_total_ms` / `llm_ttft_ms` | 613.5 | 1077.9 | 750.3 | 2165.0 |
| `client_first_byte_ms` | 750.8 | 1272.9 | 860.6 | 2266.8 |
| `client_total_ms` | 750.8 | 1272.9 | 1158.8 | 2546.1 |

**Result:** streaming's fair test. First byte got **worse** by 109.8ms at p50 (860.6 vs 750.8) — the hypothesized win did not appear. Whole reply arrived 408.0ms later on `client_total_ms`.

## 3. Provider — Groq vs Gemini, streamed short reply (N=10 each)

`LLM_MODEL` = `groq-oss` vs `gemini-flash`.

| Segment | Groq p50 | p95 | Gemini p50 | p95 |
|---|---:|---:|---:|---:|
| `llm_ttft_ms` | 450.0 | 714.5 | 1676.9 | 3211.9 |
| `client_first_byte_ms` | 552.5 | 824.5 | 1772.0 | 3313.9 |

**Result:** Groq is ~3.7x faster at p50 (1226.9ms gap), and the tail gap is even wider (2497.4ms at p95). The largest, clearest effect in the whole study.

## 4. Tool transport — MCP vs local, streamed weather prompt (N=10 each)

`USE_LOCAL_WEATHER_TOOL` = `false` (MCP, shipped) vs `true` (local).

| Segment | MCP p50 | p95 | local p50 | p95 |
|---|---:|---:|---:|---:|
| `llm_ttft_ms` | 950.1 | 2779.5 | 1255.9 | 2305.0 |
| `client_first_byte_ms` | 1055.4 | 2884.1 | 1383.8 | 2416.7 |

**Result:** MCP was **faster** than the in-process local tool at p50 by 305.8ms (24% lower) — opposite of the assumed "transport tax." Ranking reverses at p95 (one outlier per set); N=10 cannot resolve the true direction, but there is no measured cost to optimize away.

## Headline takeaways

1. **The model call dominates everything.** ~91% of a short-reply turn; database and rate-limiter costs net to zero.
2. **Streaming is a UX mechanism, not a latency win.** No first-byte improvement on either prompt length; the long reply actively got slower on total delivery time.
3. **Provider choice is the one lever that matters.** Groq vs Gemini is a 3.7x gap — bigger than every other measured difference combined.
4. **MCP transport cost is unmeasurable at this sample size, and possibly negative.** Do not spend engineering effort clawing back an MCP "tax" — none was found.
5. **Network/TLS/Caddy overhead is stable at 88–130ms** regardless of prompt, provider, or transport — a hosting/placement decision, not a code one.

Full analysis, caveats, and per-segment breakdowns: [`REPORT.md`](REPORT.md). Raw and pooled data behind every cell: [`runs/`](runs/).
