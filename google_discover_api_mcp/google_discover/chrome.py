"""Chrome's API keys for the feed and the Chrome version they belong to, from your settings.

This file is the repo's own (the hosted service keeps its keys private). `google-discover-mcp setup` reads the
keys from a Chrome for Android APK and saves them; client.py reads them here at each request.
"""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from typing import overload

from google_discover_api_mcp import settings


class _Keys(Sequence[str]):
    """The saved keys, read again at each use, so `setup` takes effect without a restart."""

    def _keys(self) -> list[str]:
        return settings.load().keys

    @overload
    def __getitem__(self, index: int) -> str: ...
    @overload
    def __getitem__(self, index: slice) -> Sequence[str]: ...
    def __getitem__(self, index: int | slice) -> str | Sequence[str]:
        return self._keys()[index]

    def __len__(self) -> int:
        return len(self._keys())

    def __iter__(self) -> Iterator[str]:
        return iter(self._keys())


class _Version(Sequence[int]):
    """major, minor, build, patch of the Chrome the keys came from."""

    @overload
    def __getitem__(self, index: int) -> int: ...
    @overload
    def __getitem__(self, index: slice) -> Sequence[int]: ...
    def __getitem__(self, index: int | slice) -> int | Sequence[int]:
        return settings.load().version()[index]

    def __len__(self) -> int:
        return 4

    def __iter__(self) -> Iterator[int]:
        return iter(settings.load().version())


KEYS = _Keys()
CHROME_VERSION = _Version()
