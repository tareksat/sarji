# The MCP server alone, reachable inside the compose network as
# http://mcp:8100/mcp. It binds 0.0.0.0 here rather than loopback because the
# backend is a different container, and it is never published to the host.
FROM python:3.12-slim
WORKDIR /srv

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY server.py config.py ./
COPY tools/ ./tools/

ENV PYTHONUNBUFFERED=1 \
    MCP_SERVER_HOST=0.0.0.0 \
    MCP_SERVER_PORT=8100

EXPOSE 8100
CMD ["python", "server.py"]
