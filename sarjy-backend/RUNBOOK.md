# Sarjy Backend Runbook

## Start

```
docker compose -f ../docker-compose.yml up -d   # Postgres, port 5432
uvicorn app.main:app --reload --port 8000
```

Requires `.env` (copy from `.env.example`), `OPENAI_API_KEY` set. No migrations — tables auto-created on startup.

## Config (`.env`)

| Var | Default | Notes |
|---|---|---|
| `DATABASE_URL` | local postgres | |
| `OPENAI_API_KEY` | — | required |
| `CORS_ORIGIN` | `http://localhost:5173` | UI origin |
| `LLM_RATE_LIMIT_PER_MINUTE` | 20 | outbound LLM call cap |
| `CHAT_HISTORY_LIMIT` | 20 | messages replayed per turn |
| `LLM_RETRY_BACKOFF_SECONDS` | `[1,2]` | retry delays on rate limit |
| `LOG_LEVEL` | `INFO` | `DEBUG`/`INFO`/`WARNING`/`ERROR` |

## Logs

- Console (stdout, wherever uvicorn runs) + `logs/app.log`.
- Daily rotation at midnight, 7 days kept (`logs/app.log.YYYY-MM-DD`).
- Tail: `Get-Content logs/app.log -Wait` (PowerShell) or `tail -f logs/app.log`.
- Bump verbosity: set `LOG_LEVEL=DEBUG` in `.env`, restart.

## Key log lines to grep for

| Line prefix | Meaning |
|---|---|
| `handle_chat start/complete` | one chat turn, by `user_id`/`session_id` |
| `Rate limited by OpenAI on attempt` | OpenAI 429, retrying |
| `handle_chat failed` | turn failed after retries — ERROR + traceback, root cause of a 502 |
| `Returning 502 for` | client saw a 502 |
| `Rate limiter: waiting` | local token bucket throttling before an LLM call |
| `Saved memory for` | agent persisted a durable fact |

## Common issues

**Client gets 502** — grep `logs/app.log` for `handle_chat failed` at the matching timestamp; the traceback under it is the real cause (usually `OPENAI_API_KEY` invalid/expired, or OpenAI outage).

**Requests feel slow / queued** — check for repeated `Rate limiter: waiting` lines; raise `LLM_RATE_LIMIT_PER_MINUTE` if the OpenAI plan allows it.

**DB connection errors on startup** — Postgres container not up; `docker compose -f ../docker-compose.yml ps`, then `up -d`.

**"Sarjy" not remembering things across sessions** — check `Saved memory for` lines fired during the conversation; if absent, the model chose not to call `save_memory` (facts, not small talk, trigger it).

## No test suite

Verify manually: hit `POST /api/chat` with `{user_id, session_id, message}`, watch `logs/app.log`.
