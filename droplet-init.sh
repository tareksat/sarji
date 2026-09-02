#!/usr/bin/env bash
#
# One-shot provisioning for a fresh DigitalOcean droplet running the production
# stack (docker-compose.prod.yml). See docs/DEPLOY.md for the manual runbook this
# automates and for the reasoning behind the shape of the deployment.
#
# Usage, as root on a fresh Ubuntu 22.04 droplet:
#
#   curl -fsSL https://raw.githubusercontent.com/tareksat/sarji/main/droplet-init.sh -o droplet-init.sh
#   bash droplet-init.sh --domain yourname.duckdns.org --groq-key gsk_...
#
# Or, if the repo is already cloned, from inside it:
#
#   sudo ./droplet-init.sh --domain yourname.duckdns.org
#
# Every step is idempotent: rerunning it after a partial failure is safe and
# never regenerates secrets that are already in .env.
#
# What it does NOT do: open the firewall. Use a DigitalOcean Cloud Firewall
# (inbound 22, 80, 443 only). ufw is not enough — Docker writes its own iptables
# chains, so a published port is world-reachable whatever ufw says.

set -euo pipefail

REPO_SSH="git@github.com:tareksat/sarji.git"
CLONE_DIR="${CLONE_DIR:-/opt/sarjy}"
COMPOSE_FILE="docker-compose.prod.yml"

SITE_DOMAIN="${SITE_DOMAIN:-}"
GROQ_API_KEY="${GROQ_API_KEY:-}"
LLM_MODEL="${LLM_MODEL:-groq-oss}"
LAUNCH=0
SKIP_DNS_CHECK=0

log()  { printf '\n\033[1;36m==>\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33mwarning:\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[1;31merror:\033[0m %s\n' "$*" >&2; exit 1; }

usage() {
    cat <<'EOF'
Usage: droplet-init.sh [options]

  --domain <fqdn>     Domain Caddy requests a certificate for (SITE_DOMAIN).
  --groq-key <key>    Provider key written to .env as GROQ_API_KEY.
  --model <name>      LiteLLM model_name (default: groq-oss).
  --dir <path>        Where to clone the repo (default: /opt/sarjy).
  --launch            Build and start the stack when provisioning finishes.
  --skip-dns-check    Do not verify that the domain resolves to this host.
  -h, --help          Show this help.

Options may also be given as environment variables: SITE_DOMAIN, GROQ_API_KEY,
LLM_MODEL, CLONE_DIR.
EOF
}

while [ $# -gt 0 ]; do
    case "$1" in
        --domain)         SITE_DOMAIN="${2:?--domain needs a value}"; shift 2 ;;
        --groq-key)       GROQ_API_KEY="${2:?--groq-key needs a value}"; shift 2 ;;
        --model)          LLM_MODEL="${2:?--model needs a value}"; shift 2 ;;
        --dir)            CLONE_DIR="${2:?--dir needs a value}"; shift 2 ;;
        --launch)         LAUNCH=1; shift ;;
        --skip-dns-check) SKIP_DNS_CHECK=1; shift ;;
        -h|--help)        usage; exit 0 ;;
        *)                usage; die "unknown option: $1" ;;
    esac
done

[ "$(id -u)" -eq 0 ] || die "run as root (sudo ./droplet-init.sh ...)"

export DEBIAN_FRONTEND=noninteractive

# --- 1. Base packages -------------------------------------------------------
# dnsutils for dig, netcat for the port checks in the DEPLOY.md verification.

log "Installing base packages"
apt-get update -qq
apt-get install -y -qq \
    ca-certificates curl git gnupg dnsutils netcat-openbsd \
    unattended-upgrades openssl

# Security updates only; the stack itself is pinned by image tag, not by apt.
dpkg-reconfigure -f noninteractive unattended-upgrades >/dev/null 2>&1 || true

# --- 2. Swap ----------------------------------------------------------------
# 1 GB droplets cannot hold LiteLLM plus Postgres plus the frontend build.
# 2 GB is the supported size; below that, swap is what keeps the build alive.

TOTAL_MB=$(awk '/MemTotal/ {print int($2 / 1024)}' /proc/meminfo)
if [ "$TOTAL_MB" -lt 1900 ] && [ ! -f /swapfile ]; then
    log "Only ${TOTAL_MB} MB RAM — adding a 2 GB swapfile"
    fallocate -l 2G /swapfile || dd if=/dev/zero of=/swapfile bs=1M count=2048
    chmod 600 /swapfile
    mkswap /swapfile >/dev/null
    swapon /swapfile
    grep -q '^/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi

# --- 3. Docker --------------------------------------------------------------
# The Marketplace "Docker on Ubuntu" image already has both; this branch is for
# a plain Ubuntu droplet.

if ! command -v docker >/dev/null 2>&1; then
    log "Installing Docker Engine"
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
        | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
        > /etc/apt/sources.list.d/docker.list
    apt-get update -qq
    apt-get install -y -qq docker-ce docker-ce-cli containerd.io \
        docker-buildx-plugin docker-compose-plugin
else
    log "Docker already present: $(docker --version)"
fi

docker compose version >/dev/null 2>&1 \
    || die "docker compose v2 plugin missing — install docker-compose-plugin"

systemctl enable --now docker >/dev/null 2>&1 || true

# Container logs are unbounded by default; a long-lived chat backend fills a
# 50 GB disk with them eventually.
if [ ! -f /etc/docker/daemon.json ]; then
    log "Capping container log size"
    mkdir -p /etc/docker
    cat > /etc/docker/daemon.json <<'EOF'
{
  "log-driver": "json-file",
  "log-opts": { "max-size": "10m", "max-file": "3" }
}
EOF
    systemctl restart docker
fi

# --- 4. Deploy key ----------------------------------------------------------
# The repo is private, so the clone is over SSH with a read-only deploy key.

KEY=/root/.ssh/id_ed25519
if [ ! -f "$KEY" ]; then
    log "Generating a deploy key"
    mkdir -p /root/.ssh && chmod 700 /root/.ssh
    ssh-keygen -t ed25519 -N '' -C sarjy-droplet -f "$KEY" >/dev/null
fi
ssh-keyscan -t ed25519 github.com 2>/dev/null >> /root/.ssh/known_hosts
sort -u -o /root/.ssh/known_hosts /root/.ssh/known_hosts

# --- 5. Clone ---------------------------------------------------------------

if [ -f "$COMPOSE_FILE" ]; then
    CLONE_DIR="$(pwd)"
    log "Running from inside the repo at $CLONE_DIR"
elif [ -d "$CLONE_DIR/.git" ]; then
    log "Repo already at $CLONE_DIR — pulling"
    git -C "$CLONE_DIR" pull --ff-only
else
    if ! ssh -o BatchMode=yes -o StrictHostKeyChecking=accept-new \
         -T git@github.com 2>&1 | grep -q 'successfully authenticated'; then
        cat <<EOF

Add this public key to the GitHub repo as a read-only deploy key
(Settings -> Deploy keys -> Add deploy key), then rerun this script:

$(cat "$KEY.pub")

EOF
        exit 1
    fi
    log "Cloning into $CLONE_DIR"
    git clone "$REPO_SSH" "$CLONE_DIR"
fi

cd "$CLONE_DIR"

# --- 6. Secrets -------------------------------------------------------------
# Existing values are never overwritten: rerunning must not rotate the Postgres
# password out from under the volume that was initialised with it.

if [ ! -f .env ]; then
    log "Writing .env"
    cp .env.example .env
    chmod 600 .env
fi

# set_env KEY VALUE [force]
#
# `force` means the value came from an explicit command-line flag, which beats
# whatever is already in .env. Without it, `.env.example` shipping a real-looking
# default (LLM_MODEL=groq-oss) made `--model gemini-flash` a silent no-op: the
# existing value was not a recognised placeholder, so it was kept and nothing
# said so.
set_env() {
    local key="$1" value="$2" force="${3:-0}"
    [ -n "$value" ] || return 0
    if grep -q "^${key}=" .env; then
        local current
        current="$(grep "^${key}=" .env | head -n1 | cut -d= -f2-)"
        if [ "$force" -ne 1 ]; then
            # Placeholders from .env.example count as unset.
            case "$current" in
                ''|sk-local|yourname.duckdns.org) ;;
                *) return 0 ;;
            esac
        elif [ "$current" = "$value" ]; then
            return 0
        else
            log "Overriding ${key} in .env (was '${current}')"
        fi
        # awk, not sed: the replacement is arbitrary user input, and every sed
        # delimiter -- | included, reachable via --groq-key or --domain -- is a
        # character some value can legitimately contain. awk takes the value as
        # data rather than as part of the expression.
        awk -v key="$key" -v value="$value" 'index($0, key "=") == 1 { print key "=" value; next } { print }' .env > .env.tmp && mv .env.tmp .env
        chmod 600 .env
    else
        echo "${key}=${value}" >> .env
    fi
}

if [ -z "$SITE_DOMAIN" ]; then
    current_domain="$(grep '^SITE_DOMAIN=' .env | cut -d= -f2-)"
    case "$current_domain" in
        ''|yourname.duckdns.org)
            read -rp "Domain for the certificate (e.g. yourname.duckdns.org): " SITE_DOMAIN
            ;;
        *) SITE_DOMAIN="$current_domain" ;;
    esac
fi
[ -n "$SITE_DOMAIN" ] || die "SITE_DOMAIN is required — Caddy needs a real name to get a certificate"

# Explicit flags win over whatever .env already holds; the generated secrets
# below must never overwrite an existing one, or the database becomes
# unreachable and the proxy key stops matching.
set_env SITE_DOMAIN      "$SITE_DOMAIN"  1
set_env LLM_MODEL        "$LLM_MODEL"    1
set_env GROQ_API_KEY     "$GROQ_API_KEY" 1
set_env POSTGRES_PASSWORD "$(openssl rand -hex 16)"
set_env LITELLM_MASTER_KEY "$(openssl rand -hex 32)"

if ! grep -qE '^(OPENAI|GROQ|GEMINI)_API_KEY=.+' .env; then
    warn "no provider key in .env — set GROQ_API_KEY (or the one your LLM_MODEL uses) before launching"
fi

# --- 7. DNS -----------------------------------------------------------------
# Caddy's HTTP-01 challenge fails if the name does not already point here, and a
# handful of failures burns through the Let's Encrypt rate limit for the domain.

if [ "$SKIP_DNS_CHECK" -eq 0 ]; then
    log "Checking that $SITE_DOMAIN resolves to this host"
    PUBLIC_IP="$(curl -fsS --max-time 10 https://api.ipify.org || true)"
    RESOLVED="$(dig +short "$SITE_DOMAIN" A | tail -n1)"
    if [ -z "$RESOLVED" ]; then
        warn "$SITE_DOMAIN does not resolve yet — point it at ${PUBLIC_IP:-this droplet} before starting the stack"
    elif [ -n "$PUBLIC_IP" ] && [ "$RESOLVED" != "$PUBLIC_IP" ]; then
        warn "$SITE_DOMAIN resolves to $RESOLVED but this host is $PUBLIC_IP — certificate issuance will fail"
    else
        log "DNS OK: $SITE_DOMAIN -> $RESOLVED"
    fi
fi

# --- 8. Launch --------------------------------------------------------------

if [ "$LAUNCH" -eq 1 ]; then
    log "Building and starting the stack (several minutes on 1 vCPU)"
    docker compose -f "$COMPOSE_FILE" up -d --build
    docker compose -f "$COMPOSE_FILE" ps
    cat <<EOF

Watch the certificate being issued:

  cd $CLONE_DIR && docker compose -f $COMPOSE_FILE logs -f caddy

Then verify from your own machine, not the droplet:

  curl -I https://$SITE_DOMAIN
  curl https://$SITE_DOMAIN/api/health/full
  nc -vz $SITE_DOMAIN 5432   # must fail to connect
EOF
else
    cat <<EOF

Provisioning done. Review $CLONE_DIR/.env, then:

  cd $CLONE_DIR && docker compose -f $COMPOSE_FILE up -d --build

Reachable inbound ports must be 22, 80 and 443 only, set as a DigitalOcean
Cloud Firewall — ufw does not cover Docker's published ports.
EOF
fi
