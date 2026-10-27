"""Check if a domain is in the Discover feed."""

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
        "domain": {
            "type": "string",
            "minLength": 3,
            "maxLength": 253,
            "description": "The site's domain, e.g. example-news.com. Its subdomains count too.",
        },
        "country": COUNTRY,
        "language": LANGUAGE,
    },
    "required": ["domain"],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "domain": "example-news.com",
    "country": "US",
    "language": "en-US",
    "fetched_at": "2026-10-25T16:12:40+00:00",
    "in_feed": True,
    "feed_size": 31,
    "cards": [
        {
            "position": 4,
            "title": "Ten herbs that survive a cold windowsill",
            "publisher": "Example News",
            "url": "https://example-news.com/guides/windowsill-herbs",
            "domain": "example-news.com",
            "type": "article",
            "age": "3h",
            "image_url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:example",
        }
    ],
}


def _bare(domain: str) -> str:
    domain = domain.strip().lower()
    for prefix in ("https://", "http://"):
        domain = domain.removeprefix(prefix)
    return domain.split("/", 1)[0].removeprefix("www.")


@tool(
    name="check_domain_in_feed",
    title="Check if a domain is in the Discover feed",
    access="read",
    confirm=False,
    description="Whether cards from a domain are in a country's Discover feed now, and at which positions.",
    details=(
        "Reads the same feed as get_discover_feed (signed out, from a home IP in the country) and keeps the cards "
        "whose link is on the domain or one of its subdomains. in_feed is false when none is there right now; "
        "feed_size says how many cards the feed held. Run it on a schedule to see when a story enters and leaves."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /feed/domains/{domain}",
    example_response=EXAMPLE_RESPONSE,
)
async def check_domain_in_feed(ctx: ToolContext, args: dict[str, Any]) -> Any:
    domain = _bare(args["domain"])
    country = ctx.profile.country
    result = await feed(ctx, country, language_of(country, args.get("language")))
    matched = [card for card in result["cards"] if card["domain"] == domain or card["domain"].endswith(f".{domain}")]
    return {
        "domain": domain,
        "country": result["country"],
        "language": result["language"],
        "fetched_at": result["fetched_at"],
        "in_feed": bool(matched),
        "feed_size": len(result["cards"]),
        "cards": matched,
    }
