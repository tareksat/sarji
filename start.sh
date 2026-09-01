#!/bin/sh
set -e

cd /srv/mcp
python server.py &
MCP_PID=$!

# Give the MCP server a moment to bind before the API's lifespan connects to it.
sleep 2

trap 'kill "$MCP_PID" 2>/dev/null' TERM INT

cd /srv/backend
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
