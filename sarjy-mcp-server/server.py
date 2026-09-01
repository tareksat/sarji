import logging

from mcp.server.mcpserver import MCPServer

from config import settings
from tools.weather import get_weather

mcp = MCPServer("sarjy-tools")
mcp.tool()(get_weather)

if __name__ == "__main__":
    logging.basicConfig(level="INFO")
    mcp.run(transport="streamable-http", host=settings.host, port=settings.port)
