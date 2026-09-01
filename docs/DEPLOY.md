# Deploying Sarjy

The public deployment is a single DigitalOcean droplet running
`docker-compose.prod.yml`, reached over HTTPS at a free DuckDNS subdomain.

## Why this shape

- **HTTPS is required, not cosmetic.** The voice input uses the browser's
  `SpeechRecognition` API, and Chrome only grants microphone access on a secure
  origin. Over plain HTTP the voice half of the product silently does nothing.
- **`docker-compose.prod.yml` is standalone, not an override.** Compose *appends*
  to `ports:` when merging files, so an override could not remove the 5432, 4000
  and 8080 publishes in `docker-compose.yml`. Those must not exist on a public
  IP, and firewalling them is not enough: Docker writes its own iptables chains,
  so a published port is world-reachable regardless of `ufw`.
- **Caddy is the only service with published ports.** It terminates TLS, obtains
  and renews the Let's Encrypt certificate on its own, and proxies to the `ui`
  nginx container, which in turn proxies `/api/` to the backend. One origin, so
  no CORS anywhere in the chain.

## Cost

The domain and the certificate are free; the host is not. DigitalOcean has no
free tier for services — a 2 GB droplet is ~$12/mo, covered by the $200 /
60-day new-account credit (or $200 / 1 year via the GitHub Student Pack).

## Scripted setup

`droplet-init.sh` at the repo root does steps 4-7 of the runbook below —
packages, Docker, swap on an undersized droplet, the deploy key, the clone,
generated secrets, and a DNS pre-check — and is safe to rerun. Steps 1-3
(droplet, cloud firewall, DuckDNS record) stay manual: they happen in
DigitalOcean's and DuckDNS's consoles, not on the host.

```
curl -fsSL https://raw.githubusercontent.com/tareksat/sarji/main/droplet-init.sh -o droplet-init.sh
sudo bash droplet-init.sh --domain yourname.duckdns.org --groq-key gsk_... --launch
```

Without `--launch` it stops after writing `.env` so you can review it first. The
first run prints the deploy key and exits if the key is not yet on the GitHub
repo. The manual runbook below is what it automates, and remains the reference
when something fails.

## Runbook

### 1. Droplet

Create Droplet → Marketplace image **Docker on Ubuntu 22.04** → region nearest
you → **2 GB / 1 vCPU**. Add your SSH key at creation.

1 GB is too tight: LiteLLM alone is around 400 MB, with Postgres, the backend,
nginx and Caddy on top. If you use 1 GB anyway, add 2 GB of swap first.

### 2. Firewall

Use a **DigitalOcean Cloud Firewall**, not `ufw` — Docker's published ports
bypass `ufw`. Allow inbound 22, 80 and 443 only.

### 3. DuckDNS

Sign in at [duckdns.org](https://www.duckdns.org), claim a subdomain, and set its
IP to the droplet's public IPv4. A droplet IP is static, so no updater cron is
needed. Confirm before going further:

```
dig +short yourname.duckdns.org
```

### 4. Clone

The repo is private and cloned over SSH. On the droplet:

```
ssh-keygen -t ed25519 -C sarjy-droplet
cat ~/.ssh/id_ed25519.pub
```

Add that key to the GitHub repo as a **read-only deploy key**, then:

```
git clone git@github.com:tareksat/sarji.git && cd sarji
```

### 5. Secrets

```
cp .env.example .env
```

Fill in:

| Variable | Value |
| --- | --- |
| `GROQ_API_KEY` | provider key for whichever `LLM_MODEL` you use |
| `LITELLM_MASTER_KEY` | `openssl rand -hex 32` — must not stay `sk-local` |
| `POSTGRES_PASSWORD` | `openssl rand -hex 16` |
| `SITE_DOMAIN` | `yourname.duckdns.org` |

`.env` is gitignored.

### 6. Launch

```
docker compose -f docker-compose.prod.yml up -d --build
```

The first build compiles the frontend; expect several minutes on 1 vCPU.

### 7. Certificate

```
docker compose -f docker-compose.prod.yml logs -f caddy
```

Wait for the certificate-obtained line. HTTP-01 needs port 80 reachable from the
internet — this is the step that fails when DNS or the firewall is wrong.

## Verification

Run these from your own machine, not the droplet:

```
curl -I https://yourname.duckdns.org           # 200, valid Let's Encrypt chain
curl -I http://yourname.duckdns.org            # 308 redirect to HTTPS
curl https://yourname.duckdns.org/api/health   # {"status":"ok"}
curl https://yourname.duckdns.org/api/health/full
```

`/api/health/full` should return 200 with `database`, `mcp` and `litellm` all
`ok`. A 503 names the failing dependency — read it first on any problem.

Confirm nothing internal is exposed. Both of these must fail to connect:

```
nc -vz yourname.duckdns.org 5432
nc -vz yourname.duckdns.org 4000
```

Then open the site in Chrome: send a typed message and confirm a reply, then
click the mic, confirm Chrome prompts for microphone permission, speak, and
confirm the transcript is sent and the reply is spoken back.

Finally, on the droplet, after a few chat turns:

```
docker stats
```

Total memory should sit comfortably under the droplet's RAM. LiteLLM is the
component most likely to push it over.

## Operations

```
docker compose -f docker-compose.prod.yml logs -f backend    # follow API logs
docker compose -f docker-compose.prod.yml ps                 # service health
git pull && docker compose -f docker-compose.prod.yml up -d --build   # deploy
```

The database lives in the `sarjy_pgdata` volume and the certificate in
`caddy_data`; neither is touched by a rebuild.

## If $0 becomes a hard requirement

When the credit runs out, the free fallback is a Render free Docker web service
plus a Neon free Postgres. It sleeps after 15 minutes idle (~50 s cold start),
and its 512 MB does not fit LiteLLM — the backend would point `LLM_BASE_URL`
straight at Groq's OpenAI-compatible endpoint, which `app/main.py` already
supports, and `_check_litellm` in `app/routers/health.py` would need to become
skippable. `render.yaml` at the repo root is the existing blueprint for the
single-container variant.
