"""Your settings: Chrome's API key for the feed, its Chrome version, your country and an optional proxy.

There is nothing to sign in to. The feed is the one Chrome for Android shows on its New Tab page to someone
who is not signed in to Google, and Google takes the request only with Chrome's own API key. This repo does
not ship that key: `<cli> setup --apk <file>` reads it from a Chrome for Android APK you download, tests it
against the feed and saves it here, readable by your user alone (0600).

Region: Google picks the feed's region from the IP the request comes from. Without a proxy that is your own
connection, so the feed is the one of your country. A proxy URL with `{country}` in it (most residential
proxy providers put the country in the user name) reads the feed of any country.
"""

from __future__ import annotations

import io
import json
import locale
import os
import re
import stat
import zipfile
from dataclasses import asdict, dataclass, field
from pathlib import Path

from google_discover_api_mcp import app
from google_discover_api_mcp.core.errors import ErrorCode, ToolError

# Answers `loc=<country>` for the IP of the request; `setup` uses it once to learn your country.
_TRACE_URL = "https://www.cloudflare.com/cdn-cgi/trace"
# The Chrome version the request names when you give a key by hand without one.
DEFAULT_CHROME_VERSION = "155.0.8059.84"
_KEY = re.compile(rb"AIzaSy[0-9A-Za-z_-]{33}")
_VERSION = re.compile(r"^\d{2,4}\.\d+\.\d{3,5}\.\d+$")
# versionName in the binary AndroidManifest.xml is UTF-16.
_D, _DOT = rb"(?:[0-9]\x00)", rb"\.\x00"
_MANIFEST_VERSION = re.compile(_D + b"{3}" + _DOT + _D + _DOT + _D + b"{4}" + _DOT + _D + b"{1,3}")


def home() -> Path:
    """Where the settings are kept: $<ENV>_MCP_HOME, or ~/.config/<slug>-api-mcp."""
    return Path(os.environ.get(f"{app.ENV}_MCP_HOME") or Path.home() / ".config" / f"{app.SLUG}-api-mcp")


def settings_path() -> Path:
    return home() / "settings.json"


@dataclass
class Settings:
    keys: list[str] = field(default_factory=list)
    chrome_version: str = DEFAULT_CHROME_VERSION
    # The country of your own connection (ISO 3166-1 alpha-2): the feed you get without a proxy. `setup` sets it.
    country: str | None = None
    # A proxy for every request; `{country}` (US) or `{country_lower}` (us) in it becomes the call's country.
    proxy: str | None = None

    @property
    def ready(self) -> bool:
        return bool(self.keys)

    @property
    def home_country(self) -> str:
        return (self.country or system_country() or "US").upper()

    @property
    def any_country(self) -> bool:
        """True when the proxy can exit in any country the call names."""
        return bool(self.proxy and ("{country}" in self.proxy or "{country_lower}" in self.proxy))

    def proxy_for(self, country: str) -> str | None:
        if not self.proxy:
            return None
        return self.proxy.replace("{country}", country.upper()).replace("{country_lower}", country.lower())

    def version(self) -> tuple[int, int, int, int]:
        major, minor, build, patch = (int(part) for part in self.chrome_version.split("."))
        return major, minor, build, patch


def system_country() -> str | None:
    """The region of this computer's locale (pl_PL gives PL), when it has one."""
    for value in (os.environ.get("LC_ALL"), os.environ.get("LANG"), locale.getlocale()[0]):
        match = re.match(r"^[a-z]{2,3}[_-]([A-Z]{2})\b", value or "")
        if match:
            return match.group(1)
    return None


def detect_country(proxy: str | None) -> str | None:
    """The country of the IP requests leave from (Cloudflare's trace page), None when it does not answer."""
    from curl_cffi import requests

    try:
        answer = requests.get(_TRACE_URL, proxy=proxy or None, timeout=10)
    except Exception:  # noqa: BLE001 - any network failure means "unknown", setup falls back to --country
        return None
    match = re.search(r"^loc=([A-Z]{2})$", answer.text, re.MULTILINE)
    return match.group(1) if match and match.group(1) != "XX" else None


def load() -> Settings:
    """The saved settings, with <ENV>_API_KEY, <ENV>_CHROME_VERSION, <ENV>_COUNTRY and <ENV>_PROXY on top."""
    settings = Settings()
    path = settings_path()
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        settings = Settings(**{k: v for k, v in data.items() if k in Settings.__dataclass_fields__})
    if keys := os.environ.get(f"{app.ENV}_API_KEY", "").strip():
        settings.keys = [key.strip() for key in keys.split(",") if key.strip()]
    if version := os.environ.get(f"{app.ENV}_CHROME_VERSION", "").strip():
        settings.chrome_version = version
    if country := os.environ.get(f"{app.ENV}_COUNTRY", "").strip():
        settings.country = country.upper()
    if proxy := os.environ.get(f"{app.ENV}_PROXY", "").strip():
        settings.proxy = proxy
    return settings


def save(settings: Settings) -> Path:
    path = settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, stat.S_IRUSR | stat.S_IWUSR)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        json.dump(asdict(settings), fh, indent=2)
    os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
    return path


def check_version(version: str) -> str:
    if not _VERSION.match(version):
        raise ToolError(
            f"A Chrome version looks like {DEFAULT_CHROME_VERSION}, got {version!r}.", ErrorCode.INVALID_INPUT
        )
    return version


def _scan(archive: zipfile.ZipFile, keys: list[str], versions: list[str]) -> None:
    """Keys from the native libraries, the version from the manifest; split APKs inside an XAPK too."""
    for info in archive.infolist():
        name = info.filename
        if name.endswith(".apk"):
            with archive.open(info) as fh, zipfile.ZipFile(io.BytesIO(fh.read())) as inner:
                _scan(inner, keys, versions)
        elif name == "manifest.json":
            with archive.open(info) as fh:
                data = json.loads(fh.read() or b"{}")
            if isinstance(data, dict) and isinstance(data.get("version_name"), str):
                versions.append(data["version_name"])
        elif name == "AndroidManifest.xml":
            with archive.open(info) as fh:
                found = _MANIFEST_VERSION.search(fh.read())
            if found:
                versions.append(found.group(0).decode("utf-16-le"))
        elif name.endswith(".so"):
            with archive.open(info) as fh:
                for key in _KEY.findall(fh.read()):
                    if key.decode() not in keys:
                        keys.append(key.decode())


def from_apk(path: str) -> tuple[list[str], str | None]:
    """Every API key in a Chrome for Android APK or XAPK, and its Chrome version when the file names one."""
    file = Path(path).expanduser()
    if not file.is_file():
        raise ToolError(f"No file at {file}.", ErrorCode.INVALID_INPUT)
    keys: list[str] = []
    versions: list[str] = []
    try:
        with zipfile.ZipFile(file) as archive:
            _scan(archive, keys, versions)
    except zipfile.BadZipFile as exc:
        raise ToolError(f"{file.name} is not an APK or XAPK file.", ErrorCode.INVALID_INPUT) from exc
    if not keys:
        raise ToolError(
            f"No API key in {file.name}. Is it Chrome for Android ({app.CHROME_PACKAGE}), with its native libraries?",
            ErrorCode.INVALID_INPUT,
        )
    version = next((v for v in versions if _VERSION.match(v)), None)
    return keys, version
