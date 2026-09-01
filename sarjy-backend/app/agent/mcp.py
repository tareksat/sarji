from agents.mcp import MCPServerStreamableHttp

from ..core.config import settings

sarjy_mcp_server = MCPServerStreamableHttp(
    name="sarjy-tools",
    params={"url": settings.mcp_server_url},
)
