# Sarjy — Deploy the Floor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Get the already-built floor — chat, memory, voice, session history, weather over MCP — onto one public HTTPS URL a reviewer can open with no setup.

**Architecture:** No behavior changes. A health endpoint is added, FastAPI mounts the built Vite `dist/` so the deployment is one origin and one URL (no CORS), and a two-stage Docker image carries the API, the built frontend, and the MCP server as a loopback process in the same container. Render runs the image against a Neon Postgres instance.

**Tech Stack:** FastAPI, SQLAlchemy 2.x, `openai-agents`, `mcp` (Streamable HTTP), Postgres 16 (Neon in production), React 19 + Vite 8, Docker, Render.

**Spec:** [`docs/IMPLEMENTATION-PLAN.md`](../../IMPLEMENTATION-PLAN.md) phase 0, [`docs/PRD.md`](../../PRD.md) §6 "Serving", [`docs/ARCHITECTURE.md`](../../ARCHITECTURE.md) §7 "Deployment", [`todo.md`](../../../todo.md) #8, #9, #11.

**Next plan:** [`2026-09-01-b-latency-deep-dive.md`](2026-09-01-b-latency-deep-dive.md) — do not start it until this plan's exit gate is met.

## Status going in

Phases 0–7 of the implementation plan are **coded but not deployed**. Present and working locally: DB models and lifespan `create_all`, `POST /api/chat` with memory + retry + token bucket, the session CRUD API, the React chat UI, both speech hooks, the weather tool served over MCP from `sarjy-mcp-server/`.

Missing, and covered by this plan:

| Gap | Spec reference |
|---|---|
| No `GET /api/health` | Implementation plan phase 0 |
| FastAPI does not serve the built UI | PRD §6 "Serving"; todo #8 |
| No Dockerfile, no Render config, nothing deployed | Phase 0 "done when"; todo #9 |
| No scripted check of the session endpoints | Implementation plan, "Verification" |

## Global Constraints

- **No test suite.** This is a deliberate cut recorded in the PRD's non-goals and in `CLAUDE.md`. Verification is per task, by `curl`, by browser, or by a script — never by a unit test framework. Do not add pytest or vitest.
- **The floor stays working.** Nothing in this plan changes what `POST /api/chat` or the session endpoints do. Every task ends with the app still able to hold a conversation.
- **Provider is config, not code.** `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL` are the only things that change between providers. No adapter layer.
- **Commit after every task**, with a `feat:` / `chore:` prefix. The branch is `UI`; do not merge to `main` without asking.
- **Chrome only** for voice. Any UI regression must still leave a working text-only interface in other browsers.
- **Secrets stay out of the repo.** The Neon connection string and the provider key live in Render's environment, never in `.env.example` or a commit.

## File Structure

**Created**

| Path | Responsibility |
|---|---|
| `sarjy-backend/app/routers/health.py` | `GET /api/health` liveness probe |
| `sarjy-backend/scripts/smoke_sessions.py` | Exercises health + session CRUD + the delete cascade against a target URL |
| `Dockerfile` (repo root) | Two-stage build: Vite build, then Python image serving both processes |
| `start.sh` (repo root) | Launches LiteLLM and the MCP server on loopback, then uvicorn in the foreground |
| `render.yaml` (repo root) | Render blueprint — Docker service, health check path, env vars |
| `.dockerignore` (repo root) | Keeps `.venv`, `node_modules`, `logs` out of the build context |
| `.gitattributes` (repo root) | Pins `start.sh` to LF so the container's shebang survives a Windows checkout |
| `litellm/requirements.txt` | Pinned `litellm[proxy]`, installed into its own virtualenv in the image |

**Modified**

| Path | Change |
|---|---|
| `sarjy-backend/app/main.py` | Health router, static mount for the built UI, MCP connect stays |
| `README.md` | Deployed URL, "open in Chrome" |
| `todo.md` | Checkboxes ticked as tasks land |

---

## Task 1: Health endpoint, static UI serving, and a smoke script

Closes the phase-0 gap (`GET /api/health` never existed) and todo #8. One origin means the CORS middleware becomes redundant in production but stays for the Vite dev server on 5173.

**Files:**
- Create: `sarjy-backend/app/routers/health.py`
- Create: `sarjy-backend/scripts/smoke_sessions.py`
- Modify: `sarjy-backend/app/main.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `GET /api/health` → `{"status": "ok"}`; a static mount at `/` serving `sarjy-backend/app/static/` when that directory exists; `python scripts/smoke_sessions.py --base-url URL` exiting non-zero on failure.

- [ ] **Step 1: Add the health router**

Create `sarjy-backend/app/routers/health.py`:

```python
from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get(
    "/api/health",
    summary="Liveness probe",
    response_description="Always `{\"status\": \"ok\"}` when the process is up.",
)
async def health() -> dict[str, str]:
    """Report that the API process is running.

    Deliberately does not touch the database: this is the target of the
    platform's health check, and a slow database should not cycle the service.
    """
    return {"status": "ok"}
```

- [ ] **Step 2: Mount the router and the built UI**

In `sarjy-backend/app/main.py`, add to the imports:

```python
from fastapi.staticfiles import StaticFiles

from .routers.health import router as health_router
```

Then replace the two `include_router` lines at the bottom of the file with:

```python
app.include_router(health_router)
app.include_router(chat_router)
app.include_router(sessions_router)

# The Vite build is copied here by the Docker build. Mounted last so that every
# /api route above wins, and only when present so local `uvicorn --reload` runs
# without a frontend build.
UI_DIST = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(UI_DIST):
    app.mount("/", StaticFiles(directory=UI_DIST, html=True), name="ui")
    logger.info("Serving built UI from %s", UI_DIST)
else:
    logger.info("No built UI at %s — API only", UI_DIST)
```

- [ ] **Step 3: Verify the health endpoint locally**

Run, from `sarjy-backend/` with the venv active and Postgres up:

```bash
uvicorn app.main:app --port 8000
curl -s http://localhost:8000/api/health
```

Expected: `{"status":"ok"}`, and a log line `No built UI at ... — API only`.

- [ ] **Step 4: Write the smoke script**

Create `sarjy-backend/scripts/smoke_sessions.py`:

```python
"""End-to-end check of the session endpoints and the delete cascade.

Usage:
    python scripts/smoke_sessions.py --base-url http://localhost:8000

Exits non-zero on the first failed assertion. Uses a throwaway user id, so it
is safe to run against the deployed app.
"""

import argparse
import sys
import uuid

import httpx

TIMEOUT_SECONDS = 60.0


def check(condition: bool, message: str) -> None:
    if not condition:
        print(f"FAIL: {message}")
        sys.exit(1)
    print(f"ok: {message}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:8000")
    args = parser.parse_args()

    base = args.base_url.rstrip("/")
    user_id = str(uuid.uuid4())
    session_id = str(uuid.uuid4())
    other_user = str(uuid.uuid4())

    with httpx.Client(base_url=base, timeout=TIMEOUT_SECONDS) as client:
        resp = client.get("/api/health")
        check(resp.status_code == 200 and resp.json()["status"] == "ok", "health returns ok")

        resp = client.post(
            "/api/chat",
            json={"user_id": user_id, "session_id": session_id, "message": "Remember I live in Riyadh."},
        )
        check(resp.status_code == 200, f"chat turn succeeded (got {resp.status_code})")

        resp = client.get("/api/sessions", params={"user_id": user_id})
        check(resp.status_code == 200 and len(resp.json()) == 1, "session list has one row")

        resp = client.get(f"/api/sessions/{session_id}/messages", params={"user_id": user_id})
        check(resp.status_code == 200 and len(resp.json()) >= 2, "message list has the turn")

        resp = client.get(f"/api/sessions/{session_id}/messages", params={"user_id": other_user})
        check(resp.status_code == 404, "another user's session returns 404")

        resp = client.patch(
            f"/api/sessions/{session_id}", params={"user_id": user_id}, json={"title": "renamed"}
        )
        check(resp.status_code == 200 and resp.json()["title"] == "renamed", "rename works")

        resp = client.delete(f"/api/sessions/{session_id}", params={"user_id": user_id})
        check(resp.status_code in (200, 204), "delete works")

        resp = client.get("/api/sessions", params={"user_id": user_id})
        check(resp.json() == [], "session list is empty after delete")

    print("\nAll session checks passed.")


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run the smoke script**

Run: `python scripts/smoke_sessions.py --base-url http://localhost:8000`
Expected: every line prefixed `ok:`, ending in `All session checks passed.` If the chat turn fails with 502, the LLM env vars are wrong — fix those before continuing, the rest of this plan depends on a working turn.

- [ ] **Step 6: Commit**

```bash
git add sarjy-backend/app/routers/health.py sarjy-backend/app/main.py sarjy-backend/scripts/smoke_sessions.py
git commit -m "feat: add health endpoint, static UI mount, and a session smoke script"
```

---

## Task 2: Docker image running all three processes

Everything — API, built UI, MCP server, and the LiteLLM proxy — ships as one image. Both helpers bind loopback inside the container: `MCP_SERVER_URL` stays `http://127.0.0.1:8100/mcp`, `LLM_BASE_URL` stays `http://127.0.0.1:4000`, nothing but the API is reachable from outside, and neither costs a second cold start or a cross-service hop on the path the deep dive measures. Keeping LiteLLM in production is what keeps provider switching a `model_name` change in `litellm/config.yaml` rather than a code change. This is the risk phase 7 of the spec flagged — verify it in a container locally before touching Render.

**Files:**
- Create: `Dockerfile`, `start.sh`, `.dockerignore`, `.gitattributes` (repo root), `litellm/requirements.txt`
- Modify: `sarjy-mcp-server/requirements.txt` (pin `mcp`)

**Interfaces:**
- Consumes: `sarjy-backend/app/main.py` static mount from Task 1; `litellm/config.yaml`.
- Produces: an image whose container serves the UI at `/` and the API at `/api/*` on `$PORT` (default 8000), with LiteLLM and the MCP server on loopback.

- [ ] **Step 1: Write `.dockerignore`**

Create `.dockerignore` at the repo root:

```
**/.venv
**/node_modules
**/__pycache__
**/logs
**/.env
**/dist
.git
docs
```

- [ ] **Step 2: Write the Dockerfile**

Create `Dockerfile` at the repo root:

```dockerfile
# Stage 1 — build the frontend.
FROM node:22-alpine AS ui
WORKDIR /ui
COPY sarjy-ui/package.json sarjy-ui/package-lock.json ./
RUN npm ci
COPY sarjy-ui/ ./
RUN npm run build

# Stage 2 — API + MCP server + the built frontend, one image.
FROM python:3.12-slim
WORKDIR /srv

COPY sarjy-backend/requirements.txt backend-requirements.txt
COPY sarjy-mcp-server/requirements.txt mcp-requirements.txt
COPY litellm/requirements.txt litellm-requirements.txt
RUN pip install --no-cache-dir -r backend-requirements.txt -r mcp-requirements.txt

# LiteLLM gets its own virtualenv: litellm[proxy] pins mcp<2.0.0, while the MCP
# server imports mcp.server.mcpserver, which exists only in 2.x. One
# site-packages cannot satisfy both, and the proxy is a process we talk to over
# HTTP rather than a library we import.
RUN python -m venv /opt/litellm \
    && /opt/litellm/bin/pip install --no-cache-dir -r litellm-requirements.txt

COPY sarjy-backend/ /srv/backend/
COPY sarjy-mcp-server/ /srv/mcp/
COPY litellm/config.yaml /srv/litellm/config.yaml
COPY --from=ui /ui/dist /srv/backend/app/static
COPY start.sh /srv/start.sh
RUN chmod +x /srv/start.sh

ENV PYTHONUNBUFFERED=1 \
    MCP_SERVER_HOST=127.0.0.1 \
    MCP_SERVER_PORT=8100 \
    MCP_SERVER_URL=http://127.0.0.1:8100/mcp \
    LLM_BASE_URL=http://127.0.0.1:4000

EXPOSE 8000
CMD ["/srv/start.sh"]
```

Create `litellm/requirements.txt`, pinned so a rebuild cannot silently move the proxy:

```
litellm[proxy]==1.83.0
```

And pin the MCP server's own dependency in `sarjy-mcp-server/requirements.txt` — the shared image resolved it down to 1.29.1 and `server.py` crashed on import:

```
# Pinned: server.py imports mcp.server.mcpserver.MCPServer, which is 2.x only.
# In the deployed image this package shares a site-packages with litellm, whose
# resolution otherwise pulls mcp back to 1.x and breaks that import.
mcp==2.1.1
httpx
pydantic-settings
```

- [ ] **Step 3: Write the start script and pin its line endings**

Create `start.sh` at the repo root, LF line endings:

```sh
#!/bin/sh
set -e

# Three processes, one container. Both helpers bind loopback: nothing but the
# API is reachable from outside, and neither costs a second cold start.

# DATABASE_URL is unset for LiteLLM only: it belongs to the API, and LiteLLM
# reads it as a request to run in Prisma-backed mode, which this image has no
# client for.
env -u DATABASE_URL /opt/litellm/bin/litellm \
    --config /srv/litellm/config.yaml --host 127.0.0.1 --port 4000 &
LITELLM_PID=$!

cd /srv/mcp
python server.py &
MCP_PID=$!

# Give the helpers a moment to bind before the API's lifespan connects to MCP.
sleep 5

trap 'kill "$LITELLM_PID" "$MCP_PID" 2>/dev/null' TERM INT

cd /srv/backend
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
```

LF is not enough on its own: Git's `autocrlf` rewrites the file on a Windows checkout and the container then fails with `no such file or directory` on the shebang. Create `.gitattributes` at the repo root:

```
# The container's entrypoint is read by /bin/sh. A CRLF shebang fails there with
# "no such file or directory", so this file must stay LF on every platform.
start.sh text eol=lf
```

- [ ] **Step 4: Build and run the container against local Postgres**

```bash
docker build -t sarjy .
docker run -d --name sarjy-test -p 8002:8000 \
  --env-file .env --env-file sarjy-backend/.env \
  -e DATABASE_URL="postgresql+psycopg://sarjy:sarjy@host.docker.internal:5432/sarjy" \
  sarjy
docker logs sarjy-test
```

The root `.env` carries the provider keys LiteLLM reads; the backend `.env` carries the rest. Expected: three `Application startup complete` lines — MCP on 127.0.0.1:8100, LiteLLM on 127.0.0.1:4000, the API on 0.0.0.0:8000 — plus `Serving built UI from /srv/backend/app/static`, and no traceback.

- [ ] **Step 5: Verify the container serves every half**

```bash
curl -s http://localhost:8002/api/health
curl -s http://localhost:8002/ | head -c 200
python sarjy-backend/scripts/smoke_sessions.py --base-url http://localhost:8002
```

Expected: `{"status":"ok"}`; the built `index.html`; all smoke checks pass. Then prove the two loopback hops in one turn — a chat POST asking for the current weather in a named city must come back with a temperature, which means the API reached LiteLLM, the model called the tool, and the tool call reached the MCP server. Finally, teach a location in one session id and ask "What's the weather right now?" under a second session id on the same user: an answer with no follow-up question is the cross-session memory requirement, proven inside the container.

- [ ] **Step 6: Commit**

```bash
docker rm -f sarjy-test
git add Dockerfile start.sh .dockerignore .gitattributes litellm/requirements.txt sarjy-mcp-server/requirements.txt
git commit -m "chore: build and serve UI, API, MCP server, and LiteLLM from one image"
```

---

## Task 3: Deploy to Render with Neon Postgres

Closes phase 0's "done when" and todo #9. Nothing measured before this point counts.

**Files:**
- Create: `render.yaml` (repo root)
- Modify: `README.md`

**Interfaces:**
- Consumes: the image from Task 2.
- Produces: a public HTTPS URL, referenced here and throughout the deep-dive plan as `$SARJY_URL`.

- [ ] **Step 1: Create the Neon database**

Create a Neon project, copy the pooled connection string, and convert it to SQLAlchemy's driver form: `postgresql+psycopg://USER:PASSWORD@HOST/DB?sslmode=require`. Keep it out of the repo — it goes into Render's environment, never into `.env.example`.

- [ ] **Step 2: Write the Render blueprint**

Create `render.yaml` at the repo root:

```yaml
services:
  - type: web
    name: sarjy
    runtime: docker
    dockerfilePath: ./Dockerfile
    dockerContext: .
    plan: starter
    healthCheckPath: /api/health
    envVars:
      - key: DATABASE_URL
        sync: false          # set in the Render dashboard from the Neon string
      # A model_name from litellm/config.yaml — gpt-4o-mini, groq-oss, or
      # gemini-flash. Switching providers is this one value.
      - key: LLM_MODEL
        value: "groq-oss"
      # LiteLLM runs in this container on loopback; LLM_API_KEY must equal
      # LITELLM_MASTER_KEY, and provider keys are read by LiteLLM, not the API.
      - key: LLM_BASE_URL
        value: "http://127.0.0.1:4000"
      - key: LLM_API_KEY
        sync: false
      - key: LITELLM_MASTER_KEY
        sync: false
      - key: GROQ_API_KEY
        sync: false
      - key: GEMINI_API_KEY
        sync: false
      - key: OPENAI_API_KEY
        sync: false
      - key: LLM_RATE_LIMIT_PER_MINUTE
        value: "20"
      - key: CHAT_HISTORY_LIMIT
        value: "20"
      - key: LOG_LEVEL
        value: "INFO"
      - key: MCP_SERVER_URL
        value: "http://127.0.0.1:8100/mcp"
```

Note the tradeoff in the commit: the free plan sleeps and its cold start would land inside the latency numbers, so the paid starter plan is used for the measurement window.

- [ ] **Step 3: Deploy**

Push the branch, create the Render service from the blueprint, and set the `sync: false` variables in the dashboard:

| Variable | Value |
|---|---|
| `DATABASE_URL` | the Neon string in `postgresql+psycopg://…?sslmode=require` form |
| `LITELLM_MASTER_KEY` | any strong secret — this is the proxy's own auth |
| `LLM_API_KEY` | **the same value** as `LITELLM_MASTER_KEY`; the API authenticates to the proxy with it |
| `GROQ_API_KEY` / `GEMINI_API_KEY` / `OPENAI_API_KEY` | whichever provider keys the `litellm/config.yaml` models need — set at least the one `LLM_MODEL` selects |

`LLM_BASE_URL` and `LLM_MODEL` are already fixed in the blueprint: the proxy is on loopback, and the provider is chosen by `LLM_MODEL` naming a `model_name` from `litellm/config.yaml`.

- [ ] **Step 4: Verify the deployment**

```bash
curl -s $SARJY_URL/api/health
python sarjy-backend/scripts/smoke_sessions.py --base-url $SARJY_URL
```

Expected: `ok` on every line. Then, in Chrome on the deployed URL: the microphone permission prompt appears (confirming real HTTPS), a spoken question gets a spoken answer, and "What's the weather?" in a fresh session — after a previous session taught the location — answers without asking for a city. That last check proves memory, MCP, and the external API in one breath, per phase 6's "done when".

- [ ] **Step 5: Record the URL**

Add to `README.md`, near the top:

```markdown
## Live

**<$SARJY_URL>** — open in **Chrome**. Voice input uses the Web Speech API,
which Safari and Firefox do not implement; those browsers get the text-only
interface and a banner saying so.
```

- [ ] **Step 6: Commit and tick the checklist**

Tick todo #8 and #9 in `todo.md`, then:

```bash
git add render.yaml README.md todo.md
git commit -m "chore: deploy to Render with Neon Postgres"
```

Send the one-line progress update (todo #11) with the URL.


---

## Exit gate

Do not start [`2026-09-01-b-latency-deep-dive.md`](2026-09-01-b-latency-deep-dive.md) until all four hold:

1. `curl $SARJY_URL/api/health` returns `{"status":"ok"}` over HTTPS.
2. `python sarjy-backend/scripts/smoke_sessions.py --base-url $SARJY_URL` passes every check.
3. In Chrome on `$SARJY_URL`: the microphone prompt appears, and a spoken question gets a spoken answer with no keyboard involved.
4. "What's the weather?" is answered without asking for a city, in a session that never mentioned one — memory and the MCP-served tool composing on the deployed app.

The deep dive measures the deployed application. Until this gate is met there is nothing valid to measure.
