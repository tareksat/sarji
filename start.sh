#!/bin/bash
# Bash rather than /bin/sh: `wait -n` and /dev/tcp are what make the supervision
# below possible, and neither exists in dash.
set -uo pipefail

# Three processes, one container. Both helpers bind loopback: nothing but the
# API is reachable from outside, and neither costs a second cold start.

pids=()
shutting_down=0

terminate() {
    shutting_down=1
    [ ${#pids[@]} -gt 0 ] && kill "${pids[@]}" 2>/dev/null
    return 0
}

# Installed before anything is started, and this shell stays PID 1 rather than
# being replaced by `exec`, so it can both forward the signal and reap children.
trap terminate TERM INT

# Waits for something to accept on the port, using bash's own /dev/tcp so no
# extra tool has to be installed.
wait_for_port() {
    local host=$1 port=$2 deadline=$(( SECONDS + $3 ))
    while (( SECONDS < deadline )); do
        if (exec 3<>"/dev/tcp/${host}/${port}") 2>/dev/null; then
            exec 3<&- 3>&- 2>/dev/null
            return 0
        fi
        sleep 0.5
    done
    return 1
}

# DATABASE_URL is unset for LiteLLM only: it belongs to the API, and LiteLLM
# reads it as a request to run in Prisma-backed mode, which this image has no
# client for.
env -u DATABASE_URL /opt/litellm/bin/litellm \
    --config /srv/litellm/config.yaml --host 127.0.0.1 --port 4000 &
pids+=($!)

cd /srv/mcp
python server.py &
pids+=($!)

# Waiting on the port, not sleeping a fixed five seconds: on a cold shared-vCPU
# instance the MCP server's imports alone can take longer than that, and the API
# would start into a race it loses. Not fatal if it times out -- the API
# connects to MCP lazily and retries -- but starting in order avoids the retry.
if ! wait_for_port 127.0.0.1 "${MCP_SERVER_PORT:-8100}" 60; then
    echo "start.sh: MCP server has not bound its port; starting the API anyway" >&2
fi

cd /srv/backend
uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}" &
pids+=($!)

# `wait -n` returns as soon as ANY of them exits. Without it, a LiteLLM or MCP
# server killed for memory goes unnoticed: uvicorn keeps serving and
# `/api/health` -- deliberately dependency-free -- keeps returning 200, so the
# platform never restarts the container while every chat turn fails.
status=0
wait -n || status=$?

if (( shutting_down == 0 )); then
    echo "start.sh: a supervised process exited (status ${status}); stopping" >&2
    terminate
    exit 1
fi

wait
exit 0
