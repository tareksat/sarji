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
