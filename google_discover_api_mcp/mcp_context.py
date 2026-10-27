"""Prompts and resources of the MCP server: how to start a task, and the tool catalog as context."""

from __future__ import annotations

import json
from collections.abc import Iterable

from mcp import types
from mcp.server.lowlevel import Server
from mcp.server.lowlevel.helper_types import ReadResourceContents
from pydantic import AnyUrl

from google_discover_api_mcp import app
from google_discover_api_mcp.runner import Runner, description, tools

GUIDE_URI = f"{app.SLUG}://guide"
TOOLS_URI = f"{app.SLUG}://tools"

SAFETY = (
    "Every tool only reads. Google picks the feed's region from the IP the request leaves from, so a country "
    "other than the user's own needs their proxy setting; the error says so."
)


def _guide(runner: Runner) -> str:
    specs = tools(runner.read_only)
    return "\n\n".join(
        [
            f"# {app.NAME} tools",
            (
                f"These tools read the {app.NAME} feed Chrome for Android shows signed out, from the user's own "
                f"connection, with no Google account. {len(specs)} tools."
            ),
            f"Where to start: {app.AGENT_START}",
            SAFETY,
            "A read of one country and language is reused for 15 minutes; collect_discover_cards merges many reads.",
            f"The full catalog with each tool's access is in {TOOLS_URI}.",
        ]
    )


def _catalog(runner: Runner) -> str:
    return json.dumps(
        [
            {"name": spec.name, "title": spec.title, "access": spec.access, "description": description(spec)}
            for spec in tools(runner.read_only)
        ],
        ensure_ascii=False,
        indent=2,
    )


def _prompts() -> list[types.Prompt]:
    return [
        types.Prompt(
            name="getting_started",
            title=f"Get started with {app.NAME}",
            description=f"Read the {app.NAME} feed once and show what the tools can do.",
        ),
        types.Prompt(
            name="plan_task",
            title=f"Plan a {app.NAME} task",
            description=f"Turn a goal into {app.NAME} tool calls.",
            arguments=[
                types.PromptArgument(name="task", description=f"What you want done in {app.NAME}", required=True)
            ],
        ),
    ]


def _prompt_text(name: str, arguments: dict[str, str] | None) -> str:
    if name == "getting_started":
        return (
            f"Use the {app.NAME} tools. {app.AGENT_START} Tell me which country the feed is from and its top "
            f"five cards, then list five things I can do with these tools."
        )
    if name == "plan_task":
        task = (arguments or {}).get("task", "").strip()
        if not task:
            raise ValueError("plan_task needs a task")
        return (
            f"I want to do this in {app.NAME}: {task}\n\n"
            f"Read {TOOLS_URI}, pick the tools, and run the read tools you need first. {SAFETY}"
        )
    raise ValueError(f"unknown prompt: {name}")


def register(server: Server, runner: Runner) -> None:
    @server.list_prompts()
    async def list_prompts() -> list[types.Prompt]:
        return _prompts()

    @server.get_prompt()
    async def get_prompt(name: str, arguments: dict[str, str] | None) -> types.GetPromptResult:
        text = _prompt_text(name, arguments)
        return types.GetPromptResult(
            description=next(prompt.description for prompt in _prompts() if prompt.name == name),
            messages=[types.PromptMessage(role="user", content=types.TextContent(type="text", text=text))],
        )

    @server.list_resources()
    async def list_resources() -> list[types.Resource]:
        return [
            types.Resource(
                uri=AnyUrl(GUIDE_URI),
                name="guide",
                title=f"How to use the {app.NAME} tools",
                description="Where to start, countries, caching.",
                mimeType="text/markdown",
            ),
            types.Resource(
                uri=AnyUrl(TOOLS_URI),
                name="tools",
                title=f"{app.NAME} tool catalog",
                description="Every tool with its access and full description.",
                mimeType="application/json",
            ),
        ]

    @server.read_resource()
    async def read_resource(uri: AnyUrl) -> Iterable[ReadResourceContents]:
        if str(uri) == GUIDE_URI:
            return [ReadResourceContents(content=_guide(runner), mime_type="text/markdown")]
        if str(uri) == TOOLS_URI:
            return [ReadResourceContents(content=_catalog(runner), mime_type="application/json")]
        raise ValueError(f"unknown resource: {uri}")
