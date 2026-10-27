"""All tools of the app in one registry, and the one way to call them: validate, run, map errors.

The REST API, the MCP server, the CLI and `google_discover_api_mcp.call()` all go through `Runner.run`.
"""

from __future__ import annotations

import asyncio
import importlib
import pkgutil
from typing import Any

import jsonschema

from google_discover_api_mcp import app, settings
from google_discover_api_mcp.core.context import Profile, ToolContext
from google_discover_api_mcp.core.errors import ErrorCode, ToolError
from google_discover_api_mcp.core.tools import ToolSpec
from google_discover_api_mcp.google_discover import tools as tools_package

_TOOLS: dict[str, ToolSpec] | None = None


def all_tools() -> dict[str, ToolSpec]:
    """Every tool in the app's tools/ package, by name, in file order."""
    global _TOOLS
    if _TOOLS is None:
        found: dict[str, ToolSpec] = {}
        for module_info in sorted(pkgutil.iter_modules(tools_package.__path__), key=lambda m: m.name):
            module = importlib.import_module(f"{tools_package.__name__}.{module_info.name}")
            for value in vars(module).values():
                if isinstance(value, ToolSpec) and value.route:
                    found[value.name] = value
        _TOOLS = found
        _local_country(found)
    return _TOOLS


def _local_country(found: dict[str, ToolSpec]) -> None:
    """The hosted tools read from a home IP in any country; here the country follows your IP or proxy."""
    for spec in found.values():
        country = spec.input_schema.get("properties", {}).get("country")
        if country is not None:
            country["description"] = COUNTRY_DESCRIPTION


COUNTRY_DESCRIPTION = (
    "Country of the feed, ISO 3166-1 alpha-2 (US, GB, DE, PL ...). Google picks the region from the IP the "
    "request leaves from: your own connection, so leave it out for your country, or a proxy with {country} in "
    f"{app.ENV}_PROXY for any country. Default: the country setup found for your IP ({app.ENV}_COUNTRY overrides it)."
)


def tools(read_only: bool = False) -> list[ToolSpec]:
    return [spec for spec in all_tools().values() if not read_only or spec.access == "read"]


def description(spec: ToolSpec) -> str:
    """What an agent reads: the one-liner, then the details."""
    return f"{spec.description}\n\n{spec.details}" if spec.details else spec.description


class Runner:
    """Runs tools with the saved settings. Answers are cached per country and language for the whole process."""

    def __init__(self, read_only: bool = False) -> None:
        # Every tool only reads; the flag is kept so --read-only works as in the other Cotlet repos.
        self.read_only = read_only
        self._cache: dict[str, tuple[float, str]] = {}

    def _context(self, args: dict[str, Any]) -> ToolContext:
        current = settings.load()
        if not current.ready:
            raise ToolError(
                f"No Chrome API key yet. Download Chrome for Android as an APK, then run: {app.CLI} setup --apk <file>",
                ErrorCode.AUTH_REQUIRED,
            )
        home = current.home_country
        country = str(args.get("country") or home).upper()
        if country != home and not current.any_country:
            raise ToolError(
                f"Google picks the feed's region from your IP, which is in {home}. Leave country out, or set "
                f"{app.ENV}_PROXY to a proxy URL with {{country}} in it to read other countries.",
                ErrorCode.INVALID_INPUT,
            )
        args["country"] = country
        return ToolContext(settings=current, profile=Profile(country=country), cache=self._cache)

    async def run(self, name: str, args: dict[str, Any] | None = None) -> Any:
        spec = all_tools().get(name)
        if spec is None:
            raise ToolError(f"No tool '{name}'. List them with: {app.CLI} tools", ErrorCode.UNKNOWN_TOOL)
        if self.read_only and spec.access != "read":
            raise ToolError(f"{name} changes {app.NAME} and this server runs read-only.", ErrorCode.SCOPE_DENIED)
        args = {k: v for k, v in (args or {}).items() if v is not None}
        try:
            jsonschema.validate(args, spec.input_schema)
        except jsonschema.ValidationError as exc:
            where = ".".join(str(p) for p in exc.absolute_path)
            raise ToolError(f"{where + ': ' if where else ''}{exc.message}", ErrorCode.INVALID_INPUT) from None
        ctx = self._context(args)
        try:
            return await asyncio.wait_for(spec.handler(ctx, args), timeout=spec.timeout_s or 120)
        except TimeoutError:
            raise ToolError("Google took too long to answer.", ErrorCode.TIMEOUT) from None
        finally:
            await ctx.close()

    async def close(self) -> None:
        self._cache.clear()
