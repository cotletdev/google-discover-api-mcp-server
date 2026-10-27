"""Read the Discover feed."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from google_discover_api_mcp.core.tools import tool
from google_discover_api_mcp.google_discover.client import feed, language_of
from google_discover_api_mcp.google_discover.tools._feed import COUNTRY, LANGUAGE

if TYPE_CHECKING:
    from google_discover_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "country": COUNTRY,
        "language": LANGUAGE,
        "limit": {
            "type": "integer",
            "minimum": 1,
            "maximum": 50,
            "description": "How many cards to return, counted from the top of the feed. Default: all (about 30).",
        },
    },
    "required": [],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "country": "US",
    "language": "en-US",
    "fetched_at": "2026-10-25T16:12:40+00:00",
    "cards": [
        {
            "position": 1,
            "title": "Ten herbs that survive a cold windowsill",
            "publisher": "Example News",
            "url": "https://example-news.com/guides/windowsill-herbs",
            "domain": "example-news.com",
            "type": "article",
            "age": "3h",
            "image_url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:example",
        },
        {
            "position": 2,
            "title": "Playful sea otters and mini pumpkins",
            "publisher": "YouTube",
            "url": "https://www.youtube.com/watch?v=example",
            "domain": "youtube.com",
            "type": "video",
            "age": "1d",
            "image_url": "https://encrypted-tbn1.gstatic.com/images?q=tbn:example",
        },
    ],
}


@tool(
    name="get_discover_feed",
    title="Read the Discover feed",
    access="read",
    confirm=False,
    description="The cards Google Discover shows right now in a country, in feed order, with no Google account.",
    details=(
        "Returns the Discover feed Chrome for Android shows on its New Tab page to someone who is not signed in to "
        "Google, read from a home IP in the country asked for: position, title, publisher, URL, domain, article or "
        "video, age as the card shows it, and the card image. It is the default feed of that country and language, "
        "not anyone's personal feed and not data from a panel of users. One read holds about 30 cards; the feed "
        "changes over the day, and a read is reused for up to 15 minutes per country and language."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /feed",
    example_response=EXAMPLE_RESPONSE,
)
async def get_discover_feed(ctx: ToolContext, args: dict[str, Any]) -> Any:
    country = ctx.profile.country
    result = await feed(ctx, country, language_of(country, args.get("language")))
    if limit := args.get("limit"):
        result["cards"] = result["cards"][:limit]
    return result
