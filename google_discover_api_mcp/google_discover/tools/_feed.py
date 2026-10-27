"""Inputs shared by the feed tools: country and language of the feed."""

from __future__ import annotations

from typing import Any

COUNTRY: dict[str, Any] = {
    "type": "string",
    "pattern": "^[A-Za-z]{2}$",
    "description": (
        "Country of the feed, ISO 3166-1 alpha-2 (US, GB, DE, PL ...). The feed is read from a home IP there, "
        "so its stories are the ones Discover shows in that country. Default: US."
    ),
}
LANGUAGE: dict[str, Any] = {
    "type": "string",
    "pattern": "^[a-z]{2,3}(-[A-Za-z]{2,4})?$",
    "description": "Language of the feed, BCP 47 (en-US, de-DE, pt-BR). Default: the country's main language.",
}
