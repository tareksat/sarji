# Sarjy — PRD

**Date:** 2026-09-01
**Budget:** 2 days, part-time
**Deep dive:** Latency

---

## 1. What this is

Sarjy is a voice assistant that listens and replies by voice, remembers facts about the user across sessions, and calls an external API to answer questions it could not answer on its own.

The assignment sets a floor and asks for one deep dive done properly. This document records what I am building, what I am deliberately not building, and how I will know whether the deep dive worked.

## 2. Goals

1. Meet the floor end to end, deployed at a URL a reviewer can open with no setup.
2. Reduce time-to-first-audio as far as two days allows, with measurements that show where the time goes.
3. Be able to answer follow-up questions about every decision here.

## 3. Non-goals

Explicitly cut, and why:

| Cut | Reason |
|---|---|
| Authentication | `user_id` is a client-generated UUID. Spoofable, and irrelevant to a single-reviewer demo. |
| Image / vision input | Not a floor requirement. Belonged to a UI-focused deep dive I am not doing. |
| Eval suite | Worth building for a system with nondeterministic output. Does not fit two days alongside the deep dive. |
| Avatar / rich visual frontend | A different deep dive. Doing it shallowly alongside this one would weaken both. |

## 4. Floor requirements

**Voice in and out.** Browser Web Speech API — `SpeechRecognition` for input, `SpeechSynthesis` for output. Both are feature-detected and degrade to a text-only interface where unsupported.

Known limitation: Web Speech is Chrome and Edge only. Safari and Firefox visitors get a text box and a banner telling them to switch browsers. Building a server-side STT fallback was considered and cut — it is audio plumbing, which the assignment explicitly does not evaluate, and the time is better spent on the deep dive.

**Session history.** Sessions and messages are read from Postgres through `GET /api/sessions` and `GET /api/sessions/{id}/messages`, with rename and delete alongside them. `localStorage` holds only the user's id and which chat was last open, so history survives a storage clear and follows the user to another browser.

Session rows are created lazily on the first message rather than when "New chat" is clicked, which keeps empty conversations out of the database. Read endpoints are scoped by `user_id` and return 404 for a session belonging to someone else. That is a scoping check, not authentication — `user_id` is a client-generated UUID and remains spoofable, which is an accepted tradeoff for a single-reviewer demo.

**Cross-session memory.** The agent exposes a `save_memory` tool and decides for itself when a fact is durable enough to keep. Facts are stored per user in Postgres and injected into the system prompt on later turns, including in new sessions. This is separate from the recent-message history, which is per session and windowed.

**External API — weather, served over MCP.**

Weather is the right choice here because it is the shortest path to proving that memory and tool use compose rather than merely coexist. Sarjy resolves the location from what it already remembers about the user, so "what's the weather" gets answered without asking which city — and if it does not yet know, it asks once and saves the answer. The failure mode this avoids is the one that makes voice assistants tiring to use: being made to repeat context you already gave.

The tool is exposed through an MCP server rather than a local function tool. This is how the external API is wired, not a second deep dive — the assignment asks for one deep dive done properly, and latency is it.

MCP is not free: it puts a transport hop in front of every tool call, which pulls against the latency work. That tension is the point rather than a problem to hide. The per-call overhead is measured on the same harness as everything else and reported as its own row, alongside what it would take to claw back.

A plain `@function_tool` implementation ships and deploys first. The MCP transport is swapped in afterwards, so a failure there costs the deep dive nothing and leaves the floor intact.

## 5. Deep dive — latency

### Why this one

Sarj builds voice products, and time-to-first-audio is the number a user actually feels. It is also the deep dive with a falsifiable outcome: either the number moved or it did not, and either way there is something specific to say about where the time went.

### Hypothesis

I expect time-to-first-audio to be dominated by two things, neither of which is audio:

1. **A request/response turn.** If the reply is returned whole, the user waits for the last token before hearing the first word. Streaming should be the single largest win.
2. **Speech endpointing.** `SpeechRecognition` waits for silence before emitting a final transcript, which can spend a second of dead air before the request is even sent — time no backend work can recover.

Secondary cost centres I expect to find: database round-trips serialised ahead of the model call, throttling that makes callers wait rather than rejecting them, and a system prompt that grows with every memory fact ever saved.

These are predictions. The measurements decide, and I would rather publish a hypothesis that turned out wrong than pretend I knew.

### Method

Instrument first, change nothing until there is a baseline.

Client-side marks: speech end → request sent → first response byte → first audio.
Server-side spans: database time, LLM time-to-first-token, total handler time.

Baseline is ten runs of a fixed prompt against the deployed application, not localhost, reported as p50 and p95 per segment. Every intervention is re-measured the same way.

### Planned interventions, in expected order of payoff

1. Stream tokens over SSE; flush to speech at the first sentence boundary.
2. Cap or remove the rate limiter's queue wait.
3. Parallelize the pre-LLM reads; defer writes until after the response has started.
4. Bound the injected memory facts and the history window.
5. Tune STT endpointing so the final transcript arrives sooner.
6. Warm the speech-synthesis voice list at page load.
7. Compare Gemini against Groq on the same harness.

### Deliverable

A before/after table by segment, including interventions that bought nothing. A change that failed to help is more informative than another win, and I would rather present the real distribution than a selected one.

### Honest caveat

Browser TTS runs locally, so it is not the bottleneck — which means the number I am optimizing is mostly the LLM path. Worth stating plainly rather than letting it be discovered.

## 6. Architecture

Component map, request-flow sequence, and the database schema are in [`ARCHITECTURE.md`](ARCHITECTURE.md).

**Stack.** FastAPI and Postgres on the server, the OpenAI Agents SDK for the agent loop, React and Vite on the client. Nothing exotic — the interesting decisions are below, not in the framework choices.

Decisions worth stating up front:

- **Model provider.** Gemini through its OpenAI-compatible endpoint, using `OpenAIChatCompletionsModel`, since the SDK's default Responses API is not implemented by Gemini, with tracing disabled. Base URL, key, and model name are env vars, so switching to Groq for the provider comparison is a config change, not a code change. This is config-driven, not an adapter layer — the abstraction would be indirection around a single live implementation.
- **Transport.** `POST /api/chat` streams over SSE so speech can start on the first sentence rather than the last token.
- **Serving.** FastAPI serves the built frontend, so the deployment is one origin and one URL — no CORS, and a link that opens with no setup.

## 7. Risks

| Risk | Mitigation |
|---|---|
| Free-tier rate limits during the live presentation | Retry with backoff; visible "rate limited, retrying" state rather than a silent stall |
| Reviewer opens the URL in Safari | Browser banner, plus "open in Chrome" in the README, the Loom, and the submission |
| Streaming rework destabilizes the working floor | Floor is deployed and working at the end of day 1, before the deep dive starts |
| Measurements taken on localhost | All numbers come from the deployed app |

## 8. Timeline

Two days, part-time. The shape matters more than the step list: **day 1 ends
with a deployed application that meets the floor**, so the deep dive can never
cost me a working submission.

**Day 0 — before any code.** Repository on GitHub, draft PR open, this document
written. Message the reviewer with the deep dive pick, a request for Gemini and
Groq keys, and a request for their GitHub username.

**Day 1 — floor, deployed.**

1. Point the agent at Gemini through its OpenAI-compatible endpoint, with base
   URL, key and model as env vars.
2. Weather tool as a plain function tool, resolving location from memory.
3. Session history in Postgres — list, read, rename, delete — so the sidebar
   survives a storage clear.
4. Serve the built frontend from FastAPI; deploy; confirm the microphone works
   over HTTPS on the deployed URL, not just locally.
5. Swap the weather tool onto MCP. **Time-boxed to day 1** — if it is not
   working by the end of the day, the plain function tool ships and I move on.

**Day 2 — the latency deep dive.**

1. Build the timing harness and record a baseline before changing anything. The
   baseline is the story; without it there is no deep dive.
2. Work the interventions in expected order of payoff, re-measuring each.
3. Barge-in, and a live time-to-first-audio readout in the UI.
4. Re-measure and build the before/after table, including what did not help.
5. **Last 90 minutes: stop building.** Record the Loom, write the five-minute
   talk. This time is not negotiable — it is the first thing the reviewer sees.

**If day 2 runs short,** the MCP overhead measurement goes first, then the
provider comparison, then the smaller interventions. The timing harness and
streaming stay — without those two there is nothing to present.

A short progress update goes out at the end of each day, including the days
where the update is that nothing happened.

Phase-by-phase build order is in [`IMPLEMENTATION-PLAN.md`](IMPLEMENTATION-PLAN.md); the working checklist is [`../todo.md`](../todo.md).
