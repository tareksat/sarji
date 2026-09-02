import asyncio
import logging
import time
from collections.abc import Awaitable, Callable

import httpx
from fastapi import APIRouter, Response
from sqlalchemy import text
from starlette.concurrency import run_in_threadpool

from ..agent.mcp import sarjy_mcp_server
from ..core.config import settings
from ..core.db import engine
from ..dtos import DependencyHealth, FullHealthResponse

logger = logging.getLogger(__name__)
router = APIRouter(tags=["health"])


@router.get(
    "/api/health",
    summary="Liveness probe",
    response_description="Always `{\"status\": \"ok\"}` when the process is up.",
)
async def health() -> dict[str, str]:
    """Report that the API process is running.

    Deliberately does not touch the database: this is the target of the
    platform's health check, and a slow database should not cycle the service.
    """
    return {"status": "ok"}


def _summarize(name: str, exc: Exception) -> str:
    """Name the failure without quoting it.

    This endpoint is unauthenticated, and psycopg and SQLAlchemy connection
    errors routinely carry the DSN host, port and user in their text, while the
    LiteLLM probe would surface the proxy's internal URL. The exception type is
    enough to tell a wrong password from an unreachable host; the detail goes to
    the log, where it is already scoped to whoever can read the logs.
    """
    logger.warning("Health probe %s failed", name, exc_info=exc)
    return type(exc).__name__


async def _probe(name: str, check: Callable[[], Awaitable[str | None]]) -> DependencyHealth:
    """Time one dependency check and turn any failure into a reportable status."""
    started = time.perf_counter()
    try:
        async with asyncio.timeout(settings.health_check_timeout_seconds):
            detail = await check()
        status = "ok"
    except TimeoutError:
        detail = f"timed out after {settings.health_check_timeout_seconds}s"
        status = "error"
    except Exception as exc:  # noqa: BLE001 - the point is to report, not to raise
        detail = _summarize(name, exc)
        status = "error"
    elapsed_ms = round((time.perf_counter() - started) * 1000, 1)
    return DependencyHealth(status=status, latency_ms=elapsed_ms, detail=detail)


async def _check_database() -> str | None:
    """Round-trip a trivial query. The engine is synchronous, so this runs off
    the event loop; a raw connection is cheaper than a session."""

    def query() -> None:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))

    await run_in_threadpool(query)
    return None


async def _check_litellm() -> str | None:
    """Ask the proxy whether it is alive. Deliberately not a model call: no
    tokens spent, no upstream provider quota touched, no 429 to trip over."""
    base = settings.llm_base_url.rstrip("/").removesuffix("/v1")
    async with httpx.AsyncClient(timeout=settings.health_check_timeout_seconds) as client:
        resp = await client.get(f"{base}/health/liveliness")
    resp.raise_for_status()
    return f"HTTP {resp.status_code}"


async def _check_mcp() -> str | None:
    """List the server's tools over the same session the agent uses, so a
    session that has died since startup shows up here.

    The client caches its tool list, so this can be answered from that cache --
    it proves the session is live, not that the server is still responsive. The
    container's own health check does the deeper probe."""
    tools = await sarjy_mcp_server.list_tools()
    return f"{len(tools)} tools"


@router.get(
    "/api/health/full",
    response_model=FullHealthResponse,
    summary="Dependency health check",
    response_description="Every dependency reachable.",
    responses={
        503: {
            "model": FullHealthResponse,
            "description": "At least one dependency is unreachable.",
        }
    },
)
async def health_full(response: Response) -> FullHealthResponse:
    """Probe Postgres, the LiteLLM proxy and the MCP server, and report each
    one's state and probe latency.

    Returns `503` when any probe fails, with the same body either way, so the
    broken dependency is named rather than guessed at.

    This is a diagnostic endpoint, **not** the platform's health-check target --
    `/api/health` is. Pointing an orchestrator here would restart a perfectly
    healthy API container every time a dependency blinked.
    """
    checks: dict[str, Callable[[], Awaitable[str | None]]] = {
        "database": _check_database,
        "mcp": _check_mcp,
    }
    if settings.llm_base_url:
        checks["litellm"] = _check_litellm

    results = dict(
        zip(checks, await asyncio.gather(*(_probe(n, c) for n, c in checks.items())))
    )

    if not settings.llm_base_url:
        # No proxy in this environment -- the agent talks to OpenAI directly.
        results["litellm"] = DependencyHealth(
            status="skipped", latency_ms=0.0, detail="LLM_BASE_URL is unset"
        )

    if any(dep.status == "error" for dep in results.values()):
        response.status_code = 503
        return FullHealthResponse(status="degraded", dependencies=results)
    return FullHealthResponse(status="ok", dependencies=results)
