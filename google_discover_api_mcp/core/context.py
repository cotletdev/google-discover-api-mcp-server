"""What a tool function gets besides its input: the call's country, an HTTP client, a log and a cache.

Requests go out with curl_cffi, which copies Chrome's TLS and HTTP/2 fingerprint. Only the feed host
(`app.DOMAINS`) is reachable. They leave from your own connection, or through your proxy when one is set
(settings.py).
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlsplit

from curl_cffi.requests import AsyncSession

from google_discover_api_mcp import app
from google_discover_api_mcp.core.errors import ErrorCode, ToolError
from google_discover_api_mcp.settings import Settings

DOMAINS = app.DOMAINS
_logger = logging.getLogger(app.CLI)
_logger.addHandler(logging.NullHandler())


def allowed_host(url: str) -> bool:
    host = (urlsplit(url).hostname or "").lower()
    return any(host == domain or host.endswith(f".{domain}") for domain in DOMAINS)


@dataclass(frozen=True)
class HttpResponse:
    status: int
    url: str
    headers: dict[str, str]
    content: bytes

    @property
    def text(self) -> str:
        return self.content.decode("utf-8", errors="replace")


class HttpClient:
    """One connection to the feed host, from your IP or through `proxy`."""

    def __init__(self, proxy: str | None, timeout_s: float = 30.0) -> None:
        self._session = AsyncSession(impersonate="chrome", proxy=proxy or None)  # pyright: ignore[reportArgumentType] - "chrome" is a BrowserType value
        self._timeout_s = timeout_s

    async def request(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        json: Any = None,
        data: Any = None,
        headers: dict[str, str] | None = None,
    ) -> HttpResponse:
        if not allowed_host(url):
            raise ToolError(f"Request outside {DOMAINS[0]}.", ErrorCode.INTERNAL_ERROR)
        try:
            raw = await self._session.request(
                method.upper(),  # pyright: ignore[reportArgumentType] - an HTTP method name
                url,
                params=params,
                json=json,
                data=data,
                headers=headers,
                timeout=self._timeout_s,
                allow_redirects=False,
            )
        except Exception as exc:
            raise ToolError(f"Google did not answer: {type(exc).__name__}.", ErrorCode.TARGET_ERROR) from exc
        return HttpResponse(
            status=raw.status_code,
            url=str(raw.url),
            headers={k.lower(): v or "" for k, v in raw.headers.items()},
            content=raw.content,
        )

    async def close(self) -> None:
        await self._session.close()


class Log:
    """The few log calls the tools make, on Python's logging (quiet unless you configure it)."""

    def _emit(self, level: int, event: str, fields: dict[str, Any]) -> None:
        extra = " ".join(f"{key}={value}" for key, value in fields.items())
        _logger.log(level, f"{event} {extra}".strip())

    def info(self, event: str, **fields: Any) -> None:
        self._emit(logging.INFO, event, fields)

    def warning(self, event: str, **fields: Any) -> None:
        self._emit(logging.WARNING, event, fields)


@dataclass(frozen=True)
class Profile:
    """The call's country: where the feed is read from."""

    country: str


@dataclass
class ToolContext:
    settings: Settings
    profile: Profile
    cache: dict[str, tuple[float, str]] = field(default_factory=dict, repr=False)
    log: Log = field(default_factory=Log, repr=False)
    _http: HttpClient | None = field(default=None, repr=False)
    _extra: list[HttpClient] = field(default_factory=list, repr=False)

    @property
    def http(self) -> HttpClient:
        if self._http is None:
            self._http = HttpClient(self.settings.proxy_for(self.profile.country))
        return self._http

    def new_http(self) -> HttpClient:
        """Another client for a parallel read; with a rotating proxy it may get another IP."""
        client = HttpClient(self.settings.proxy_for(self.profile.country))
        self._extra.append(client)
        return client

    async def cache_get(self, key: str) -> str | None:
        """A recent answer, kept in this process."""
        entry = self.cache.get(key)
        if entry is None or entry[0] < time.monotonic():
            return None
        return entry[1]

    async def cache_set(self, key: str, value: str, ttl_s: int) -> None:
        self.cache[key] = (time.monotonic() + ttl_s, value)

    async def close(self) -> None:
        for client in [*self._extra, *([self._http] if self._http else [])]:
            await client.close()
        self._http, self._extra = None, []
