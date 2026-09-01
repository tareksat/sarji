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

Config is env-driven via `app/config.py` (pydantic-settings, reads `.env`). Copy `.env.example` to `.env` and set `OPENAI_API_KEY`. No migrations tool — tables are created on startup via `Base.metadata.create_all` in the `lifespan` handler in `app/main.py`.

No test suite exists yet.

### Architecture

Single endpoint: `POST /api/chat` (`app/main.py`) taking `{user_id, session_id, message}` (both ids are client-generated UUIDs) and returning `{reply}`.

Request flow (`app/chat_service.py::handle_chat`):
1. Upsert `User` / `Session` rows if new (`app/models.py`).
2. Persist the incoming user `Message`.
3. Load the last `chat_history_limit` messages for the session, plus all `Memory` rows for the user (durable cross-session facts).
4. Build an `Agent` (`app/agent/sarjy_agent.py::build_agent`) with those memory facts injected into the system prompt, and run it via `agents.Runner.run`, passing history as `input`.
5. Retry on `openai.RateLimitError` using `llm_retry_backoff_seconds` (`_run_with_retry`); any other exception rolls back the DB transaction and surfaces as `LLMUnavailableError` -> HTTP 502.
6. Persist the assistant reply and commit.

A process-local `TokenBucketRateLimiter` (`app/rate_limiter.py`) throttles outbound LLM calls to `llm_rate_limit_per_minute`, queuing rather than rejecting.

The agent (`app/agent/sarjy_agent.py`) exposes one local tool, `save_memory`, which the LLM calls to persist durable facts about the user into the `memories` table — this is how "remembers things across sessions" works, separate from the recent-message history. Everything else (currently just `get_weather`) comes from `sarjy-mcp-server` via `mcp_servers=[sarjy_mcp_server]` on the `Agent` — see `app/agent/mcp.py` for the client singleton, connected/cleaned up once in `app/main.py`'s `lifespan` (`MCP_SERVER_URL` in config).

DB models (`app/models.py`): `User` (1) -> `Session` (many) -> `Message` (many); `Memory` belongs to a `User` and optionally references the `Session` it was learned in.

### Note on session persistence

Sessions/messages are persisted server-side (Postgres), but there is currently no GET endpoint to read them back — the UI's session list, titles, and message history are stored purely client-side in `localStorage` (`sarjy-ui/src/hooks/useSessions.js`) and keyed by the same UUID the backend uses. Clearing browser storage loses the visible history even though the DB rows remain.

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

`App.jsx` is the composition root: wires together session state, chat state, speech I/O, and the three presentational components (`ChatWindow`, `MessageInput`, `SessionList`).

- `hooks/useSessions.js` — owns the list of chat sessions, the active session, and message arrays; persists to `localStorage` under `sarjy_sessions` / `sarjy_active_session`. Session titles auto-derive from the first user message.
- `api.js` — `getUserId()` (persists a UUID in `localStorage` under `sarjy_user_id`) and `sendMessage(userId, sessionId, message)`, the single point that calls `POST /api/chat`.
- `hooks/useSpeechRecognition.js` / `hooks/useSpeechSynthesis.js` — wrap the browser's native `SpeechRecognition`/`webkitSpeechRecognition` and `SpeechSynthesis` APIs (STT/TTS). Both must degrade gracefully when unsupported (feature-detected, not polyfilled).

Voice flow: a final STT transcript is sent exactly like a typed message (same `handleSend` in `App.jsx`); an assistant reply is spoken automatically via TTS unless muted, and any in-flight speech is cancelled when a new message is sent.

### when commiting anything commit it with my username do not use Claude