import asyncio
import logging

from agents.mcp import MCPServerStreamableHttp

from ..core.config import settings

logger = logging.getLogger(__name__)

sarjy_mcp_server = MCPServerStreamableHttp(
    name="sarjy-tools",
    params={"url": settings.mcp_server_url},
    # Without this the agent lists the server's tools over the wire before every
    # single turn, which is a full round trip added to time-to-first-token. The
    # tool set only changes when the MCP server is redeployed, and a redeploy
    # drops the session, so the cache cannot outlive what it describes.
    cache_tools_list=True,
    client_session_timeout_seconds=settings.mcp_timeout_seconds,
)

# One connect at a time: several turns can discover a dead session together.
_connect_lock = asyncio.Lock()


async def ensure_connected() -> bool:
    """Connect if not connected. Returns whether the server is usable.

    Never raises. The MCP server is a separate process that can be slow to
    start, can be restarted under the running API, and can simply be down --
    none of which is a reason for the whole assistant to stop answering. A turn
    that finds it unavailable runs without its tools instead.
    """
    if sarjy_mcp_server.session is not None:
        return True
    async with _connect_lock:
        if sarjy_mcp_server.session is not None:
            return True
        try:
            await sarjy_mcp_server.connect()
        except Exception as exc:
            logger.warning("MCP server unavailable at %s: %s", settings.mcp_server_url, exc)
            return False
    logger.info("Connected to MCP server at %s", settings.mcp_server_url)
    return True


async def reset() -> None:
    """Drop the session so the next turn reconnects.

    A restarted MCP server leaves this side holding a session that is dead but
    not None, and every later tool call fails against it until the API itself is
    restarted. Called after a failed turn, which is cheap and self-correcting:
    if the failure had nothing to do with MCP, the next turn pays one handshake.
    """
    async with _connect_lock:
        if sarjy_mcp_server.session is None:
            return
        try:
            await sarjy_mcp_server.cleanup()
        except Exception as exc:
            logger.warning("Could not clean up the MCP session: %s", exc)


async def shutdown() -> None:
    try:
        await sarjy_mcp_server.cleanup()
    except Exception as exc:
        logger.warning("MCP cleanup on shutdown failed: %s", exc)
