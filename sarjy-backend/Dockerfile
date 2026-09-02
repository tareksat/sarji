# The API alone. The MCP server, the LiteLLM proxy and the frontend are their
# own images in docker-compose.yml; the repo-root Dockerfile is the other
# deployment shape, where all of them share one container for Render.
FROM python:3.12-slim
WORKDIR /srv

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY scripts/ ./scripts/

ENV PYTHONUNBUFFERED=1

# Not root. Nothing here needs it, and the process parses untrusted input.
RUN useradd --system --create-home --uid 10001 sarjy && chown -R sarjy /srv
USER sarjy

EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
