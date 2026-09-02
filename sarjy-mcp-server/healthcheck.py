"""Container health check: complete an MCP handshake and list the tools.

A bare TCP connect only proves the socket is bound, which a hung server also
manages -- and that is exactly the failure the backend cannot see from its own
side, since its MCP session goes on looking alive.

Exits 0 when the server answers, 1 otherwise.
"""

import asyncio
import sys

from mcp import Client

from config import settings

TIMEOUT_SECONDS = 5.0


async def main() -> int:
    host = "127.0.0.1" if settings.host in {"0.0.0.0", "::"} else settings.host
    url = f"http://{host}:{settings.port}/mcp"
    try:
        async with asyncio.timeout(TIMEOUT_SECONDS):
            async with Client(url, raise_exceptions=True) as client:
                await client.list_tools()
    except Exception as exc:  # noqa: BLE001 - a health check reports, it does not raise
        print(f"MCP health check failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
