"""The MCP server: one MCP tool per tool of the app, over stdio or streamable HTTP."""

from __future__ import annotations

import json
from typing import Any

from mcp import types
from mcp.server.lowlevel import Server

from google_discover_api_mcp import __version__, app, mcp_context
from google_discover_api_mcp.core.errors import ToolError
from google_discover_api_mcp.runner import Runner, description, tools

INSTRUCTIONS = (
    f"{app.NAME} tools: the feed Chrome for Android shows on its New Tab page to someone not signed in to Google, "
    f"read from the user's own connection or their proxy. No Google account; every tool only reads. {app.AGENT_START}"
)


def _annotations(spec: Any) -> types.ToolAnnotations:
    method = (spec.route or "GET").split(" ", 1)[0]
    return types.ToolAnnotations(
        title=spec.title,
        readOnlyHint=spec.access == "read",
        destructiveHint=spec.access == "write" and (method == "DELETE" or spec.confirm),
        idempotentHint=method in ("GET", "PUT"),
        openWorldHint=True,
    )


def build(runner: Runner) -> Server:
    server: Server = Server(app.SLUG, version=__version__, instructions=INSTRUCTIONS)

    @server.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name=spec.name,
                title=spec.title,
                description=description(spec),
                inputSchema=spec.input_schema,
                annotations=_annotations(spec),
            )
            for spec in tools(runner.read_only)
        ]

    @server.call_tool(validate_input=False)
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[types.TextContent]:
        try:
            result = await runner.run(name, arguments)
        except ToolError as exc:
            raise RuntimeError(f"{exc.code}: {exc}") from None
        return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]

    mcp_context.register(server, runner)
    return server


async def run_stdio(runner: Runner) -> None:
    from mcp.server.stdio import stdio_server

    server = build(runner)
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())
