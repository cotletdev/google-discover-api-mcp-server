"""The Discover feed of Chrome for Android, signed out, by one request (docs/05, 25.10.2026).

Chrome asks `POST discover-pa.googleapis.com/v1:queryInteractiveFeed?key=<Chrome's API key>` with a gzipped
feedwire.Request and gets every card of the signed-out feed (about 30, no next page) in one protobuf answer.
The request copies Chromium components/feed/core/v2/proto_util.cc (CreateFeedQueryRequest): Android, the
Chrome app, a phone screen, the feed language. The region is the exit IP's country.

KEYS and CHROME_VERSION live in chrome.py. When Google stops taking a key, the next one is tried.
"""

from __future__ import annotations

import gzip
import json
import re
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, Protocol
from urllib.parse import urlsplit

from google_discover_api_mcp.core.errors import ErrorCode, ToolError
from google_discover_api_mcp.google_discover import protowire as pw
from google_discover_api_mcp.google_discover.chrome import CHROME_VERSION, KEYS

if TYPE_CHECKING:
    from google_discover_api_mcp.core.context import ToolContext


# What `ask` needs of the HTTP client and the log, so the public repo can pass its own (exits.py).
class _Answer(Protocol):
    @property
    def status(self) -> int: ...
    @property
    def content(self) -> bytes: ...


class HttpClient(Protocol):
    async def request(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, Any] | None = ...,
        data: Any = ...,
        headers: dict[str, str] | None = ...,
    ) -> _Answer: ...


class BoundLogger(Protocol):
    def warning(self, event: str, **fields: Any) -> Any: ...


FEED_HOST = "discover-pa.googleapis.com"
FEED_URL = f"https://{FEED_HOST}/v1:queryInteractiveFeed"
ANDROID_MAJOR, ANDROID_API = 14, 34
# The feed changes over hours, not minutes: one answer per country and language serves every call for a while.
CACHE_S = 15 * 60
# Capability values Chrome sends (capability.proto), in its order.
_CAPABILITIES = (19, 37, 38, 24, 67, 9, 5, 43, 20, 17, 10, 104, 35, 77, 30, 93, 27)
_ARM64, _RELEASE, _ANDROID, _CHROME_ANDROID, _MANUAL_REFRESH, _CHROME_DISCOVER_FEED = 2, 4, 1, 3, 1, 19
# The language of the feed when the call names none: the country's main one, else US English.
LANGUAGES = {
    "AR": "es-AR", "AT": "de-AT", "AU": "en-AU", "BE": "nl-BE", "BR": "pt-BR", "CA": "en-CA", "CH": "de-CH",
    "CL": "es-CL", "CO": "es-CO", "CZ": "cs-CZ", "DE": "de-DE", "DK": "da-DK", "ES": "es-ES", "FI": "fi-FI",
    "FR": "fr-FR", "GB": "en-GB", "GR": "el-GR", "HU": "hu-HU", "ID": "id-ID", "IE": "en-IE", "IN": "en-IN",
    "IT": "it-IT", "JP": "ja-JP", "KR": "ko-KR", "MX": "es-MX", "MY": "en-MY", "NG": "en-NG", "NL": "nl-NL",
    "NO": "nb-NO", "NZ": "en-NZ", "PH": "en-PH", "PL": "pl-PL", "PT": "pt-PT", "RO": "ro-RO", "SE": "sv-SE",
    "SG": "en-SG", "TH": "th-TH", "TR": "tr-TR", "TW": "zh-TW", "UA": "uk-UA", "US": "en-US", "VN": "vi-VN",
    "ZA": "en-ZA",
}  # fmt: skip
# A card in the answer: its link, title, image, publisher and favicon, one after another.
_IMAGE = "gstatic.com/images?"
_AGE = re.compile(r"^(\d+\s?(s|m|min|h|d|w|mo|y)|yesterday|just now)$", re.IGNORECASE)


def language_of(country: str, language: str | None) -> str:
    return language or LANGUAGES.get(country, "en-US")


def _request(language: str) -> bytes:
    major, minor, build, patch = CHROME_VERSION
    platform = pw.uint(1, ANDROID_MAJOR) + pw.uint(5, _ARM64) + pw.uint(6, _RELEASE) + pw.uint(7, ANDROID_API)
    app = (
        pw.uint(1, major) + pw.uint(2, minor) + pw.uint(3, build) + pw.uint(4, patch)
        + pw.uint(5, _ARM64) + pw.uint(6, _RELEASE) + pw.uint(7, ANDROID_API)
    )  # fmt: skip
    # A 1080 x 2400 phone at 2.625 dpr, as a Pixel.
    display = pw.float32(1, 2.625) + pw.uint(2, 1080) + pw.uint(3, 2400)
    client = (
        pw.uint(1, _ANDROID) + pw.message(2, platform) + pw.uint(3, _CHROME_ANDROID) + pw.message(4, app)
        + pw.message(5, language.encode()) + pw.message(6, display)
    )  # fmt: skip
    query = pw.uint(1, _MANUAL_REFRESH) + pw.message(9, pw.uint(1, _CHROME_DISCOVER_FEED))
    feed = pw.message(1, client) + pw.message(2, query) + b"".join(pw.uint(4, cap) for cap in _CAPABILITIES)
    return pw.uint(1, 1) + pw.message(1000, feed)


def _headers(language: str) -> dict[str, str]:
    major, minor, build, patch = CHROME_VERSION
    return {
        "content-type": "application/x-protobuf",
        "content-encoding": "gzip",
        "accept-language": f"{language},{language.split('-')[0]};q=0.9",
        "user-agent": (
            f"Mozilla/5.0 (Linux; Android {ANDROID_MAJOR}; K) AppleWebKit/537.36 (KHTML, like Gecko) "
            f"Chrome/{major}.{minor}.{build}.{patch} Mobile Safari/537.36"
        ),
    }


def _domain(url: str) -> str:
    host = (urlsplit(url).hostname or "").lower()
    return host.removeprefix("www.").removeprefix("m.")


def cards(strings: list[str]) -> list[dict[str, Any]]:
    """Cards in feed order. Each appears as link, title, image, publisher, favicon; its age follows soon after."""
    found: list[dict[str, Any]] = []
    seen: set[str] = set()
    for at in range(len(strings) - 4):
        url, title, image, publisher, favicon = strings[at : at + 5]
        if (
            not url.startswith(("https://", "http://"))
            or "gstatic." in url
            or url in seen
            or title.startswith("http")
            or _IMAGE not in image
            or publisher.startswith("http")
            or "favicon" not in favicon
        ):
            continue
        seen.add(url)
        age = next((text for text in strings[at + 5 : at + 40] if _AGE.match(text)), None)
        domain = _domain(url)
        found.append(
            {
                "position": len(found) + 1,
                "title": title,
                "publisher": publisher,
                "url": url,
                "domain": domain,
                "type": "video" if domain == "youtube.com" else "article",
                "age": age,
                "image_url": image,
            }
        )
    return found


async def ask(http: HttpClient, log: BoundLogger, language: str) -> bytes:
    """One read of the feed through `http`'s exit: the raw answer."""
    body = gzip.compress(_request(language))
    refused = ""
    for key in KEYS:
        response = await http.request("POST", FEED_URL, params={"key": key}, data=body, headers=_headers(language))
        if response.status == 200:
            return response.content
        if response.status == 429:
            raise ToolError("Google is rate limiting the feed. Try again in a minute.", ErrorCode.RATE_LIMITED)
        if response.status >= 500:
            raise ToolError(f"Google did not serve the feed (HTTP {response.status}).", ErrorCode.TARGET_ERROR)
        # 403 for a key Google stopped taking: the next key of the same Chrome.
        refused = f"HTTP {response.status}"
        log.warning("Discover feed refused a key", status=response.status, key_suffix=key[-4:])
    raise ToolError(f"Google refused the feed request ({refused}).", ErrorCode.TARGET_ERROR)


async def feed(ctx: ToolContext, country: str, language: str) -> dict[str, Any]:
    """The feed of one country and language, from cache when it is fresh."""
    cache_key = f"feed:{country}:{language}"
    if cached := await ctx.cache_get(cache_key):
        return json.loads(cached)
    found = cards(pw.strings(await ask(ctx.http, ctx.log, language)))
    if not found:
        raise ToolError("Google answered with an empty feed. Try again in a minute.", ErrorCode.TARGET_ERROR)
    result = {
        "country": country,
        "language": language,
        "fetched_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "cards": found,
    }
    await ctx.cache_set(cache_key, json.dumps(result), CACHE_S)
    return result
