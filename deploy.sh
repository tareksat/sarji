#!/usr/bin/env bash
#
# Redeploy the production stack (docker-compose.prod.yml) from a branch.
#
# droplet-init.sh provisions a host once; this is the repeat case — take the
# named branch, land the host exactly on its remote state, stop the running
# stack, and bring it back up with a rebuild.
#
# Usage, on the droplet:
#
#   ./deploy.sh              # deploy main
#   ./deploy.sh deep-dive    # deploy a named branch
#
# Safe to rerun: on the same branch it just rebuilds and restarts. Named volumes
# (the database and the Let's Encrypt certificate) are never removed.
#
# The branch sync is destructive to the host's working tree — local edits and
# untracked files under version control's reach are discarded, so that what runs
# is exactly what is on origin. It stops for confirmation before doing that on a
# dirty tree; --yes skips the prompt.

set -euo pipefail

CLONE_DIR="${CLONE_DIR:-/opt/sarjy}"
COMPOSE_FILE="docker-compose.prod.yml"

BRANCH="${DEPLOY_BRANCH:-}"
BUILD=1
ASSUME_YES=0
HEALTH_TIMEOUT="${HEALTH_TIMEOUT:-90}"

log()  { printf '\n\033[1;36m==>\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33mwarning:\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[1;31merror:\033[0m %s\n' "$*" >&2; exit 1; }

usage() {
    cat <<'EOF'
Usage: deploy.sh [branch] [options]

  branch              Branch to deploy (default: main).

  --dir <path>        Repo location (default: /opt/sarjy). Ignored when the
                      script is run from inside the repo.
  --no-build          Restart without rebuilding images.
  --yes               Do not prompt before discarding host-local changes.
  -h, --help          Show this help.

Options may also be given as environment variables: DEPLOY_BRANCH, CLONE_DIR,
HEALTH_TIMEOUT.
EOF
}

while [ $# -gt 0 ]; do
    case "$1" in
        --dir)      CLONE_DIR="${2:?--dir needs a value}"; shift 2 ;;
        --no-build) BUILD=0; shift ;;
        --yes|-y)   ASSUME_YES=1; shift ;;
        -h|--help)  usage; exit 0 ;;
        -*)         usage; die "unknown option: $1" ;;
        *)
            [ -z "$BRANCH" ] || die "only one branch may be given (got '$BRANCH' and '$1')"
            BRANCH="$1"; shift
            ;;
    esac
done

BRANCH="${BRANCH:-main}"

# --- 1. Preflight -----------------------------------------------------------
# Running from inside the repo wins over --dir, the same way droplet-init.sh
# prefers the checkout it was launched from.

if [ -f "$COMPOSE_FILE" ]; then
    CLONE_DIR="$(pwd)"
else
    [ -d "$CLONE_DIR" ] || die "no repo at $CLONE_DIR — pass --dir, or run droplet-init.sh first"
    cd "$CLONE_DIR"
    [ -f "$COMPOSE_FILE" ] || die "$CLONE_DIR has no $COMPOSE_FILE"
fi

git rev-parse --is-inside-work-tree >/dev/null 2>&1 \
    || die "$CLONE_DIR is not a git repository"

# The compose file uses ${POSTGRES_PASSWORD:?} and friends; without .env the
# deploy fails after the stack is already down, with a bare compose error.
[ -f .env ] || die "no .env in $CLONE_DIR — copy .env.example and fill it in (see docs/DEPLOY.md)"

command -v docker >/dev/null 2>&1 || die "docker not installed"
docker compose version >/dev/null 2>&1 \
    || die "docker compose v2 plugin missing — install docker-compose-plugin"

log "Deploying branch '$BRANCH' from $CLONE_DIR"
printf '    currently at: %s\n' "$(git log --oneline -1 2>/dev/null || echo 'no commits')"

# --- 2. Sync the branch -----------------------------------------------------

log "Fetching origin"
git fetch --prune origin

git rev-parse --verify --quiet "refs/remotes/origin/$BRANCH" >/dev/null \
    || die "no origin/$BRANCH — check the branch name, or push it first"

DIRTY="$(git status --porcelain)"
if [ -n "$DIRTY" ]; then
    warn "the working tree at $CLONE_DIR has local changes; they will be discarded:"
    printf '%s\n' "$DIRTY" >&2
    if [ "$ASSUME_YES" -eq 0 ]; then
        [ -t 0 ] || die "refusing to discard local changes without a TTY — rerun with --yes"
        read -rp "Discard them and deploy origin/$BRANCH? [y/N] " reply
        case "$reply" in
            [yY]|[yY][eE][sS]) ;;
            *) die "aborted" ;;
        esac
    fi
fi

log "Resetting to origin/$BRANCH"
git checkout -B "$BRANCH" "origin/$BRANCH"
git reset --hard "origin/$BRANCH"
# No -x: that would delete .env and take the Postgres password with it.
git clean -fd

DEPLOYED="$(git log --oneline -1)"
printf '    now at: %s\n' "$DEPLOYED"

# --- 3. Stop ----------------------------------------------------------------
# Never `down -v`: sarjy_pgdata holds the database and caddy_data the issued
# certificate, and Let's Encrypt rate-limits reissues.

log "Stopping the running stack"
docker compose -f "$COMPOSE_FILE" down --remove-orphans

# --- 4. Start ---------------------------------------------------------------

if [ "$BUILD" -eq 1 ]; then
    log "Building and starting (several minutes on 1 vCPU)"
    docker compose -f "$COMPOSE_FILE" up -d --build
else
    log "Starting without a rebuild"
    docker compose -f "$COMPOSE_FILE" up -d
fi

docker compose -f "$COMPOSE_FILE" ps

# --- 5. Health --------------------------------------------------------------
# Checked from inside the backend container, which is where the compose
# healthcheck runs it too — no host-side curl or published port needed.

log "Waiting for the backend to report healthy (up to ${HEALTH_TIMEOUT}s)"
healthy=0
elapsed=0
while [ "$elapsed" -lt "$HEALTH_TIMEOUT" ]; do
    if docker compose -f "$COMPOSE_FILE" exec -T backend python -c \
        "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health/full', timeout=3)" \
        >/dev/null 2>&1; then
        healthy=1
        break
    fi
    sleep 5
    elapsed=$((elapsed + 5))
done

if [ "$healthy" -eq 1 ]; then
    log "Healthy after ${elapsed}s — deployed $BRANCH @ $DEPLOYED"
    SITE_DOMAIN="$(grep '^SITE_DOMAIN=' .env | head -n1 | cut -d= -f2- || true)"
    cat <<EOF

Verify from your own machine, not the host:

  curl -I https://${SITE_DOMAIN:-<domain>}
  curl https://${SITE_DOMAIN:-<domain>}/api/health/full

Certificate and API logs:

  docker compose -f $COMPOSE_FILE logs -f caddy
  docker compose -f $COMPOSE_FILE logs -f backend
EOF
else
    warn "backend not healthy after ${HEALTH_TIMEOUT}s — last 50 lines:"
    docker compose -f "$COMPOSE_FILE" logs --tail 50 backend || true
    die "deploy of $BRANCH finished but the stack is unhealthy"
fi
