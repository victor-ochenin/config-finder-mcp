"""Entry point for running the MCP server."""

import asyncio
from mcp.server.stdio import stdio_server
from config_finder_mcp.server import app


async def main():
    """Запуск MCP сервера через STDIO."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
