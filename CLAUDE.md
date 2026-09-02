# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repo layout

Two independent apps, no shared package/monorepo tooling:

- `sarjy-backend/` — FastAPI + Postgres backend, OpenAI Agents SDK
- `sarjy-ui/` — React 19 + Vite frontend
- `sarjy-mcp-server/` — standalone MCP server (Streamable HTTP) exposing tools to the backend agent, starting with `get_weather`
- `prompts/` — original spec prompts used to scaffold the apps (e.g. `ui_init.md` for the UI)

There is no root build/test command; work in each subdirectory separately.

Three deployment shapes exist at the repo root:

- `docker-compose.yml` — the whole application as five services (Postgres, LiteLLM, `mcp`, `backend`, `ui`), each app service built from its own `Dockerfile` in its subdirectory. `docker compose up -d --build`, then open `http://localhost:8080`. Only the UI is published; nginx in the `ui` image serves the built frontend and proxies `/api` to `backend:8000`, so there is one origin and no CORS. Postgres and LiteLLM are also published for local work against a non-containerized backend.
- `Dockerfile` at the root — the same four processes in a single container (LiteLLM and the MCP server on loopback), for Render, which runs one image per service rather than a compose file. `render.yaml` is its blueprint. LiteLLM lives in its own virtualenv at `/opt/litellm` there, because `litellm[proxy]` pins `mcp<2.0.0` while `sarjy-mcp-server` needs 2.x.
- `docker-compose.prod.yml` + `Caddyfile` — the compose stack for a public host (a DigitalOcean droplet, HTTPS at a DuckDNS subdomain); `docs/DEPLOY.md` is the runbook. Standalone rather than an override of `docker-compose.yml`, because Compose appends to `ports:` when merging and the local file's 5432/4000/8080 publishes must not exist on a public IP — Docker publishes bypass `ufw`. Caddy is the only service with published ports and gets the Let's Encrypt certificate itself; HTTPS is required for the browser to grant microphone access to the speech input.

## Backend (`sarjy-backend/`)

Setup:
```
python -m venv .venv && .venv\Scripts\activate  # already present as .venv
pip install -r requirements.txt
docker compose -f ../docker-compose.yml up -d   # Postgres on 5432; or run from the repo root
```

Run:
```
uvicorn app.main:app --reload --port 8000
```

Config is env-driven via `app/core/config.py` (pydantic-settings, reads `.env`). Copy `.env.example` to `.env` and set `OPENAI_API_KEY`. No migrations tool — tables are created on startup via `Base.metadata.create_all` in the `lifespan` handler in `app/main.py`.

Tests: `pip install -r requirements-dev.txt`, then `.venv/Scripts/python.exe -m pytest` from `sarjy-backend/`.

### Architecture

Two chat endpoints (`app/routers/chat.py`), both taking `{user_id, session_id, message}` (both ids are client-generated UUIDs) and persisting identically, plus session reads in `app/routers/sessions.py`:

- `POST /api/chat` — returns `{reply, timings}`. Kept unchanged as the "before" column of the latency comparison; do not repurpose it.
- `POST /api/chat/stream` — `text/event-stream`, one `data:` frame per token (`delta`), then one `done` frame with the reply and timings, or an `error` frame under HTTP 200 (the response has usually already begun). This is what the UI uses.

Request flow (`app/services/chat.py::handle_chat`, and `app/services/streaming.py::stream_chat`):
1. Upsert `User` / `Session` rows if new (`app/models/`).
2. Persist the incoming user `Message` — flushed on the non-streaming path, **committed** on the streamed one, because its history read runs in a separate Session.
3. Load the last `chat_history_limit` messages plus the newest `memory_facts_limit` `Memory` rows (durable cross-session facts). The streamed path runs the two reads concurrently via `asyncio.to_thread`, each with its own `SessionLocal` — SQLAlchemy's sync `Session` is not thread-safe.
4. Build an `Agent` (`app/agent/sarjy_agent.py::build_agent`) with those memory facts injected into the system prompt, and run it via `agents.Runner.run` (or `Runner.run_streamed`), passing history as `input`.
5. Retry on `openai.RateLimitError` using `llm_retry_backoff_seconds` (`_run_with_retry`); any other exception rolls back the DB transaction and surfaces as `LLMUnavailableError` -> HTTP 502.
6. Persist the assistant reply and commit.

Every turn is instrumented with `app/core/timing.py::Timings` — named spans returned on the wire and logged (`db_read_ms`, `db_write_pre_ms`, `limiter_wait_ms`, `llm_ttft_ms`, `llm_total_ms`, `db_write_ms`, `total_ms`). `llm_ttft_ms` exists only on the streamed path; `llm_total_ms` only on the non-streamed one. The harness that turns these into p50/p95 tables is `scripts/measure.py`, with results in `docs/latency/`.

A process-local `TokenBucketRateLimiter` (`app/core/rate_limiter.py`) throttles outbound LLM calls to `llm_rate_limit_per_minute`. It queues rather than rejecting, but only up to `llm_rate_limit_max_wait_seconds`; past that it raises `RateLimitedError`, which becomes a 429 with `Retry-After` or an `error` frame.

The agent (`app/agent/sarjy_agent.py`) exposes one local tool, `save_memory`, which the LLM calls to persist durable facts about the user into the `memories` table — this is how "remembers things across sessions" works, separate from the recent-message history. Everything else (currently just `get_weather`) comes from `sarjy-mcp-server` via `mcp_servers=[sarjy_mcp_server]` on the `Agent` — see `app/agent/mcp.py` for the client singleton, connected/cleaned up once in `app/main.py`'s `lifespan` (`MCP_SERVER_URL` in config).

The agent also carries a local copy of the weather tool (`app/agent/local_weather.py`) behind `USE_LOCAL_WEATHER_TOOL`. It exists only to measure what the MCP transport hop costs and ships `false` — the MCP server is the shipped path.

DB models (`app/models/`): `User` (1) -> `Session` (many) -> `Message` (many); `Memory` belongs to a `User` and optionally references the `Session` it was learned in.

### Note on session persistence

Sessions and messages are read back from Postgres through `app/routers/sessions.py`; `localStorage` holds only the user id and which chat was last open (`sarjy-ui/src/hooks/useSessions.js`).

## MCP server (`sarjy-mcp-server/`)

Setup:
```
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
```

Run:
```
python server.py   # Streamable HTTP on MCP_SERVER_HOST:MCP_SERVER_PORT (default 0.0.0.0:8100), path /mcp
```

Config is env-driven via `config.py` (pydantic-settings, `MCP_SERVER_` prefix, reads `.env`; copy `.env.example` to `.env`). Standalone process — not spawned by the backend, must be running before the backend connects to it. `server.py` defines an `MCPServer("sarjy-tools")` (the `mcp` package's `MCPServer`, formerly `FastMCP` pre-2.x) with one tool, `get_weather`. Add more tools here as they come up; the backend picks up whatever the server exposes automatically.

No test suite exists yet.

## Frontend (`sarjy-ui/`)

```
npm install
npm run dev      # Vite dev server, proxies /api -> http://localhost:8000 (vite.config.js)
npm run build
npm run lint      # oxlint
```

No test suite exists yet.

### Architecture

`App.jsx` is the composition root: wires together session state, chat state, speech I/O, and the presentational components (`ChatWindow`, `MessageInput`, `SessionList`, `TurnTimings`).

- `hooks/useSessions.js` — owns the list of chat sessions, the active session, and message arrays. Session titles auto-derive from the first user message.
- `api.js` — `getUserId()` (persists a UUID in `localStorage` under `sarjy_user_id`), `sendMessageStream(...)` (the path the UI takes: reads the SSE frames off `POST /api/chat/stream`), and `sendMessage(...)` for the non-streaming route.
- `hooks/useSpeechRecognition.js` / `hooks/useSpeechSynthesis.js` — wrap the browser's native `SpeechRecognition`/`webkitSpeechRecognition` and `SpeechSynthesis` APIs (STT/TTS). Both must degrade gracefully when unsupported (feature-detected, not polyfilled).
- `timing.js` — one timer per turn (speech end, request sent, first byte, first audio), published as a `[sarjy-timing]` console line and rendered live by `components/TurnTimings.jsx`. A demo readout only: the latency study in `docs/latency/` is backend-side and does not consume these lines.

Voice flow: a final STT transcript is sent exactly like a typed message (same `handleSend` in `App.jsx`). The reply streams in, and `App.jsx` splits it on sentence boundaries so TTS starts at the first sentence rather than the last token — whole sentences, because token-by-token speech has no prosody. Recognition finalizes at `onspeechend` rather than waiting out the engine's silence timeout, with the last interim transcript as a fallback and a `sent` guard so the two paths cannot both fire. A hands-free toggle keeps the mic open between turns and arms barge-in: speaking over Sarjy cancels playback. It is opt-in because a hot mic during playback can hear the speakers.

### when commiting anything commit it with my username do not use Claude