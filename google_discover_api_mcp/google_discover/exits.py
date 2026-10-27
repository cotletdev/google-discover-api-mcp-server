"""One read of the feed for collect_discover_cards, through a new connection.

This file is the repo's own. The hosted service takes a new home IP in the country for each read; here
every read leaves from your connection, or from your proxy, which may give each connection another IP.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from google_discover_api_mcp.google_discover.client import ask

if TYPE_CHECKING:
    from google_discover_api_mcp.core.context import ToolContext


async def ask_from_new_exit(ctx: ToolContext, language: str) -> bytes:
    """The raw answer of one read through a new connection."""
    return await ask(ctx.new_http(), ctx.log, language)
