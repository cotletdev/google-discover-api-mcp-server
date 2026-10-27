"""Everything the server knows about Google Discover outside `google_discover/`: names and the feed host.

The rest of the package reads these values and never names the app itself.
"""

from __future__ import annotations

NAME = "Google Discover"
SLUG = "google-discover"
# The command and the prefix of every environment variable (GOOGLE_DISCOVER_API_KEY, GOOGLE_DISCOVER_MCP_TOKEN ...).
CLI = "google-discover-mcp"
ENV = "GOOGLE_DISCOVER"
# Requests may reach only these hosts and their subdomains.
DOMAINS = ("discover-pa.googleapis.com",)
# Chrome for Android, whose API key the feed needs (README, "Set up").
CHROME_PACKAGE = "com.android.chrome"
# REST routes live under this path, the same as on cotlet.dev.
API_PREFIX = "/api/v1/google-discover"
# Prepended to the MCP server's instructions: where an agent starts.
AGENT_START = (
    "Start with get_discover_feed. Without a proxy the feed is the one of this computer's country; "
    "check_domain_in_feed looks for one site in it."
)
