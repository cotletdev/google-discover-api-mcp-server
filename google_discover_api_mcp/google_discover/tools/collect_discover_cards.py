"""Collect many Discover cards of a country."""

from __future__ import annotations

import asyncio
import time
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from google_discover_api_mcp.core.errors import ErrorCode, ToolError
from google_discover_api_mcp.core.tools import tool
from google_discover_api_mcp.google_discover import protowire as pw
from google_discover_api_mcp.google_discover.client import cards, language_of
from google_discover_api_mcp.google_discover.exits import ask_from_new_exit
from google_discover_api_mcp.google_discover.tools._feed import COUNTRY, LANGUAGE

if TYPE_CHECKING:
    from google_discover_api_mcp.core.context import ToolContext

# One read holds about 31 cards, drawn from a larger pool that changes with each read and each home IP.
# Measured 25.10.2026 in the US: 10 reads 126 unique cards, 40 reads 212, 90 reads 265.
MAX_CARDS = 300
DEFAULT_CARDS = 300
MAX_READS = 150
PARALLEL = 8
# Stop when the pool runs dry: this many reads in a row brought at most STALL_NEW new cards.
STALL_READS = 15
STALL_NEW = 2
# The agent gets its answer within 85 s (api ANSWER_WITHIN_S; Cloudflare cuts at 100 s): room to wait and reply.
DEADLINE_S = 70

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "cards": {
            "type": "integer",
            "minimum": 1,
            "maximum": MAX_CARDS,
            "description": f"How many different cards to collect, at most {MAX_CARDS}. Default: {DEFAULT_CARDS}.",
        },
        "country": COUNTRY,
        "language": LANGUAGE,
    },
    "required": [],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "country": "US",
    "language": "en-US",
    "collected_at": "2026-10-25T17:40:12+00:00",
    "reads": 74,
    "complete": True,
    "cards": [
        {
            "title": "Ten herbs that survive a cold windowsill",
            "publisher": "Example News",
            "url": "https://example-news.com/guides/windowsill-herbs",
            "domain": "example-news.com",
            "type": "article",
            "age": "3h",
            "image_url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:example",
            "seen_in": 41,
            "best_position": 1,
        },
        {
            "title": "Playful sea otters and mini pumpkins",
            "publisher": "YouTube",
            "url": "https://www.youtube.com/watch?v=example",
            "domain": "youtube.com",
            "type": "video",
            "age": "1d",
            "image_url": "https://encrypted-tbn1.gstatic.com/images?q=tbn:example",
            "seen_in": 3,
            "best_position": 12,
        },
    ],
}


class _Pool:
    """Cards of every read, by URL: how many reads showed each and its best position."""

    def __init__(self) -> None:
        self.cards: dict[str, dict[str, Any]] = {}
        self.reads = 0
        self.growth: list[int] = []

    def add(self, found: list[dict[str, Any]]) -> None:
        before = len(self.cards)
        for card in found:
            kept = self.cards.get(card["url"])
            if kept is None:
                kept = {k: v for k, v in card.items() if k != "position"} | {"seen_in": 0, "best_position": 999}
                self.cards[card["url"]] = kept
            kept["seen_in"] += 1
            kept["best_position"] = min(kept["best_position"], card["position"])
        self.reads += 1
        self.growth.append(len(self.cards) - before)

    def stalled(self) -> bool:
        return len(self.growth) >= STALL_READS and sum(self.growth[-STALL_READS:]) <= STALL_NEW


async def _read(ctx: ToolContext, language: str) -> list[dict[str, Any]] | None:
    """One read through a fresh home IP in the call's country; None when that exit or read failed."""
    try:
        return cards(pw.strings(await ask_from_new_exit(ctx, language)))
    except ToolError as error:
        ctx.log.info("Discover read failed, the collection goes on", error=str(error))
        return None


@tool(
    name="collect_discover_cards",
    title="Collect Discover cards",
    access="read",
    confirm=False,
    description="Up to 300 different cards Discover shows in a country, from many reads, with how often each appeared.",
    details=(
        "One read of the Discover feed holds about 31 cards, and each read draws them from a larger pool. This "
        "tool reads the feed of the country many times in parallel, each time from another home IP there, until it "
        "has the number of different cards asked for or the pool runs dry, and returns them at once. seen_in says "
        "in how many reads a card appeared (a card in most reads is the core of the feed, one seen once is rare) and "
        "best_position its highest place. Cards come most often seen first. complete is false when the feed held "
        "fewer different cards than asked for in the time of one call. A call takes up to about 70 seconds and costs "
        "more credits than one read, because it makes many."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /feed/cards",
    example_response=EXAMPLE_RESPONSE,
    timeout_s=120,
)
async def collect_discover_cards(ctx: ToolContext, args: dict[str, Any]) -> Any:
    wanted = args.get("cards") or DEFAULT_CARDS
    country = ctx.profile.country
    language = language_of(country, args.get("language"))
    pool = _Pool()
    deadline = time.monotonic() + DEADLINE_S
    started_reads = 0
    while len(pool.cards) < wanted and started_reads < MAX_READS and not pool.stalled():
        if time.monotonic() > deadline:
            break
        batch = min(PARALLEL, MAX_READS - started_reads)
        started_reads += batch
        remaining = deadline - time.monotonic()
        try:
            async with asyncio.timeout(max(remaining, 1)):
                results = await asyncio.gather(*(_read(ctx, language) for _ in range(batch)))
        except TimeoutError:
            break
        for found in results:
            if found:
                pool.add(found)
    if not pool.cards:
        raise ToolError("Google did not serve the feed. Try again in a minute.", ErrorCode.TARGET_ERROR)
    ranked = sorted(pool.cards.values(), key=lambda card: (-card["seen_in"], card["best_position"]))
    return {
        "country": country,
        "language": language,
        "collected_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "reads": pool.reads,
        "complete": len(pool.cards) >= wanted,
        "cards": ranked[:wanted],
    }
