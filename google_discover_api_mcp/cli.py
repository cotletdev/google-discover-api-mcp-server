"""<cli>: set up Chrome's API key, then run the REST API and MCP server, or call one tool.

<cli> setup --apk <file>  # read Chrome's API key from a Chrome for Android APK, test it, save it
<cli> status           # key, Chrome version, country and proxy, and one test read of the feed
<cli> tools            # every tool with its REST route
<cli> call <tool> k=v  # one tool, arguments as JSON or key=value
<cli> mcp              # MCP server over stdio, for Claude Code, Claude Desktop, Cursor
<cli> serve            # REST API + MCP over HTTP on http://127.0.0.1:8787
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import getpass
import ipaddress
import json
import os
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from google_discover_api_mcp import __version__, app
from google_discover_api_mcp import settings as config
from google_discover_api_mcp.core.errors import ToolError
from google_discover_api_mcp.runner import Runner, all_tools, tools


def _test(keys: list[str], version: str, current: config.Settings) -> list[str]:
    """The keys the feed takes, each tried with one read from this computer (or the proxy)."""
    from google_discover_api_mcp.core.context import HttpClient, Log
    from google_discover_api_mcp.google_discover import client

    proxy = current.proxy_for(current.home_country)
    working: list[str] = []

    async def go() -> None:
        http = HttpClient(proxy)
        try:
            for key in keys:
                with _only(client, key, version):
                    try:
                        await client.ask(http, Log(), client.language_of(current.home_country, None))
                    except ToolError:
                        continue
                working.append(key)
        finally:
            await http.close()

    asyncio.run(go())
    return working


@contextlib.contextmanager
def _only(client: Any, key: str, version: str) -> Iterator[None]:
    """client.ask with one key and version, before anything is saved."""
    keys, chrome = client.KEYS, client.CHROME_VERSION
    client.KEYS, client.CHROME_VERSION = (key,), config.Settings(chrome_version=version).version()
    try:
        yield
    finally:
        client.KEYS, client.CHROME_VERSION = keys, chrome


def _setup(args: argparse.Namespace) -> None:
    current = config.load()
    if args.apk:
        keys, version = config.from_apk(args.apk)
        print(f"Found {len(keys)} API keys in {Path(args.apk).name}" + (f", Chrome {version}" if version else ""))
    elif args.key:
        keys, version = [getpass.getpass("Chrome API key (input hidden): ").strip()], None
    else:
        sys.exit(f"Pass --apk <file> (Chrome for Android, {app.CHROME_PACKAGE}) or --key.")
    version = config.check_version(args.chrome_version or version or current.chrome_version)
    if args.proxy is not None:
        current.proxy = args.proxy or None
    if args.country:
        current.country = args.country.upper()
    elif not current.any_country:
        current.country = config.detect_country(current.proxy) or current.country
    print(f"Testing each key with one read of the {current.home_country} feed ...")
    working = _test(keys, version, current)
    if not working:
        sys.exit(
            "Google took none of the keys. Use the newest Chrome for Android APK, "
            "or pass the version of an older one with --chrome-version."
        )
    current.keys, current.chrome_version = working, version
    path = config.save(current)
    print(f"Saved {len(working)} working keys of Chrome {version} to {path}")
    print(f"Feed country: {current.home_country}" + (" (any country through the proxy)" if current.any_country else ""))


def _status(_: argparse.Namespace) -> None:
    current = config.load()
    if not current.ready:
        sys.exit(f"No Chrome API key yet. Run: {app.CLI} setup --apk <file>")
    proxy = "none" if not current.proxy else ("with {country}" if current.any_country else "fixed")
    print(f"Keys: {len(current.keys)}, Chrome {current.chrome_version}, country {current.home_country}, proxy {proxy}")
    runner = Runner()

    async def go() -> Any:
        try:
            return await runner.run("get_discover_feed", {"limit": 1})
        finally:
            await runner.close()

    try:
        feed = asyncio.run(go())
    except ToolError as exc:
        sys.exit(f"{exc.code}: {exc}")
    print(f"The {feed['country']} feed answers: first card {feed['cards'][0]['title']!r}")


def _tools(args: argparse.Namespace) -> None:
    specs = tools(args.read_only)
    if args.json:
        rows = [{"name": s.name, "access": s.access, "route": s.route, "input_schema": s.input_schema} for s in specs]
        print(json.dumps(rows, indent=2))
        return
    for spec in specs:
        print(f"{spec.name:<30} {spec.access:<5} {spec.route:<62} {spec.description}")


def _parse_args(tool: str, pairs: list[str]) -> dict[str, Any]:
    """key=value pairs; a value is JSON unless the tool's schema wants a string (IDs like 148213977)."""
    if len(pairs) == 1 and pairs[0].lstrip().startswith("{"):
        return json.loads(pairs[0])
    spec = all_tools().get(tool)
    properties = spec.input_schema.get("properties", {}) if spec else {}
    out: dict[str, Any] = {}
    for pair in pairs:
        key, sep, value = pair.partition("=")
        if not sep:
            sys.exit(f"Arguments are key=value or one JSON object, got {pair!r}")
        if properties.get(key, {}).get("type") == "string":
            out[key] = value
            continue
        try:
            out[key] = json.loads(value)
        except ValueError:
            out[key] = value
    return out


def _call(args: argparse.Namespace) -> None:
    runner = Runner(read_only=args.read_only)

    async def go() -> Any:
        try:
            return await runner.run(args.tool, _parse_args(args.tool, args.arguments))
        finally:
            await runner.close()

    try:
        result = asyncio.run(go())
    except ToolError as exc:
        sys.exit(f"{exc.code}: {exc}")
    print(json.dumps(result, indent=2, ensure_ascii=False))


def _mcp(args: argparse.Namespace) -> None:
    from google_discover_api_mcp.mcp_server import run_stdio

    asyncio.run(run_stdio(Runner(read_only=args.read_only)))


def _serve(args: argparse.Namespace) -> None:
    import uvicorn

    from google_discover_api_mcp.api import create_app

    try:
        loopback = ipaddress.ip_address(args.host).is_loopback
    except ValueError:
        loopback = args.host == "localhost"
    if not loopback and not os.environ.get(f"{app.ENV}_MCP_TOKEN"):
        sys.exit(f"Listening beyond this machine needs {app.ENV}_MCP_TOKEN, or anyone on the network can use it.")
    print(
        f"REST API  http://{args.host}:{args.port}{app.API_PREFIX}   docs http://{args.host}:{args.port}/docs",
        file=sys.stderr,
    )
    print(f"MCP       http://{args.host}:{args.port}/mcp", file=sys.stderr)
    uvicorn.run(create_app(Runner(read_only=args.read_only)), host=args.host, port=args.port, log_level="warning")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog=app.CLI,
        description=(__doc__ or "").replace("<cli>", app.CLI),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("setup", help="read Chrome's API key from a Chrome for Android APK, test it and save it")
    p.add_argument("--apk", help=f"a Chrome for Android APK or XAPK ({app.CHROME_PACKAGE}), e.g. from apkeep")
    p.add_argument("--key", action="store_true", help="paste one API key by hand instead")
    p.add_argument("--chrome-version", help="the Chrome version of the key, e.g. 155.0.8059.84, when the APK has none")
    p.add_argument(
        "--country", help="the country of your connection (ISO 3166-1 alpha-2); found from your IP otherwise"
    )
    p.add_argument("--proxy", help="proxy URL for every request; {country} in it is replaced with the call's country")
    p.set_defaults(func=_setup)

    p = sub.add_parser("status", help="show the settings and read the feed once")
    p.set_defaults(func=_status)

    for name, func, text in (
        ("tools", _tools, "list the tools"),
        ("mcp", _mcp, "MCP server over stdio"),
        ("serve", _serve, "REST API and MCP over HTTP"),
    ):
        p = sub.add_parser(name, help=text)
        p.add_argument(
            "--read-only",
            action="store_true",
            default=os.environ.get(f"{app.ENV}_MCP_READ_ONLY") == "1",
            help="only tools that read",
        )
        p.set_defaults(func=func)
        if name == "tools":
            p.add_argument("--json", action="store_true", help="names, routes and input schemas as JSON")
        if name == "serve":
            p.add_argument("--host", default=os.environ.get(f"{app.ENV}_MCP_HOST", "127.0.0.1"))
            p.add_argument("--port", type=int, default=int(os.environ.get(f"{app.ENV}_MCP_PORT", "8787")))

    p = sub.add_parser("call", help="run one tool and print its JSON answer")
    p.add_argument("tool")
    p.add_argument("arguments", nargs="*", help="key=value pairs or one JSON object, e.g. country=GB limit=10")
    p.add_argument("--read-only", action="store_true")
    p.set_defaults(func=_call)

    args = parser.parse_args()
    try:
        args.func(args)
    except ToolError as exc:
        sys.exit(f"{exc.code}: {exc}")
    except KeyboardInterrupt:
        sys.exit(130)


if __name__ == "__main__":
    main()
