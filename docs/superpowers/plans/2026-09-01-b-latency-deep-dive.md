# Sarjy — Latency Deep Dive Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

> **Prerequisite:** [`2026-09-01-a-deploy-the-floor.md`](2026-09-01-a-deploy-the-floor.md) is complete and the app is live at a public HTTPS URL, referred to throughout as `$SARJY_URL`. Every number in this plan comes from that URL, never from localhost.

**Goal:** Drive time-to-first-audio down, measure where the time goes, and publish a before/after table that includes the interventions that bought nothing.

**Architecture:** Two layers are added around the working backend. A timing layer reports per-segment spans with every turn — database, limiter wait, model time-to-first-token, total — returned on the wire and logged. A streaming SSE variant of `POST /api/chat` lets the browser start speaking at the first sentence rather than the last token. The existing non-streaming `POST /api/chat` is kept for the whole exercise: it is the "before" column, and deleting it would make the comparison unreproducible.

**Tech Stack:** FastAPI, SQLAlchemy 2.x (sync sessions), `openai-agents` (`Runner.run_streamed`), `mcp` (Streamable HTTP), Postgres 16 on Neon, React 19 + Vite 8, browser Web Speech API (STT + TTS), Render.

**Spec:** [`docs/IMPLEMENTATION-PLAN.md`](../../IMPLEMENTATION-PLAN.md) phases 8–11, [`docs/PRD.md`](../../PRD.md) §5 "Deep dive — latency", [`docs/ARCHITECTURE.md`](../../ARCHITECTURE.md), [`todo.md`](../../../todo.md) #12–26.

## Status going in

The floor is deployed and working. Missing, and covered by this plan:

| Gap | Spec reference |
|---|---|
| No timing instrumentation, client or server | Phase 8; todo #12 |
| No baseline table | Phase 8; todo #13 |
| No streaming / SSE | Phase 9.1; todo #14 |
| Rate limiter queue wait uncapped | Phase 9.2; todo #15 |
| Pre-model DB reads serial, writes on the hot path | Phase 9.3; todo #16 |
| Memory facts and history window unbounded/untuned | Phase 9.4; todo #17 |
| STT endpointing untuned | Phase 9.5; todo #18 |
| TTS voice list not warmed | Phase 9.6; todo #19 |
| No provider comparison run | Phase 9.7; todo #20 |
| No MCP-vs-function-tool overhead run | Phase 9.8; todo #21 |
| No barge-in | Phase 10; todo #22 |
| No TTFA readout / waterfall | Phase 10; todo #23 |
| No before/after table, Loom, or talk | Phase 11; todo #24–26 |

## Global Constraints

- **No test suite.** This is a deliberate cut recorded in the PRD's non-goals and in `CLAUDE.md`. Verification is per task, by `curl`, by browser, or by a script — never by a unit test framework. Do not add pytest or vitest.
- **All numbers come from the deployed app, not localhost.** (PRD §7 risk table.) Local runs are for correctness only; every measurement written into a results table is taken against `$SARJY_URL`.
- **Instrument before intervening.** Task 3's baseline is committed before a single optimization lands. It cannot be reconstructed later.
- **The floor stays working.** `POST /api/chat` (non-streaming) keeps its current behavior and response contract for the whole plan; streaming is added at `POST /api/chat/stream`. Every task ends with the deployed app still able to hold a conversation.
- **Provider is config, not code.** `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL` are the only things that change between Gemini and Groq. No adapter layer.
- **Timings are milliseconds, floats rounded to one decimal**, and every server span name ends in `_ms`.
- **Percentiles reported are p50 and p95 over 10 iterations of one fixed prompt**, warm-up run discarded.
- **Record what did not help.** A null result is a row in the results table, not a failure to hide.
- **Commit after every task**, with a `feat:` / `perf:` / `docs:` prefix. The branch is `UI`; do not merge to `main` without asking.
- **Chrome only** for voice. Any UI regression must still leave a working text-only interface in other browsers.

## File Structure

**Created**

| Path | Responsibility |
|---|---|
| `sarjy-backend/app/core/timing.py` | `Timings` collector — spans, marks, serialization |
| `sarjy-backend/app/services/streaming.py` | SSE event generator for a streamed turn |
| `sarjy-backend/app/agent/local_weather.py` | Local `@function_tool` copy of `get_weather`, for the MCP-overhead A/B only |
| `sarjy-backend/scripts/measure.py` | Server/network harness — N runs, p50/p95, writes a markdown table |
| `sarjy-backend/scripts/summarize_client_timings.py` | Turns pasted browser timing JSON lines into the same table shape |
| `sarjy-ui/src/timing.js` | Client turn timer — marks and derived segments |
| `sarjy-ui/src/components/TurnTimings.jsx` | Live TTFA readout and per-turn waterfall |
| `docs/latency/baseline.md` | The "before" column. Committed before any intervention |
| `docs/latency/RESULTS.md` | The before/after table, including what did not help |
| `docs/latency/runs/` | Raw per-run output from `measure.py`, one file per labelled run |

**Modified**

| Path | Change |
|---|---|
| `sarjy-backend/app/core/config.py` | New settings: limiter cap, memory fact cap, local-tool flag |
| `sarjy-backend/app/core/rate_limiter.py` | Bounded wait, returns waited-ms, raises when over the cap |
| `sarjy-backend/app/services/chat.py` | Timings, limiter cap, fact cap |
| `sarjy-backend/app/routers/chat.py` | Returns timings; adds the streaming route; 429 response |
| `sarjy-backend/app/dtos/chat.py` | `timings` field on `ChatResponse` |
| `sarjy-backend/app/agent/sarjy_agent.py` | Local-tool switch for the A/B |
| `sarjy-backend/app/repositories/memory.py` | `facts_for_user(db, user_id, limit)` — newest first, capped |
| `sarjy-ui/src/api.js` | `sendMessageStream()` alongside `sendMessage()` |
| `sarjy-ui/src/App.jsx` | Streaming turn, timings wiring, barge-in, TTS warm |
| `sarjy-ui/src/hooks/useSpeechSynthesis.js` | Chunk queue, `warm()`, speaking state |
| `sarjy-ui/src/hooks/useSpeechRecognition.js` | Interim results, speech-end mark, endpointing, barge-in hook |
| `sarjy-ui/src/App.css` | Styles for the readout and waterfall |
| `sarjy-backend/RUNBOOK.md` | New env vars, deployment section, harness usage |
| `docs/openapi.json` | Regenerated after the endpoint changes |
| `README.md` | Pointer to the results, how to run the harness |
| `todo.md` | Checkboxes ticked as tasks land |

---

## Task 1: Server-side timing spans

Phase 8, server half. Measure before changing anything. The non-streaming path cannot report a true time-to-first-token — it only ever sees the whole response — so it reports `llm_total_ms` and leaves `llm_ttft_ms` null. That is the honest baseline, and Task 4's streaming endpoint is what fills the column in.

**Files:**
- Create: `sarjy-backend/app/core/timing.py`
- Modify: `sarjy-backend/app/services/chat.py`, `sarjy-backend/app/dtos/chat.py`, `sarjy-backend/app/routers/chat.py`, `sarjy-backend/app/core/rate_limiter.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `Timings` with `span(name)`, `mark(name)`, `set(name, value)`, `as_dict() -> dict[str, float | None]`; `handle_chat(...) -> tuple[str, dict]`; `TokenBucketRateLimiter.acquire() -> float` (ms waited); `ChatResponse.timings: dict[str, float] | None`. Span names: `db_read_ms`, `db_write_ms`, `limiter_wait_ms`, `llm_total_ms`, `llm_ttft_ms`, `total_ms`.

- [ ] **Step 1: Write the timing collector**

Create `sarjy-backend/app/core/timing.py`:

```python
import time
from contextlib import contextmanager

MS = 1000.0


class Timings:
    """Per-turn wall-clock spans, in milliseconds.

    Returned with the response and logged, so a slow turn on the deployed app
    can be attributed without a profiler attached.
    """

    def __init__(self) -> None:
        self._started = time.perf_counter()
        self._spans: dict[str, float | None] = {}

    @contextmanager
    def span(self, name: str):
        started = time.perf_counter()
        try:
            yield
        finally:
            self._spans[name] = round((time.perf_counter() - started) * MS, 1)

    def mark(self, name: str) -> None:
        """Record the time from the start of the turn to now."""
        self._spans[name] = round((time.perf_counter() - self._started) * MS, 1)

    def set(self, name: str, value: float | None) -> None:
        self._spans[name] = None if value is None else round(value, 1)

    def add(self, name: str, value: float) -> None:
        """Accumulate into a span that is entered more than once per turn."""
        self._spans[name] = round((self._spans.get(name) or 0.0) + value, 1)

    def as_dict(self) -> dict[str, float | None]:
        return {**self._spans, "total_ms": round((time.perf_counter() - self._started) * MS, 1)}

    def as_log_line(self) -> str:
        return " ".join(f"{k}={v}" for k, v in self.as_dict().items())
```

- [ ] **Step 2: Make the limiter report its wait**

In `sarjy-backend/app/core/rate_limiter.py`, change `acquire` to return the milliseconds it waited. Replace the method body's two `return` paths:

```python
    async def acquire(self) -> float:
        """Take a token, waiting if necessary. Returns the ms spent waiting."""
        started = time.monotonic()
        while True:
            async with self._lock:
                now = time.monotonic()
                elapsed = now - self._updated_at
                self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
                self._updated_at = now

                if self.tokens >= 1:
                    self.tokens -= 1
                    return (time.monotonic() - started) * 1000.0

                wait_time = (1 - self.tokens) / self.refill_rate

            logger.info("Rate limiter: waiting %.2fs for a token", wait_time)
            await asyncio.sleep(wait_time)
```

- [ ] **Step 3: Instrument `handle_chat`**

In `sarjy-backend/app/services/chat.py`, import the collector:

```python
from ..core.timing import Timings
```

Change the signature and body of `handle_chat` so every phase is inside a span and the timings come back with the reply:

```python
async def handle_chat(
    db: DbSession, user_id: uuid.UUID, session_id: uuid.UUID, message: str
) -> tuple[str, dict[str, float | None]]:
    logger.info("handle_chat start user_id=%s session_id=%s", user_id, session_id)
    timings = Timings()

    with timings.span("db_read_ms"):
        users_repo.upsert(db, user_id)
        session = sessions_repo.get_or_create(db, session_id, user_id, title_from_message(message))
        sessions_repo.add_message(db, session_id, "user", message)
        db.flush()
        history = [
            {"role": m.role, "content": m.content}
            for m in sessions_repo.recent_messages(db, session_id, settings.chat_history_limit)
        ]
        facts = memory_repo.facts_for_user(db, user_id)

    agent = build_agent(facts)
    context = ChatContext(user_id=user_id, session_id=session_id, db=db)

    timings.set("limiter_wait_ms", await _rate_limiter.acquire())

    try:
        with timings.span("llm_total_ms"):
            result = await _run_with_retry(agent, history, context)
    except Exception as exc:
        db.rollback()
        logger.error(
            "handle_chat failed user_id=%s session_id=%s: %s",
            user_id, session_id, exc, exc_info=True,
        )
        raise LLMUnavailableError(
            "Sarjy is having trouble responding right now. Please try again."
        ) from exc

    reply = result.final_output

    with timings.span("db_write_ms"):
        sessions_repo.add_message(db, session_id, "assistant", reply)
        # Inserting a Message does not touch the Session row, so `onupdate` never
        # fires. Set it explicitly to keep the sidebar's recency ordering correct.
        session.updated_at = now_utc()
        db.commit()

    # A non-streamed turn only ever sees the whole response, so there is no
    # first-token moment to measure. The streaming endpoint fills this in.
    timings.set("llm_ttft_ms", None)

    logger.info(
        "handle_chat complete user_id=%s session_id=%s %s",
        user_id, session_id, timings.as_log_line(),
    )

    return reply, timings.as_dict()
```

- [ ] **Step 4: Return timings on the wire**

In `sarjy-backend/app/dtos/chat.py`, add the field to `ChatResponse`:

```python
    timings: dict[str, float | None] | None = Field(
        default=None,
        description=(
            "Server-side spans for this turn, in milliseconds: `db_read_ms`, "
            "`db_write_ms`, `limiter_wait_ms`, `llm_total_ms`, `llm_ttft_ms` "
            "(null unless streamed) and `total_ms`. Present so the client can "
            "attribute latency without server access."
        ),
    )
```

In `sarjy-backend/app/routers/chat.py`, unpack the tuple:

```python
        reply, timings = await handle_chat(db, user_id, session_id, req.message)
    except LLMUnavailableError as exc:
        logger.warning("Returning 502 for user_id=%s session_id=%s: %s", user_id, session_id, exc)
        raise HTTPException(status_code=502, detail=str(exc))

    return ChatResponse(reply=reply, timings=timings)
```

- [ ] **Step 5: Verify against the deployed app**

```bash
curl -s -X POST $SARJY_URL/api/chat \
  -H 'Content-Type: application/json' \
  -d '{"user_id":"3f1a9c2e-5b7d-4e88-9a21-6c0f4d8b1e33","session_id":"b74e2f10-8c3a-4d61-9f52-1a7e0c9d4b88","message":"Say hello in five words."}'
```

Expected: JSON containing a `timings` object where `db_read_ms`, `llm_total_ms`, `total_ms` are positive numbers, `llm_ttft_ms` is `null`, and `db_read_ms + llm_total_ms + db_write_ms` is close to `total_ms`. If `total_ms` is much larger than the sum, something un-instrumented is on the hot path — find it before recording a baseline.

- [ ] **Step 6: Commit**

```bash
git add sarjy-backend/app/core/timing.py sarjy-backend/app/core/rate_limiter.py sarjy-backend/app/services/chat.py sarjy-backend/app/dtos/chat.py sarjy-backend/app/routers/chat.py
git commit -m "feat: report per-turn server timing spans"
```

---

## Task 2: Client-side timing marks

Phase 8, client half. The four marks the PRD names: speech end → request sent → first response byte → first audio. Typed turns skip the speech-end mark and measure from send.

**Files:**
- Create: `sarjy-ui/src/timing.js`
- Modify: `sarjy-ui/src/hooks/useSpeechRecognition.js`, `sarjy-ui/src/hooks/useSpeechSynthesis.js`, `sarjy-ui/src/App.jsx`

**Interfaces:**
- Consumes: `ChatResponse.timings` from Task 1.
- Produces: `createTurnTimer()` → `{ mark(name), setServer(timings), segments(), publish() }`; `useSpeechRecognition(onResult, { onSpeechEnd })`; `useSpeechSynthesis()` additionally returns `onAudioStart` registration via a `speak(text, { onStart })` option. Segment names: `stt_tail_ms`, `request_ms`, `first_byte_ms`, `ttfa_ms`, plus the server spans nested under `server`.

- [ ] **Step 1: Write the client timer**

Create `sarjy-ui/src/timing.js`:

```javascript
// One timer per conversational turn. Marks are wall-clock ms from
// `performance.now()`; segments are the differences the deep dive reports.
export function createTurnTimer() {
  const marks = {};
  let server = null;

  const diff = (from, to) =>
    marks[from] !== undefined && marks[to] !== undefined
      ? Math.round(marks[to] - marks[from])
      : null;

  return {
    mark(name) {
      if (marks[name] === undefined) marks[name] = performance.now();
    },
    setServer(timings) {
      server = timings ?? null;
    },
    segments() {
      // The origin is speech end for a spoken turn and the send for a typed
      // one, so the two are never averaged together in a results table.
      const origin = marks.speechEnd !== undefined ? 'speechEnd' : 'requestSent';
      return {
        source: marks.speechEnd !== undefined ? 'voice' : 'typed',
        stt_tail_ms: diff('speechEnd', 'requestSent'),
        first_byte_ms: diff('requestSent', 'firstByte'),
        reply_complete_ms: diff('requestSent', 'replyComplete'),
        ttfa_ms: diff(origin, 'firstAudio'),
        server,
      };
    },
    publish() {
      const line = this.segments();
      // One JSON line per turn. `summarize_client_timings.py` reads these.
      console.log(`[sarjy-timing] ${JSON.stringify(line)}`);
      return line;
    },
  };
}
```

- [ ] **Step 2: Mark speech end in the recognition hook**

In `sarjy-ui/src/hooks/useSpeechRecognition.js`, accept an options object and wire `onspeechend` — this is the mark that exposes the STT tail, the dead air between the user stopping and the transcript arriving:

```javascript
export function useSpeechRecognition(onResult, { onSpeechEnd } = {}) {
  const [listening, setListening] = useState(false);
  const recognitionRef = useRef(null);
  const onResultRef = useRef(onResult);
  const onSpeechEndRef = useRef(onSpeechEnd);
  onResultRef.current = onResult;
  onSpeechEndRef.current = onSpeechEnd;
```

and inside the effect, next to the existing handlers:

```javascript
    recognition.onspeechend = () => onSpeechEndRef.current?.();
```

- [ ] **Step 3: Mark first audio in the synthesis hook**

In `sarjy-ui/src/hooks/useSpeechSynthesis.js`, let callers observe the moment audio actually starts:

```javascript
  const speak = (text, { onStart } = {}) => {
    if (!supported || !text) return;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = ARABIC_SCRIPT.test(text) ? 'ar-SA' : 'en-US';
    // `onstart` fires when the utterance begins, which is the client-side
    // definition of time-to-first-audio.
    utterance.onstart = () => onStart?.();
    window.speechSynthesis.speak(utterance);
  };
```

- [ ] **Step 4: Wire the timer through a turn in `App.jsx`**

Add the import:

```javascript
import { createTurnTimer } from './timing';
```

Add a ref that holds the timer for the turn currently in flight, next to the other state:

```javascript
  const timerRef = useRef(null);
```

(and add `useRef` to the existing `react` import).

Change `runSend` to mark the request and the reply:

```javascript
  const runSend = useCallback(
    async (userMessageId, text) => {
      setLoading(true);
      const timer = timerRef.current ?? createTurnTimer();
      timerRef.current = timer;
      timer.mark('requestSent');
      try {
        const { reply, timings } = await sendMessage(userId, activeId, text);
        timer.mark('firstByte');
        timer.mark('replyComplete');
        timer.setServer(timings);
        updateActiveMessages((prev) => [
          ...prev,
          {
            id: crypto.randomUUID(),
            role: 'assistant',
            text: reply,
            createdAt: new Date().toISOString(),
          },
        ]);
        notePersisted();
        if (!muted && ttsSupported) {
          speak(reply, {
            onStart: () => {
              timer.mark('firstAudio');
              timer.publish();
            },
          });
        } else {
          timer.publish();
        }
      } catch {
        updateActiveMessages((prev) =>
          prev.map((m) => (m.id === userMessageId ? { ...m, status: 'error' } : m))
        );
      } finally {
        setLoading(false);
      }
    },
    [activeId, muted, ttsSupported, speak, updateActiveMessages, notePersisted]
  );
```

Start the timer at speech end, before the transcript exists:

```javascript
  const handleSpeechEnd = useCallback(() => {
    const timer = createTurnTimer();
    timer.mark('speechEnd');
    timerRef.current = timer;
  }, []);

  const { supported: micSupported, listening, start, stop } = useSpeechRecognition(
    handleSend,
    { onSpeechEnd: handleSpeechEnd }
  );
```

- [ ] **Step 5: Verify in the browser**

Open `$SARJY_URL` in Chrome with the console open. Type a message: one `[sarjy-timing]` line appears with `"source":"typed"`, a null `stt_tail_ms`, and a populated `server` object. Speak a message: the line has `"source":"voice"` and a positive `stt_tail_ms`. If `stt_tail_ms` is null on a spoken turn, `onspeechend` is not firing — check that `handleSpeechEnd` is passed, since every later STT number depends on it.

- [ ] **Step 6: Commit**

```bash
git add sarjy-ui/src/timing.js sarjy-ui/src/hooks/useSpeechRecognition.js sarjy-ui/src/hooks/useSpeechSynthesis.js sarjy-ui/src/App.jsx
git commit -m "feat: mark speech end, request, first byte, and first audio per turn"
```

---

## Task 3: Measurement harness and the committed baseline

Phase 8's deliverable. This is the "before" column and cannot be reconstructed later — do not start Task 4 until this table is committed.

**Files:**
- Create: `sarjy-backend/scripts/measure.py`, `sarjy-backend/scripts/summarize_client_timings.py`, `docs/latency/baseline.md`, `docs/latency/runs/`

**Interfaces:**
- Consumes: `timings` from Task 1, the console lines from Task 2.
- Produces: `python scripts/measure.py --base-url URL --label NAME [--stream]` writing `docs/latency/runs/NAME.md` and printing the same table; `python scripts/summarize_client_timings.py FILE` printing the client-side table.

- [ ] **Step 1: Write the server/network harness**

Create `sarjy-backend/scripts/measure.py`:

```python
"""Latency harness: N turns of one fixed prompt, p50/p95 per segment.

Usage:
    python scripts/measure.py --base-url https://sarjy.onrender.com --label baseline
    python scripts/measure.py --base-url ... --label streaming --stream

Each iteration uses a fresh session id so history length stays constant, and
the first run is discarded as a warm-up. Covers the server and network
segments only; the browser-side marks come from summarize_client_timings.py.
"""

import argparse
import json
import time
import uuid
from pathlib import Path

import httpx

TIMEOUT_SECONDS = 120.0
DEFAULT_PROMPT = "In one sentence, what is the capital of France?"
SEGMENTS = [
    "db_read_ms",
    "limiter_wait_ms",
    "llm_ttft_ms",
    "llm_total_ms",
    "db_write_ms",
    "total_ms",
    "client_first_byte_ms",
    "client_total_ms",
]


def percentile(values: list[float], p: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round(p / 100 * len(ordered) + 0.5) - 1))
    return round(ordered[index], 1)


def run_once(client: httpx.Client, user_id: str, prompt: str, stream: bool) -> dict:
    session_id = str(uuid.uuid4())
    payload = {"user_id": user_id, "session_id": session_id, "message": prompt}
    started = time.perf_counter()

    if not stream:
        resp = client.post("/api/chat", json=payload)
        resp.raise_for_status()
        body = resp.json()
        elapsed = (time.perf_counter() - started) * 1000
        timings = dict(body.get("timings") or {})
        timings["client_first_byte_ms"] = round(elapsed, 1)
        timings["client_total_ms"] = round(elapsed, 1)
        return timings

    first_byte = None
    timings = {}
    with client.stream("POST", "/api/chat/stream", json=payload) as resp:
        resp.raise_for_status()
        for line in resp.iter_lines():
            if not line.startswith("data: "):
                continue
            event = json.loads(line[len("data: "):])
            if event["type"] == "delta" and first_byte is None:
                first_byte = (time.perf_counter() - started) * 1000
            elif event["type"] == "done":
                timings = dict(event.get("timings") or {})
            elif event["type"] == "error":
                raise RuntimeError(event.get("detail", "stream error"))

    total = (time.perf_counter() - started) * 1000
    timings["client_first_byte_ms"] = round(first_byte or total, 1)
    timings["client_total_ms"] = round(total, 1)
    return timings


def render_table(label: str, base_url: str, prompt: str, rows: list[dict]) -> str:
    lines = [
        f"# Latency run — {label}",
        "",
        f"- Target: `{base_url}`",
        f"- Prompt: `{prompt}`",
        f"- Iterations: {len(rows)} (warm-up discarded)",
        "",
        "| Segment | p50 (ms) | p95 (ms) |",
        "|---|---:|---:|",
    ]
    for name in SEGMENTS:
        values = [r[name] for r in rows if isinstance(r.get(name), (int, float))]
        if not values:
            lines.append(f"| `{name}` | — | — |")
            continue
        lines.append(f"| `{name}` | {percentile(values, 50)} | {percentile(values, 95)} |")
    lines.append("")
    lines.append("Raw per-run values:")
    lines.append("")
    lines.append("```json")
    lines.append(json.dumps(rows, indent=2))
    lines.append("```")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--iterations", type=int, default=10)
    parser.add_argument("--prompt", default=DEFAULT_PROMPT)
    parser.add_argument("--stream", action="store_true")
    parser.add_argument("--out-dir", default="../docs/latency/runs")
    args = parser.parse_args()

    user_id = str(uuid.uuid4())
    rows: list[dict] = []

    with httpx.Client(base_url=args.base_url.rstrip("/"), timeout=TIMEOUT_SECONDS) as client:
        print("warm-up…")
        run_once(client, user_id, args.prompt, args.stream)
        for i in range(args.iterations):
            row = run_once(client, user_id, args.prompt, args.stream)
            rows.append(row)
            print(f"{i + 1}/{args.iterations}: {row}")

    table = render_table(args.label, args.base_url, args.prompt, rows)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{args.label}.md"
    out_path.write_text(table, encoding="utf-8")

    print()
    print(table)
    print(f"written to {out_path}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Write the client-timing summarizer**

Create `sarjy-backend/scripts/summarize_client_timings.py`:

```python
"""Summarize browser timing lines into the same p50/p95 table shape.

Copy the `[sarjy-timing] {...}` lines out of the Chrome console into a file,
then:

    python scripts/summarize_client_timings.py runs/baseline-client.txt

The browser marks (STT tail, time-to-first-audio) cannot be driven headlessly
without changing the thing being measured, so they are collected by hand from
ten real spoken turns on the deployed app.
"""

import argparse
import json
import sys
from pathlib import Path

PREFIX = "[sarjy-timing] "
SEGMENTS = ["stt_tail_ms", "first_byte_ms", "reply_complete_ms", "ttfa_ms"]


def percentile(values: list[float], p: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round(p / 100 * len(ordered) + 0.5) - 1))
    return round(ordered[index], 1)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    parser.add_argument("--source", choices=["voice", "typed"], default="voice")
    args = parser.parse_args()

    rows = []
    for line in Path(args.path).read_text(encoding="utf-8").splitlines():
        marker = line.find(PREFIX)
        if marker == -1:
            continue
        row = json.loads(line[marker + len(PREFIX):])
        if row.get("source") == args.source:
            rows.append(row)

    if not rows:
        print(f"No {args.source} turns found in {args.path}")
        sys.exit(1)

    print(f"| Segment | p50 (ms) | p95 (ms) |")
    print(f"|---|---:|---:|")
    for name in SEGMENTS:
        values = [r[name] for r in rows if isinstance(r.get(name), (int, float))]
        print(f"| `{name}` | {percentile(values, 50)} | {percentile(values, 95)} |")
    print(f"\n{len(rows)} {args.source} turns.")


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Record the server baseline against the deployed app**

From `sarjy-backend/`:

```bash
python scripts/measure.py --base-url $SARJY_URL --label baseline
```

Expected: ten rows printed, then a table where `llm_ttft_ms` is `—` (not measurable without streaming) and `llm_total_ms` dominates `total_ms`. File written to `docs/latency/runs/baseline.md`.

- [ ] **Step 4: Record the client baseline by hand**

In Chrome on `$SARJY_URL`, speak the same fixed prompt — "In one sentence, what is the capital of France?" — ten times, unmuted, waiting for the reply each time. Copy the console lines into `docs/latency/runs/baseline-client.txt`, then:

```bash
python scripts/summarize_client_timings.py ../docs/latency/runs/baseline-client.txt
```

Expected: a table with a positive `stt_tail_ms` p50 (the hypothesized second of dead air) and a `ttfa_ms` p50 close to `stt_tail_ms + total_ms`.

- [ ] **Step 5: Write the baseline document**

Create `docs/latency/baseline.md` combining both tables, with the target URL, the model, the date, and one paragraph naming what the numbers already suggest — where the time sits before anything is changed. State plainly that browser TTS is local and therefore not the bottleneck, per the PRD's honest caveat.

- [ ] **Step 6: Commit**

```bash
git add sarjy-backend/scripts/measure.py sarjy-backend/scripts/summarize_client_timings.py docs/latency/
git commit -m "feat: add the latency harness and record the baseline"
```

---

## Task 4: Stream the reply over SSE (backend)

Phase 9.1, expected to be the largest win. New endpoint; `POST /api/chat` is untouched.

**Files:**
- Create: `sarjy-backend/app/services/streaming.py`
- Modify: `sarjy-backend/app/routers/chat.py`

**Interfaces:**
- Consumes: `Timings`, `build_agent`, `ChatContext`, the repositories.
- Produces: `POST /api/chat/stream` emitting `text/event-stream` frames, each `data: <json>\n\n`, with `{"type":"delta","text":str}`, then exactly one `{"type":"done","reply":str,"timings":{...}}`, or `{"type":"error","detail":str}`. Also `stream_chat(db, user_id, session_id, message) -> AsyncIterator[dict]`.

- [ ] **Step 1: Write the streaming service**

Create `sarjy-backend/app/services/streaming.py`:

```python
import logging
import uuid
from collections.abc import AsyncIterator

from agents import Runner
from openai.types.responses import ResponseTextDeltaEvent
from sqlalchemy.orm import Session as DbSession

from ..agent.sarjy_agent import ChatContext, build_agent
from ..core.config import settings
from ..core.timing import Timings
from ..models import now_utc
from ..repositories import memory as memory_repo
from ..repositories import sessions as sessions_repo
from ..repositories import users as users_repo
from .chat import _rate_limiter, title_from_message

logger = logging.getLogger(__name__)


async def stream_chat(
    db: DbSession, user_id: uuid.UUID, session_id: uuid.UUID, message: str
) -> AsyncIterator[dict]:
    """Run one turn, yielding token deltas as they arrive.

    The point of the endpoint: the client can start speaking at the first
    sentence instead of waiting for the last token.
    """
    logger.info("stream_chat start user_id=%s session_id=%s", user_id, session_id)
    timings = Timings()

    with timings.span("db_read_ms"):
        users_repo.upsert(db, user_id)
        session = sessions_repo.get_or_create(db, session_id, user_id, title_from_message(message))
        sessions_repo.add_message(db, session_id, "user", message)
        db.flush()
        history = [
            {"role": m.role, "content": m.content}
            for m in sessions_repo.recent_messages(db, session_id, settings.chat_history_limit)
        ]
        facts = memory_repo.facts_for_user(db, user_id)

    agent = build_agent(facts)
    context = ChatContext(user_id=user_id, session_id=session_id, db=db)

    timings.set("limiter_wait_ms", await _rate_limiter.acquire())

    chunks: list[str] = []
    try:
        result = Runner.run_streamed(agent, input=history, context=context)
        async for event in result.stream_events():
            if event.type != "raw_response_event":
                continue
            if not isinstance(event.data, ResponseTextDeltaEvent):
                continue
            if not chunks:
                timings.mark("llm_ttft_ms")
            chunks.append(event.data.delta)
            yield {"type": "delta", "text": event.data.delta}
    except Exception as exc:
        db.rollback()
        logger.error(
            "stream_chat failed user_id=%s session_id=%s: %s",
            user_id, session_id, exc, exc_info=True,
        )
        yield {
            "type": "error",
            "detail": "Sarjy is having trouble responding right now. Please try again.",
        }
        return

    reply = "".join(chunks) or result.final_output

    with timings.span("db_write_ms"):
        sessions_repo.add_message(db, session_id, "assistant", reply)
        session.updated_at = now_utc()
        db.commit()

    timings.set("llm_total_ms", None)
    logger.info(
        "stream_chat complete user_id=%s session_id=%s %s",
        user_id, session_id, timings.as_log_line(),
    )

    yield {"type": "done", "reply": reply, "timings": timings.as_dict()}
```

Note: `llm_ttft_ms` is a `mark`, so it is measured from the start of the turn — subtract `db_read_ms` and `limiter_wait_ms` when attributing it purely to the model.

- [ ] **Step 2: Add the route**

In `sarjy-backend/app/routers/chat.py`, add the imports:

```python
import json

from fastapi.responses import StreamingResponse

from ..services.streaming import stream_chat
```

and the route below the existing one:

```python
@router.post(
    "/api/chat/stream",
    summary="Send a message and stream Sarjy's reply",
    response_description="A `text/event-stream` of `delta` frames, then one `done` frame.",
    responses={**BAD_UUID},
)
async def chat_stream(req: ChatRequest, db: DbSession = Depends(get_db)):
    """Run one conversational turn, streamed.

    Identical to `POST /api/chat` in what it persists; the difference is that
    tokens are emitted as they arrive, so the browser can begin speaking at the
    first sentence boundary rather than at the last token. Frames are
    `data: {json}` and carry `type` of `delta`, `done`, or `error`; failures
    arrive as an `error` frame with HTTP 200, since the response has usually
    already begun by then.
    """
    user_id = parse_uuid(req.user_id, "user_id")
    session_id = parse_uuid(req.session_id, "session_id")

    async def events():
        async for event in stream_chat(db, user_id, session_id, req.message):
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # stop any proxy from buffering the stream
        },
    )
```

- [ ] **Step 3: Verify streaming locally**

```bash
curl -N -X POST http://localhost:8000/api/chat/stream \
  -H 'Content-Type: application/json' \
  -d '{"user_id":"3f1a9c2e-5b7d-4e88-9a21-6c0f4d8b1e33","session_id":"'"$(python -c 'import uuid;print(uuid.uuid4())')"'","message":"Count slowly from one to twenty."}'
```

Expected: `data: {"type":"delta"...}` frames appearing progressively (not all at once), then one `done` frame with a `timings` object whose `llm_ttft_ms` is much smaller than `total_ms`. If every frame arrives together, buffering is in the way — check `X-Accel-Buffering` and that no middleware is collecting the body.

- [ ] **Step 4: Verify the memory tool still fires on the streamed path**

Send `{"message": "Remember that I live in Riyadh."}` to `/api/chat/stream`, then ask `"What's the weather?"` in a **new** session id on the same user. Expected: the weather answer without a follow-up question, and a `Saved memory for` line in the log. Tool calls inside a streamed run are the thing most likely to silently regress here.

- [ ] **Step 5: Deploy and re-verify**

Push, let Render build, then repeat step 3 against `$SARJY_URL`. Streaming through the platform's proxy is a different question from streaming locally, which is why it is checked separately.

- [ ] **Step 6: Commit**

```bash
git add sarjy-backend/app/services/streaming.py sarjy-backend/app/routers/chat.py
git commit -m "perf: stream chat replies over SSE"
```

---

## Task 5: Consume the stream and speak at the first sentence

The client half of phase 9.1. Audio must start at the first sentence boundary, not the last token — that is where the TTFA win actually comes from.

**Files:**
- Modify: `sarjy-ui/src/api.js`, `sarjy-ui/src/hooks/useSpeechSynthesis.js`, `sarjy-ui/src/App.jsx`

**Interfaces:**
- Consumes: the SSE contract from Task 4.
- Produces: `sendMessageStream(userId, sessionId, message, { onDelta, onDone, onError })`; `useSpeechSynthesis()` returning `{ speak, speakChunk, beginTurn, cancel, speaking, supported }` where `speakChunk(text, { onStart })` enqueues without cancelling what is already speaking, and `beginTurn()` re-arms the once-per-turn `onStart` that marks first audio. (`warm` joins this object in Task 10.)

- [ ] **Step 1: Add the streaming client**

In `sarjy-ui/src/api.js`, below `sendMessage`:

```javascript
// SSE over POST, so `fetch` rather than `EventSource` (which is GET-only).
export async function sendMessageStream(userId, sessionId, message, handlers = {}) {
  const { onDelta, onDone, onError } = handlers;
  const res = await fetch('/api/chat/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: userId, session_id: sessionId, message }),
  });
  if (!res.ok || !res.body) throw new Error(`Request failed: ${res.status}`);

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    // Frames are separated by a blank line; a partial frame stays in `buffer`.
    let split;
    while ((split = buffer.indexOf('\n\n')) !== -1) {
      const frame = buffer.slice(0, split).trim();
      buffer = buffer.slice(split + 2);
      if (!frame.startsWith('data:')) continue;
      const event = JSON.parse(frame.slice(5).trim());
      if (event.type === 'delta') onDelta?.(event.text);
      else if (event.type === 'done') onDone?.(event);
      else if (event.type === 'error') onError?.(new Error(event.detail));
    }
  }
}
```

- [ ] **Step 2: Give the synthesis hook a queue**

Rewrite `sarjy-ui/src/hooks/useSpeechSynthesis.js`:

```javascript
import { useCallback, useRef, useState } from 'react';

const supported = typeof window !== 'undefined' && 'speechSynthesis' in window;

const ARABIC_SCRIPT = /[؀-ۿ]/;

function utteranceFor(text) {
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = ARABIC_SCRIPT.test(text) ? 'ar-SA' : 'en-US';
  return utterance;
}

export function useSpeechSynthesis() {
  const [speaking, setSpeaking] = useState(false);
  const startedRef = useRef(false);

  // Whole-reply speech: cancels whatever is in flight first.
  const speak = useCallback((text, { onStart } = {}) => {
    if (!supported || !text) return;
    window.speechSynthesis.cancel();
    const utterance = utteranceFor(text);
    utterance.onstart = () => {
      setSpeaking(true);
      onStart?.();
    };
    utterance.onend = () => setSpeaking(false);
    window.speechSynthesis.speak(utterance);
  }, []);

  // Streamed speech: each sentence is appended to the queue the browser
  // already holds, so playback is continuous while tokens are still arriving.
  const speakChunk = useCallback((text, { onStart } = {}) => {
    if (!supported || !text.trim()) return;
    const utterance = utteranceFor(text);
    utterance.onstart = () => {
      setSpeaking(true);
      if (!startedRef.current) {
        startedRef.current = true;
        onStart?.();
      }
    };
    utterance.onend = () => setSpeaking(window.speechSynthesis.speaking);
    window.speechSynthesis.speak(utterance);
  }, []);

  const beginTurn = useCallback(() => {
    startedRef.current = false;
  }, []);

  const cancel = useCallback(() => {
    if (!supported) return;
    window.speechSynthesis.cancel();
    setSpeaking(false);
  }, []);

  return { speak, speakChunk, beginTurn, cancel, speaking, supported };
}
```

- [ ] **Step 3: Add sentence splitting and stream the turn in `App.jsx`**

Add a module-level helper above the component:

```javascript
// Returns [complete sentences, remainder]. Speaking whole sentences keeps the
// prosody natural; speaking token-by-token does not.
const SENTENCE_END = /([.!?…]+["')\]]*)(\s+)/;

function takeSentences(buffer) {
  const sentences = [];
  let rest = buffer;
  for (;;) {
    const match = SENTENCE_END.exec(rest);
    if (!match) break;
    const cut = match.index + match[1].length + match[2].length;
    sentences.push(rest.slice(0, cut).trim());
    rest = rest.slice(cut);
  }
  return [sentences, rest];
}
```

Replace `runSend` with the streamed version:

```javascript
  const runSend = useCallback(
    async (userMessageId, text) => {
      setLoading(true);
      const timer = timerRef.current ?? createTurnTimer();
      timerRef.current = timer;
      timer.mark('requestSent');
      beginTurn();

      const assistantId = crypto.randomUUID();
      let full = '';
      let spoken = '';
      let unspoken = '';
      let opened = false;

      const markAudio = () => {
        timer.mark('firstAudio');
      };

      try {
        await sendMessageStream(userId, activeId, text, {
          onDelta: (delta) => {
            timer.mark('firstByte');
            full += delta;
            unspoken += delta;

            if (!opened) {
              opened = true;
              updateActiveMessages((prev) => [
                ...prev,
                {
                  id: assistantId,
                  role: 'assistant',
                  text: full,
                  createdAt: new Date().toISOString(),
                },
              ]);
            } else {
              updateActiveMessages((prev) =>
                prev.map((m) => (m.id === assistantId ? { ...m, text: full } : m))
              );
            }

            const [sentences, rest] = takeSentences(unspoken);
            unspoken = rest;
            if (!muted && ttsSupported) {
              sentences.forEach((sentence) => {
                spoken += sentence;
                speakChunk(sentence, { onStart: markAudio });
              });
            }
          },
          onDone: (event) => {
            timer.mark('replyComplete');
            timer.setServer(event.timings);
            const tail = event.reply.slice(spoken.length).trim();
            if (!muted && ttsSupported && tail) speakChunk(tail, { onStart: markAudio });
            updateActiveMessages((prev) =>
              prev.map((m) => (m.id === assistantId ? { ...m, text: event.reply } : m))
            );
            setTimings(timer.publish());
            notePersisted();
          },
          onError: (error) => {
            throw error;
          },
        });
      } catch {
        updateActiveMessages((prev) =>
          prev
            .filter((m) => m.id !== assistantId)
            .map((m) => (m.id === userMessageId ? { ...m, status: 'error' } : m))
        );
      } finally {
        setLoading(false);
      }
    },
    [activeId, muted, ttsSupported, speakChunk, beginTurn, updateActiveMessages, notePersisted]
  );
```

Add the state it references, next to the other `useState` calls:

```javascript
  const [timings, setTimings] = useState(null);
```

and update the hook destructuring and imports:

```javascript
import { getUserId, sendMessageStream } from './api';
```

```javascript
  const {
    speak,
    speakChunk,
    beginTurn,
    cancel: cancelSpeech,
    speaking,
    supported: ttsSupported,
  } = useSpeechSynthesis();
```

`speak` is now unused by `runSend` but stays exported for the barge-in work in Task 11; if the linter objects, drop it from the destructuring until then.

- [ ] **Step 4: Verify in the browser**

On the deployed URL in Chrome, unmuted, ask for a long answer ("Tell me about Riyadh in four sentences."). Expected: text appears progressively in the bubble, and speech begins after the first sentence completes rather than at the end. The `[sarjy-timing]` line's `ttfa_ms` should be dramatically lower than the baseline's.

- [ ] **Step 5: Verify the failure and retry paths**

Stop the backend mid-reply (or throttle the network to offline in DevTools). Expected: the partial assistant bubble is removed, the user bubble shows the error state, and the retry button re-runs the turn. No orphaned bubble, no stuck typing indicator.

- [ ] **Step 6: Commit**

```bash
git add sarjy-ui/src/api.js sarjy-ui/src/hooks/useSpeechSynthesis.js sarjy-ui/src/App.jsx
git commit -m "perf: consume the SSE stream and speak at the first sentence boundary"
```

---

## Task 6: Re-measure, then cap the rate limiter's queue wait

Phase 9.2. Measure the streaming win first — that number is the headline — then take the limiter off the critical path.

**Files:**
- Modify: `sarjy-backend/app/core/config.py`, `sarjy-backend/app/core/rate_limiter.py`, `sarjy-backend/app/services/chat.py`, `sarjy-backend/app/services/streaming.py`, `sarjy-backend/app/routers/chat.py`, `sarjy-ui/src/App.jsx`, `sarjy-ui/src/App.css`, `sarjy-backend/.env.example`

**Interfaces:**
- Consumes: `TokenBucketRateLimiter.acquire()` from Task 1.
- Produces: `settings.llm_rate_limit_max_wait_seconds` (default `2.0`); `RateLimitedError` raised by `acquire()` when the projected wait exceeds the cap; HTTP 429 with a `Retry-After` header from both chat routes; a visible "rate limited, retrying" state in the UI.

- [ ] **Step 1: Record the streaming run**

```bash
python scripts/measure.py --base-url $SARJY_URL --label streaming --stream
```

Collect ten spoken turns' console lines into `docs/latency/runs/streaming-client.txt` and summarize them. This is intervention 1's "after" column — capture it before intervention 2 changes anything.

- [ ] **Step 2: Add the cap setting**

In `sarjy-backend/app/core/config.py`, after `llm_rate_limit_per_minute`:

```python
    llm_rate_limit_max_wait_seconds: float = 2.0
```

and in `sarjy-backend/.env.example`:

```
# Longest a turn will queue behind the local token bucket before the caller is
# told to retry. The bucket used to wait indefinitely, which showed up as
# latency the user could not explain.
LLM_RATE_LIMIT_MAX_WAIT_SECONDS=2.0
```

- [ ] **Step 3: Bound the wait**

In `sarjy-backend/app/core/rate_limiter.py`, add the error and enforce the cap:

```python
class RateLimitedError(Exception):
    """Raised when a caller would have to queue longer than the cap allows."""

    def __init__(self, retry_after_seconds: float):
        self.retry_after_seconds = retry_after_seconds
        super().__init__(f"Rate limited; retry in {retry_after_seconds:.1f}s")
```

Change the constructor to take the cap, and the wait branch to honour it:

```python
    def __init__(self, rate_per_minute: int, max_wait_seconds: float = 2.0):
        self.capacity = rate_per_minute
        self.tokens = float(rate_per_minute)
        self.refill_rate = rate_per_minute / 60.0  # tokens per second
        self.max_wait_seconds = max_wait_seconds
        self._updated_at = time.monotonic()
        self._lock = asyncio.Lock()
```

```python
                wait_time = (1 - self.tokens) / self.refill_rate

            if (time.monotonic() - started) + wait_time > self.max_wait_seconds:
                logger.warning(
                    "Rate limiter: refusing to queue %.2fs (cap %.2fs)",
                    wait_time, self.max_wait_seconds,
                )
                raise RateLimitedError(wait_time)

            logger.info("Rate limiter: waiting %.2fs for a token", wait_time)
            await asyncio.sleep(wait_time)
```

- [ ] **Step 4: Surface it as a 429**

In `sarjy-backend/app/services/chat.py`, construct the limiter with the cap:

```python
_rate_limiter = TokenBucketRateLimiter(
    settings.llm_rate_limit_per_minute, settings.llm_rate_limit_max_wait_seconds
)
```

In `sarjy-backend/app/routers/chat.py`, import `RateLimitedError` from `..core.rate_limiter` and catch it in `chat()`:

```python
    except RateLimitedError as exc:
        raise HTTPException(
            status_code=429,
            detail=str(exc),
            headers={"Retry-After": str(max(1, round(exc.retry_after_seconds)))},
        )
```

In `sarjy-backend/app/services/streaming.py`, add the import:

```python
from ..core.rate_limiter import RateLimitedError
```

and wrap the `acquire()` call so the client gets a frame rather than a broken stream:

```python
    try:
        timings.set("limiter_wait_ms", await _rate_limiter.acquire())
    except RateLimitedError as exc:
        db.rollback()
        yield {"type": "error", "detail": f"Rate limited. Retry in {exc.retry_after_seconds:.0f}s."}
        return
```

Declare the response in the route decorator's `responses` dict:

```python
        429: {
            "model": ErrorResponse,
            "description": "The local token bucket would have queued this turn past its cap.",
        },
```

- [ ] **Step 5: Verify the cap fires and is visible**

Temporarily set `LLM_RATE_LIMIT_PER_MINUTE=1` locally, then send three turns quickly. Expected: the first succeeds, later ones return an `error` frame within ~2s rather than hanging, the log shows `Rate limiter: refusing to queue`, and the UI shows the error state rather than a silent stall. Restore the value afterwards.

- [ ] **Step 6: Re-measure, then commit**

```bash
python scripts/measure.py --base-url $SARJY_URL --label limiter-capped --stream
git add sarjy-backend/app/core/config.py sarjy-backend/app/core/rate_limiter.py sarjy-backend/app/services/ sarjy-backend/app/routers/chat.py sarjy-backend/.env.example docs/latency/runs/
git commit -m "perf: cap the rate limiter's queue wait and surface it as 429"
```

---

## Task 7: Take the database off the hot path

Phase 9.3. Two reads run in parallel on their own sessions, and the user-message insert moves behind the first token. SQLAlchemy's sync `Session` is not safe to share across threads, so each parallel read gets its own — that is the reason for the extra sessions, and it belongs in the commit message.

**Files:**
- Modify: `sarjy-backend/app/services/streaming.py`

**Interfaces:**
- Consumes: `SessionLocal` from `app.core.db`.
- Produces: `_load_context(session_id, user_id) -> tuple[list[dict], list[str]]` running both reads concurrently.

- [ ] **Step 1: Add the parallel loader**

In `sarjy-backend/app/services/streaming.py`, add the imports:

```python
import asyncio

from ..core.db import SessionLocal
```

and the helper above `stream_chat`:

```python
def _read_history(session_id: uuid.UUID) -> list[dict]:
    # Its own Session: SQLAlchemy's sync Session is not thread-safe, and this
    # runs concurrently with the memory read on a worker thread.
    with SessionLocal() as db:
        return [
            {"role": m.role, "content": m.content}
            for m in sessions_repo.recent_messages(db, session_id, settings.chat_history_limit)
        ]


def _read_facts(user_id: uuid.UUID) -> list[str]:
    with SessionLocal() as db:
        return memory_repo.facts_for_user(db, user_id)


async def _load_context(
    session_id: uuid.UUID, user_id: uuid.UUID
) -> tuple[list[dict], list[str]]:
    return await asyncio.gather(
        asyncio.to_thread(_read_history, session_id),
        asyncio.to_thread(_read_facts, user_id),
    )
```

- [ ] **Step 2: Restructure the turn**

Replace the read block at the top of `stream_chat` with a minimal write plus the parallel read, and defer the assistant write:

```python
    with timings.span("db_write_pre_ms"):
        users_repo.upsert(db, user_id)
        session = sessions_repo.get_or_create(db, session_id, user_id, title_from_message(message))
        sessions_repo.add_message(db, session_id, "user", message)
        db.commit()

    with timings.span("db_read_ms"):
        history, facts = await _load_context(session_id, user_id)
```

The user message is committed before the reads because the history read runs in another session and must see it. The assistant-side write already happens after the stream finishes, which is the "defer writes" half.

Add the new span to the harness so it shows up in every later table — in `sarjy-backend/scripts/measure.py`, insert `"db_write_pre_ms"` into `SEGMENTS` directly after `"db_read_ms"`.

- [ ] **Step 3: Verify correctness before speed**

Hold a three-turn conversation on the deployed app. Expected: turn three still sees turns one and two (the parallel read sees the just-committed user message), the sidebar still orders by recency, and `save_memory` still writes. A dropped message here would be invisible in the timings and obvious in the demo.

- [ ] **Step 4: Re-measure**

```bash
python scripts/measure.py --base-url $SARJY_URL --label db-parallel --stream
```

Expected: `db_read_ms` p50 falls to roughly the slower of the two reads rather than their sum. If it does not move, say so in the results table — a null result is a row, not a failure.

- [ ] **Step 5: Commit**

```bash
git add sarjy-backend/app/services/streaming.py docs/latency/runs/
git commit -m "perf: parallelize the pre-model reads and defer the assistant write"
```

---

## Task 8: Bound the injected memory facts and the history window

Phase 9.4. The system prompt currently grows with every fact ever saved — architecture §4 calls this out as deliberate-for-now and one of the interventions.

**Files:**
- Modify: `sarjy-backend/app/repositories/memory.py`, `sarjy-backend/app/core/config.py`, `sarjy-backend/app/agent/sarjy_agent.py`, `sarjy-backend/app/services/chat.py`, `sarjy-backend/app/services/streaming.py`, `sarjy-backend/.env.example`

**Interfaces:**
- Consumes: `Memory.created_at`.
- Produces: `facts_for_user(db, user_id, limit: int | None = None) -> list[str]` returning the newest `limit` facts in chronological order; `settings.memory_facts_limit` (default `20`).

- [ ] **Step 1: Cap the fact read**

Rewrite `sarjy-backend/app/repositories/memory.py`:

```python
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from ..models import Memory


def facts_for_user(db: DbSession, user_id: uuid.UUID, limit: int | None = None) -> list[str]:
    """Return the user's durable facts, oldest first.

    `limit` keeps the newest N. Every fact is injected into the system prompt on
    every turn, so an unbounded read grows the input token count — and the
    time-to-first-token — for the life of the account.
    """
    query = select(Memory).where(Memory.user_id == user_id).order_by(Memory.created_at.desc())
    if limit is not None:
        query = query.limit(limit)
    rows = list(db.execute(query).scalars().all())
    rows.reverse()
    return [m.content for m in rows]
```

- [ ] **Step 2: Add the setting**

In `sarjy-backend/app/core/config.py`:

```python
    memory_facts_limit: int = 20
```

In `sarjy-backend/.env.example`:

```
# Newest N durable facts injected into the system prompt each turn. Unbounded
# before the latency work; every fact costs input tokens on every turn.
MEMORY_FACTS_LIMIT=20
```

- [ ] **Step 3: Pass the limit at both call sites**

In `sarjy-backend/app/services/chat.py`:

```python
    facts = memory_repo.facts_for_user(db, user_id, settings.memory_facts_limit)
```

In `sarjy-backend/app/services/streaming.py`, inside `_read_facts`:

```python
        return memory_repo.facts_for_user(db, user_id, settings.memory_facts_limit)
```

- [ ] **Step 4: Verify the cap and the recall it protects**

Save 25 facts on a throwaway user (25 turns of "Remember that fact number N is X"), then ask about fact 25 and about fact 1. Expected: fact 25 is recalled; fact 1 is not — and that is the tradeoff to state out loud in the results, not to hide.

- [ ] **Step 5: Measure both the fact cap and a smaller history window**

```bash
python scripts/measure.py --base-url $SARJY_URL --label prompt-trimmed --stream
```

Then set `CHAT_HISTORY_LIMIT=10` on Render, redeploy, and run `--label history-10 --stream`. Record both, including whichever bought nothing.

- [ ] **Step 6: Commit**

```bash
git add sarjy-backend/app/repositories/memory.py sarjy-backend/app/core/config.py sarjy-backend/app/services/ sarjy-backend/.env.example docs/latency/runs/
git commit -m "perf: bound the injected memory facts and the history window"
```

---

## Task 9: Cut the STT tail

Phase 9.5. The dead air between the user stopping and the transcript arriving is time no backend work can recover, and Task 2's `stt_tail_ms` says exactly how much of it there is.

**Files:**
- Modify: `sarjy-ui/src/hooks/useSpeechRecognition.js`

**Interfaces:**
- Consumes: `onSpeechEnd` from Task 2.
- Produces: unchanged public shape — `{ supported, listening, start, stop }` — with interim results tracked internally and `stop()` called on speech end to force the final transcript.

- [ ] **Step 1: Track interim results and end the turn on speech end**

Replace the effect body in `sarjy-ui/src/hooks/useSpeechRecognition.js`:

```javascript
  useEffect(() => {
    if (!SpeechRecognitionImpl) return;

    const recognition = new SpeechRecognitionImpl();
    recognition.continuous = false;
    // Interim results give a transcript to fall back on the moment speech ends,
    // instead of waiting out the engine's silence timeout.
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    let interim = '';
    let sent = false;

    const send = (transcript) => {
      const text = transcript.trim();
      if (sent || !text) return;
      sent = true;
      onResultRef.current(text);
    };

    recognition.onresult = (event) => {
      let final = '';
      interim = '';
      for (let i = event.resultIndex; i < event.results.length; i += 1) {
        const result = event.results[i];
        if (result.isFinal) final += result[0].transcript;
        else interim += result[0].transcript;
      }
      if (final) send(final);
    };

    recognition.onspeechend = () => {
      onSpeechEndRef.current?.();
      // Forces the engine to finalize now rather than after its own silence
      // timeout. The final result usually still arrives and wins the race; the
      // interim is the floor, not the plan.
      recognition.stop();
      interimTimeoutRef.current = window.setTimeout(() => send(interim), 400);
    };

    recognition.onend = () => {
      window.clearTimeout(interimTimeoutRef.current);
      if (!sent) send(interim);
      sent = false;
      interim = '';
      setListening(false);
    };
    recognition.onerror = () => setListening(false);

    recognitionRef.current = recognition;
    return () => {
      window.clearTimeout(interimTimeoutRef.current);
      recognition.abort();
    };
  }, []);
```

Add the ref next to the others at the top of the hook:

```javascript
  const interimTimeoutRef = useRef(null);
```

- [ ] **Step 2: Verify no double sends**

On the deployed app, speak five short questions. Expected: exactly one user bubble per utterance — the `sent` guard is what prevents the interim fallback and the final result both firing. A duplicated message here is worse than the latency it saves, so check this before measuring.

- [ ] **Step 3: Verify transcript quality did not drop**

Speak three longer sentences with a mid-sentence pause. Expected: the full sentence is captured, not a truncated fragment. If pauses now cut people off, raise the 400 ms fallback and re-check — and record the tradeoff.

- [ ] **Step 4: Re-measure the client segments**

Ten spoken turns of the fixed prompt into `docs/latency/runs/stt-tuned-client.txt`, then summarize. Expected: `stt_tail_ms` p50 drops; `ttfa_ms` drops by roughly the same amount.

- [ ] **Step 5: Commit**

```bash
git add sarjy-ui/src/hooks/useSpeechRecognition.js docs/latency/runs/
git commit -m "perf: finalize the transcript at speech end instead of the silence timeout"
```

---

## Task 10: Warm the speech-synthesis voices

Phase 9.6. The first utterance can stall while the voice list loads; warming at page start moves that cost out of the first turn.

**Files:**
- Modify: `sarjy-ui/src/hooks/useSpeechSynthesis.js`, `sarjy-ui/src/App.jsx`

**Interfaces:**
- Consumes: nothing.
- Produces: `useSpeechSynthesis()` additionally returning `warm()`, safe to call repeatedly.

- [ ] **Step 1: Add warming to the hook**

In `sarjy-ui/src/hooks/useSpeechSynthesis.js`, add above the returned object:

```javascript
  const warmedRef = useRef(false);

  // Chrome populates the voice list asynchronously, and the first utterance
  // pays for it. Called at page load and again on the first user gesture,
  // since autoplay policy blocks synthesis before one.
  const warm = useCallback(() => {
    if (!supported || warmedRef.current) return;
    window.speechSynthesis.getVoices();
    const silent = new SpeechSynthesisUtterance(' ');
    silent.volume = 0;
    silent.onend = () => {
      warmedRef.current = true;
    };
    window.speechSynthesis.speak(silent);
  }, []);
```

and include `warm` in the returned object.

- [ ] **Step 2: Call it at load and on the first gesture**

In `sarjy-ui/src/App.jsx`, pull `warm` out of the hook and add:

```javascript
  useEffect(() => {
    warm();
    const onFirstGesture = () => warm();
    window.addEventListener('pointerdown', onFirstGesture, { once: true });
    window.addEventListener('keydown', onFirstGesture, { once: true });
    return () => {
      window.removeEventListener('pointerdown', onFirstGesture);
      window.removeEventListener('keydown', onFirstGesture);
    };
  }, [warm]);
```

- [ ] **Step 3: Verify the first turn**

Hard-reload the deployed app and immediately speak one question. Expected: no audible delay before the first word beyond the measured TTFA, and no stray sound from the silent warm-up utterance.

- [ ] **Step 4: Measure the first-turn effect specifically**

This one only shows up on a cold page, so measure it as five hard-reload-then-one-turn runs, not ten consecutive turns. Record `ttfa_ms` for the first turn in each, with and without the change (comment out the `warm()` call to get the "before"). Note the smaller sample size in the results table rather than pretending it matches the others.

- [ ] **Step 5: Commit**

```bash
git add sarjy-ui/src/hooks/useSpeechSynthesis.js sarjy-ui/src/App.jsx docs/latency/runs/
git commit -m "perf: warm the speech-synthesis voice list at page load"
```

---

## Task 11: Barge-in

Phase 10. Perceived latency rather than measured — speaking over Sarjy cuts her off immediately and starts a new turn. Armed only in hands-free mode, because a hot mic during playback will otherwise hear the speakers and interrupt Sarjy with her own voice.

**Files:**
- Modify: `sarjy-ui/src/hooks/useSpeechRecognition.js`, `sarjy-ui/src/App.jsx`, `sarjy-ui/src/components/MessageInput.jsx`, `sarjy-ui/src/App.css`

**Interfaces:**
- Consumes: `speaking` from Task 5's synthesis hook.
- Produces: `useSpeechRecognition(onResult, { onSpeechEnd, onSpeechStart })`; a `handsFree` toggle in `App.jsx` that keeps recognition running between turns.

- [ ] **Step 1: Expose speech start**

In `sarjy-ui/src/hooks/useSpeechRecognition.js`, accept and store the callback alongside `onSpeechEnd`:

```javascript
export function useSpeechRecognition(onResult, { onSpeechEnd, onSpeechStart } = {}) {
```

```javascript
  const onSpeechStartRef = useRef(onSpeechStart);
  onSpeechStartRef.current = onSpeechStart;
```

and in the effect:

```javascript
    recognition.onspeechstart = () => onSpeechStartRef.current?.();
```

- [ ] **Step 2: Cut speech when the user starts talking**

In `sarjy-ui/src/App.jsx`, add the state and handler:

```javascript
  const [handsFree, setHandsFree] = useState(false);

  // Barge-in: the moment the user starts speaking, Sarjy stops. Only armed in
  // hands-free mode — with a hot mic during playback, the microphone can hear
  // the speakers and interrupt Sarjy with her own voice.
  const handleSpeechStart = useCallback(() => {
    if (speaking) cancelSpeech();
  }, [speaking, cancelSpeech]);
```

and pass it:

```javascript
  const { supported: micSupported, listening, start, stop } = useSpeechRecognition(handleSend, {
    onSpeechEnd: handleSpeechEnd,
    onSpeechStart: handleSpeechStart,
  });
```

- [ ] **Step 3: Keep the microphone open in hands-free mode**

```javascript
  useEffect(() => {
    if (!handsFree || !micSupported || listening || loading) return;
    start();
  }, [handsFree, micSupported, listening, loading, start]);
```

- [ ] **Step 4: Add the toggle to the input bar**

In `sarjy-ui/src/components/MessageInput.jsx`, accept `handsFree` and `onHandsFreeToggle` and render a button next to the mic:

```jsx
      {micSupported && (
        <button
          className={`icon-btn hands-free-btn ${handsFree ? 'active' : ''}`}
          onClick={onHandsFreeToggle}
          title={handsFree ? 'Hands-free on — speak any time to interrupt' : 'Hands-free off'}
          aria-pressed={handsFree}
        >
          ∞
        </button>
      )}
```

Style `.hands-free-btn.active` in `App.css` to match the existing `.mic-listening` treatment.

- [ ] **Step 5: Verify barge-in on the deployed app**

In Chrome with headphones on (to remove the echo path), turn hands-free on, ask for a long answer, and start speaking mid-sentence. Expected: speech stops within a beat, the new utterance becomes the next turn, and the previous reply stays in the transcript. Then repeat on laptop speakers and note in the results whether echo triggers false interrupts — that observation is part of the honest write-up.

- [ ] **Step 6: Commit**

```bash
git add sarjy-ui/src/hooks/useSpeechRecognition.js sarjy-ui/src/App.jsx sarjy-ui/src/components/MessageInput.jsx sarjy-ui/src/App.css
git commit -m "feat: barge-in — speaking over Sarjy cuts her off"
```

---

## Task 12: The TTFA readout and per-turn waterfall

Phase 10's other half. Numbers on screen are what the room remembers.

**Files:**
- Create: `sarjy-ui/src/components/TurnTimings.jsx`
- Modify: `sarjy-ui/src/App.jsx`, `sarjy-ui/src/App.css`

**Interfaces:**
- Consumes: the `timings` state set in Task 5 from `timer.publish()`.
- Produces: `<TurnTimings timings={timings} />` rendering the last turn's TTFA and a four-segment bar.

- [ ] **Step 1: Write the component**

Create `sarjy-ui/src/components/TurnTimings.jsx`:

```jsx
// Segments in the order they happen, so the bar reads left to right as the
// turn actually unfolded.
const SEGMENTS = [
  { key: 'stt_tail_ms', label: 'speech → send', className: 'seg-stt' },
  { key: 'server_read_ms', label: 'db', className: 'seg-db' },
  { key: 'server_ttft_ms', label: 'model', className: 'seg-model' },
  { key: 'audio_ms', label: 'audio start', className: 'seg-audio' },
];

function derive(timings) {
  if (!timings) return null;
  const server = timings.server ?? {};
  const dbMs = server.db_read_ms ?? 0;
  const ttftMs = Math.max(0, (server.llm_ttft_ms ?? 0) - dbMs);
  const sttMs = timings.stt_tail_ms ?? 0;
  const audioMs = Math.max(0, (timings.ttfa_ms ?? 0) - sttMs - dbMs - ttftMs);
  return {
    stt_tail_ms: sttMs,
    server_read_ms: dbMs,
    server_ttft_ms: ttftMs,
    audio_ms: audioMs,
    total: timings.ttfa_ms ?? 0,
  };
}

export default function TurnTimings({ timings }) {
  const parts = derive(timings);
  if (!parts || !parts.total) return null;

  return (
    <div className="turn-timings" title="Time to first audio, by segment">
      <div className="ttfa-readout">
        <strong>{Math.round(parts.total)}</strong> ms to first audio
      </div>
      <div className="waterfall">
        {SEGMENTS.map(({ key, label, className }) => {
          const width = (parts[key] / parts.total) * 100;
          if (width <= 0) return null;
          return (
            <div
              key={key}
              className={`waterfall-seg ${className}`}
              style={{ width: `${width}%` }}
              title={`${label}: ${Math.round(parts[key])} ms`}
            />
          );
        })}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Render it**

In `sarjy-ui/src/App.jsx`, import the component and place it between `ChatWindow` and `MessageInput`:

```jsx
        <TurnTimings timings={timings} />
```

- [ ] **Step 3: Style it**

Append to `sarjy-ui/src/App.css`. Keep it quiet enough that it does not compete with the conversation:

```css
.turn-timings {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 16px 0;
  font-size: 12px;
  opacity: 0.75;
}

.ttfa-readout strong {
  font-variant-numeric: tabular-nums;
}

.waterfall {
  display: flex;
  flex: 1;
  height: 6px;
  border-radius: 3px;
  overflow: hidden;
}

.waterfall-seg {
  height: 100%;
}

.seg-stt { background: #8b8bff; }
.seg-db { background: #4fb3a5; }
.seg-model { background: #f4a142; }
.seg-audio { background: #7a7f8a; }
```

- [ ] **Step 4: Verify on the deployed app**

Speak a turn. Expected: the readout updates per turn, the four segments sum to the full width, and the model segment visibly dominates — which is the point the deep dive makes out loud.

- [ ] **Step 5: Commit**

```bash
git add sarjy-ui/src/components/TurnTimings.jsx sarjy-ui/src/App.jsx sarjy-ui/src/App.css
git commit -m "feat: live time-to-first-audio readout and per-turn waterfall"
```

---

## Task 13: Provider comparison — Gemini against Groq

Phase 9.7. Config change only, per the PRD. Two rows in the results table.

**Files:**
- Create: `docs/latency/runs/provider-gemini.md`, `docs/latency/runs/provider-groq.md` (harness output)

**Interfaces:**
- Consumes: `scripts/measure.py`, the deployed service's env vars.
- Produces: two labelled runs taken on the same harness, same prompt, same day.

- [ ] **Step 1: Run Gemini**

With the deployed service on Gemini (`LLM_MODEL=gemini-3.6-flash`):

```bash
python scripts/measure.py --base-url $SARJY_URL --label provider-gemini --stream
```

- [ ] **Step 2: Switch the deployed service to Groq**

In Render, set:

```
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_API_KEY=<groq key>
LLM_MODEL=openai/gpt-oss-120b
```

Wait for the redeploy, then `curl $SARJY_URL/api/health` and hold one conversational turn to confirm the swap worked — including a weather question, since tool calling is the part most likely to differ between providers.

- [ ] **Step 3: Run Groq**

```bash
python scripts/measure.py --base-url $SARJY_URL --label provider-groq --stream
```

- [ ] **Step 4: Restore the demo provider**

Set the env vars back to whichever provider won, redeploy, and confirm a turn works. The demo must not be left pointing at a half-checked configuration.

- [ ] **Step 5: Commit**

```bash
git add docs/latency/runs/provider-gemini.md docs/latency/runs/provider-groq.md
git commit -m "docs: measure Gemini against Groq on the same harness"
```

---

## Task 14: MCP overhead against a plain function tool

Phase 9.8. The PRD promised this row: MCP puts a transport hop in front of every tool call, and the cost is reported rather than hidden. First on the cut list if time runs out.

**Files:**
- Create: `sarjy-backend/app/agent/local_weather.py`
- Modify: `sarjy-backend/app/core/config.py`, `sarjy-backend/app/agent/sarjy_agent.py`, `sarjy-backend/.env.example`

**Interfaces:**
- Consumes: the weather logic in `sarjy-mcp-server/tools/weather.py`.
- Produces: `settings.use_local_weather_tool` (default `False`); when true, `build_agent` registers the local tool and passes no `mcp_servers`.

- [ ] **Step 1: Copy the weather tool into the backend**

Copy `sarjy-mcp-server/tools/weather.py` to `sarjy-backend/app/agent/local_weather.py` verbatim — the imports, `WEATHER_GEOCODING_URL`, `WEATHER_FORECAST_URL`, `WEATHER_REQUEST_TIMEOUT_SECONDS`, the full `WEATHER_CODE_DESCRIPTIONS` map, and the `get_weather` body — then make exactly three changes to the copy:

Replace the module docstring area at the top with a header stating why the duplicate exists:

```python
"""A local `@function_tool` copy of the MCP server's `get_weather`.

Exists only for the latency write-up's A/B: the same lookup with and without
the MCP transport hop in front of it. `sarjy-mcp-server` remains the shipped
path — this module is reached only when `USE_LOCAL_WEATHER_TOOL=true`, and it
should be deleted if that comparison is ever dropped.
"""
```

Add the decorator import:

```python
from agents import function_tool
```

Rename the function and decorate it, leaving the docstring and body exactly as they are in the MCP copy — the docstring is the tool description the model reads, so a divergence here would make the A/B compare two different prompts:

```python
@function_tool
async def local_get_weather(location: str) -> str:
    """Get the current weather for a location. Only call this once the user's
    location is known (from known facts or from their answer earlier in this
    conversation) — do not guess a location."""
    # … body unchanged from sarjy-mcp-server/tools/weather.py …
```

- [ ] **Step 2: Add the switch**

In `sarjy-backend/app/core/config.py`:

```python
    use_local_weather_tool: bool = False
```

In `sarjy-backend/.env.example`:

```
# Measurement switch only: serves get_weather as a local function tool instead
# of over MCP, so the transport's per-call cost can be measured. Ships false.
USE_LOCAL_WEATHER_TOOL=false
```

In `sarjy-backend/app/agent/sarjy_agent.py`, change the return of `build_agent`:

```python
    tools = [save_memory]
    mcp_servers = [sarjy_mcp_server]  # get_weather lives in sarjy-mcp-server
    if settings.use_local_weather_tool:
        # A/B for the latency write-up: same tool, no transport hop.
        tools.append(local_get_weather)
        mcp_servers = []

    return Agent(
        name="Sarjy",
        instructions=instructions,
        model=settings.llm_model,
        tools=tools,
        mcp_servers=mcp_servers,
    )
```

with `from .local_weather import local_get_weather` added to the imports.

- [ ] **Step 3: Measure the MCP path**

The prompt must force a tool call, and the location must already be known, so seed a memory first with one manual turn on a fixed user id: "Remember that I live in Riyadh." Then:

```bash
python scripts/measure.py --base-url $SARJY_URL --label tool-mcp --stream \
  --prompt "What's the weather right now?"
```

- [ ] **Step 4: Measure the local-tool path**

Set `USE_LOCAL_WEATHER_TOOL=true` on Render, redeploy, confirm one weather turn answers, then:

```bash
python scripts/measure.py --base-url $SARJY_URL --label tool-local --stream \
  --prompt "What's the weather right now?"
```

Set it back to `false` and redeploy. The difference in `total_ms` p50 between the two runs is the per-call MCP overhead — that number, plus what it would take to claw it back (a warm connection, in-process transport, or fewer round trips), is the row.

- [ ] **Step 5: Commit**

```bash
git add sarjy-backend/app/agent/local_weather.py sarjy-backend/app/agent/sarjy_agent.py sarjy-backend/app/core/config.py sarjy-backend/.env.example docs/latency/runs/
git commit -m "docs: measure MCP transport overhead against a local function tool"
```

---

## Task 15: Final re-measure and the before/after table

Phase 11's substance. Same ten runs, same prompt, everything on.

**Files:**
- Create: `docs/latency/RESULTS.md`
- Modify: `docs/latency/baseline.md` (link only)

**Interfaces:**
- Consumes: every file in `docs/latency/runs/`.
- Produces: one table the reviewer reads first.

- [ ] **Step 1: Take the final run**

```bash
python scripts/measure.py --base-url $SARJY_URL --label final --stream
```

Plus ten spoken turns into `docs/latency/runs/final-client.txt` and its summary.

- [ ] **Step 2: Write the results document**

Create `docs/latency/RESULTS.md` with, in order: the headline before/after TTFA (p50 and p95), the per-segment table with a row per intervention, and a short section on what did not help. Include the interventions that bought nothing — a null result is the more interesting row, and the PRD commits to publishing the real distribution rather than a selected one.

Table shape:

```markdown
| Segment | Baseline p50 | Baseline p95 | Final p50 | Final p95 | Δ p50 |
|---|---:|---:|---:|---:|---:|
| Speech end → request sent | | | | | |
| Request → first byte | | | | | |
| Server: db read | | | | | |
| Server: limiter wait | | | | | |
| Server: model TTFT | | | | | |
| **Speech end → first audio (TTFA)** | | | | | |
```

and a per-intervention table:

```markdown
| # | Intervention | Segment moved | Δ p50 | Verdict |
|---|---|---|---:|---|
| 1 | SSE streaming, speak at first sentence | TTFA | | |
| 2 | Cap the limiter's queue wait | limiter_wait_ms | | |
| 3 | Parallel reads, deferred writes | db_read_ms | | |
| 4 | Bound memory facts and history | model TTFT | | |
| 5 | STT endpointing | stt_tail_ms | | |
| 6 | Warm the TTS voice list | first-turn TTFA | | |
| 7 | Gemini vs Groq | model TTFT | | |
| 8 | MCP vs local function tool | tool turn total | | |
```

- [ ] **Step 3: Write the caveats section**

State plainly: browser TTS is local, so the number being optimized is mostly the LLM path; the client-side segments come from ten hand-driven turns rather than a headless harness; the voice-warming row has a smaller sample; every number is from the deployed app on a paid Render instance, so a cold free-tier start is not included.

- [ ] **Step 4: Commit**

```bash
git add docs/latency/
git commit -m "docs: publish the latency before/after results"
```

---

## Task 16: Documentation, OpenAPI, and the presentation

Phase 11's deliverable, plus the housekeeping the new endpoints created. **Reserve the last 90 minutes for this and do not spend it on code.**

**Files:**
- Modify: `docs/openapi.json`, `README.md`, `sarjy-backend/RUNBOOK.md`, `CLAUDE.md`, `todo.md`, `docs/ARCHITECTURE.md`

**Interfaces:**
- Consumes: everything above.
- Produces: a repository a reviewer can read without running it, and a five-minute talk.

- [ ] **Step 1: Regenerate the OpenAPI document**

From `sarjy-backend/`:

```bash
python scripts/export_openapi.py
```

Expected: `/api/health` and `/api/chat/stream` appear in `docs/openapi.json`, and `ChatResponse` carries `timings`.

- [ ] **Step 2: Update the runbook**

Add to `sarjy-backend/RUNBOOK.md`: the new env vars (`LLM_RATE_LIMIT_MAX_WAIT_SECONDS`, `MEMORY_FACTS_LIMIT`, `USE_LOCAL_WEATHER_TOOL`), a deployment section (Render + Neon, the Docker image, the loopback MCP process), the harness commands, and the new log lines to grep for (`stream_chat start/complete`, `Rate limiter: refusing to queue`).

- [ ] **Step 3: Update the README and the architecture doc**

README: the live URL, "open in Chrome", a short "what to look at" pointing straight at `docs/latency/RESULTS.md`, and how to run the harness. ARCHITECTURE §7: change the "Planned" deployment paragraph to describe what is actually deployed, and update the request-flow section to show the streamed path.

Also update `CLAUDE.md`: the note claiming the UI stores sessions in `localStorage` is already stale, and the streaming endpoint plus the timing layer are new facts a future session needs.

- [ ] **Step 4: Record the Loom**

Five minutes, in this order: the deployed URL and a spoken turn; memory across sessions; weather over MCP; barge-in; then the results table with the TTFA readout on screen. Share it before the meeting.

- [ ] **Step 5: Write the five-minute talk**

One page of notes. Lead with the number that moved, name the hypothesis that was wrong, and end on what another week would buy — realtime speech-to-speech, server-side streaming TTS with sentence chunking, speculative tool prefetch, deploying closer to the user, warm connection pooling. They stop at five minutes and thirty seconds.

- [ ] **Step 6: Commit and send the final update**

Tick the remaining boxes in `todo.md`, then:

```bash
git add docs/ README.md CLAUDE.md sarjy-backend/RUNBOOK.md todo.md
git commit -m "docs: deployment, streaming, and latency results"
```

Send the final update with the deployment URL and the repository URL (todo #26).

---

## Cut order

If day 2 runs short, drop from the bottom of this list first — matching the spec's own cut order:

1. Task 14 (MCP overhead measurement)
2. Task 13 (provider comparison)
3. Task 10 (TTS voice warming)
4. Task 8 (memory and history trimming)

Tasks 1–5 (instrumentation, baseline, streaming), 15 and 16 are **not cuttable**. Without instrumentation there is no deep dive; without streaming there is no result; without the write-up there is nothing to show for either.
