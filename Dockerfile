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
