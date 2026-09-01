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
RUN pip install --no-cache-dir -r backend-requirements.txt -r mcp-requirements.txt

COPY sarjy-backend/ /srv/backend/
COPY sarjy-mcp-server/ /srv/mcp/
COPY --from=ui /ui/dist /srv/backend/app/static
COPY start.sh /srv/start.sh
RUN chmod +x /srv/start.sh

ENV PYTHONUNBUFFERED=1 \
    MCP_SERVER_HOST=127.0.0.1 \
    MCP_SERVER_PORT=8100 \
    MCP_SERVER_URL=http://127.0.0.1:8100/mcp

EXPOSE 8000
CMD ["/srv/start.sh"]
