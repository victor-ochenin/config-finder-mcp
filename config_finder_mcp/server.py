"""MCP Server for Config Finder."""

import json
import asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from config_finder_mcp import finder

app = Server("config-finder-mcp")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """Вернуть список доступных инструментов."""
    return [
        Tool(
            name="find_configs",
            description="Найти все конфигурационные файлы в указанной директории. "
                        "Быстрее чем ручной поиск через list_directory, так как один вызов "
                        "сканирует всю директорию рекурсивно и фильтрует только конфиги.",
            inputSchema={
                "type": "object",
                "properties": {
                    "root_path": {
                        "type": "string",
                        "description": "Корневая директория для поиска (абсолютный путь).",
                    },
                    "max_depth": {
                        "type": "integer",
                        "description": "Максимальная глубина поиска (по умолчанию 5).",
                        "default": 5,
                    },
                    "file_name_filter": {
                        "type": "string",
                        "description": "Фильтр по части имени файла (например, 'docker' найдёт Dockerfile, docker-compose).",
                    },
                },
                "required": ["root_path"],
            },
        ),
        Tool(
            name="read_config",
            description="Прочитать содержимое конфигурационного файла с ограничением по количеству строк.",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Абсолютный путь к конфигурационному файлу.",
                    },
                    "max_lines": {
                        "type": "integer",
                        "description": "Максимальное количество строк для чтения (по умолчанию 200).",
                        "default": 200,
                    },
                },
                "required": ["file_path"],
            },
        ),
        Tool(
            name="find_config_by_name",
            description="Найти конфигурационные файлы по имени приложения в стандартных директориях.",
            inputSchema={
                "type": "object",
                "properties": {
                    "app_name": {
                        "type": "string",
                        "description": "Имя приложения или часть имени для поиска.",
                    },
                    "search_roots": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Список корневых директорий для поиска. По умолчанию Desktop и текущая директория.",
                    },
                },
                "required": ["app_name"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Вызвать инструмент по имени."""
    if name == "find_configs":
        result = finder.find_configs(
            root_path=arguments["root_path"],
            max_depth=arguments.get("max_depth", 5),
            file_name_filter=arguments.get("file_name_filter"),
        )
    elif name == "read_config":
        result = finder.read_config(
            file_path=arguments["file_path"],
            max_lines=arguments.get("max_lines", 200),
        )
    elif name == "find_config_by_name":
        result = finder.find_config_by_name(
            app_name=arguments["app_name"],
            search_roots=arguments.get("search_roots"),
        )
    else:
        result = {"error": f"Unknown tool: {name}"}

    return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]


async def main():
    """Запуск MCP сервера через STDIO."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
