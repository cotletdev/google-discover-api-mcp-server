# Google Discover API and MCP server: the Discover feed in ChatGPT and Claude

**Yes, ChatGPT, Claude and other AI agents can read the Google Discover feed.** That includes Cursor, Codex, OpenClaw and any MCP client, plus automations in n8n, Make and Zapier. Ask in plain words, and the AI reads the Google Discover feed of any country and topic, shows which publishers and stories trend and tracks your own site.

This repo is the missing piece: 3 Google Discover tools for AI assistants and scripts.

## What you can ask

> *Is example-news.com in the Discover feed right now? Give the position, title and age of each card.*
>
> *Which publishers have the most cards in Discover today?*
>
> *List the video cards in the feed with their positions.*
>
> *Collect 200 Discover cards and tell me which topics most of them are about.*

## Two ways to get it

| | [Ready to use, at Cotlet](https://cotlet.dev/integrations/google-discover-api-mcp-server?utm_source=github&utm_medium=readme&utm_campaign=google-discover&utm_content=two-ways) | Run it yourself, this repo |
|---|---|---|
| For | publishers, SEO teams and newsrooms | developers |
| Setup | no Google account, about 2 minutes, nothing to install | Python and a terminal |
| Works in | ChatGPT and Claude apps, on your phone too, Cursor, Codex, OpenClaw, any MCP client, n8n, Make, Zapier, REST API | Claude Code, Claude Desktop, Cursor, Codex on your computer |
| Runs | 24/7, your computer can be off | while your computer is on |
| Price | 7 days free, no card | free |

**[Start free at cotlet.dev →](https://cotlet.dev/signup?app=google-discover&utm_source=github&utm_medium=readme&utm_campaign=google-discover&utm_content=top-button)**

## Run it yourself

A **Google Discover API** and a **Google Discover MCP server** you run on your own computer, in Python. It reads the Discover feed that Chrome for Android shows on its New Tab page to someone not signed in to Google, and gives you every card as JSON: position, title, publisher, URL, domain, article or video, age and image. The same 3 tools we run in production at [Cotlet](https://cotlet.dev/integrations/google-discover-api-mcp-server).

Google has no API for the Discover feed. The Discover report in Search Console counts clicks on your own site; it does not say which cards a country sees or in what order. This repo gives you:

- **MCP server** for Claude Code, Claude Desktop, Cursor, Codex and any MCP client, over stdio or HTTP. [Setup](#mcp-server)
- **REST API** on `http://127.0.0.1:8787/api/v1/google-discover`, with OpenAPI docs at `/docs`. [Setup](#rest-api)
- **Python**: `call("check_domain_in_feed", domain="example-news.com")`, plus 7 ready scripts in [`examples/`](https://github.com/cotletdev/google-discover-api-mcp-server/blob/main/examples/).

No Google account and no browser. Free for your own use, your own business included ([license](#license)).

[![Google Discover MCP server](https://img.shields.io/badge/Google%20Discover%20MCP-3%20tools-6d4aef)](#all-3-tools)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-141318)](#requirements)
[![License: Elastic 2.0](https://img.shields.io/badge/license-Elastic%202.0-141318)](https://github.com/cotletdev/google-discover-api-mcp-server/blob/main/LICENSE)

```bash
pip install google-discover-api-mcp
apkeep -a com.android.chrome -d apk-pure -o 'acknowledge_dangers=true,arch=arm64-v8a' .   # or any Chrome APK
google-discover-mcp setup --apk "com.android.chrome@arm64-v8a.xapk"
google-discover-mcp call get_discover_feed limit=10
claude mcp add google-discover -- google-discover-mcp mcp
```

## Contents

- [Questions from Google Discover users](#questions-from-google-discover-users)
- [How it works](#how-it-works)
- [Requirements](#requirements)
- [Install](#install)
- [Set up: Chrome's API key](#set-up-chromes-api-key)
- [Countries and proxies](#countries-and-proxies)
- [MCP server](#mcp-server)
- [REST API](#rest-api)
- [Python and the example scripts](#python-and-the-example-scripts)
- [All 3 tools](#all-3-tools)
- [Configuration](#configuration)
- [Security](#security)
- [Errors](#errors)
- [Self-hosted or hosted](#self-hosted-or-hosted)
- [FAQ](#faq)
- [License](#license)

## Questions from Google Discover users

**Does Google Discover have an API?**
No. Google has no API for the Discover feed. The only official Discover data is the Discover report in Search Console, with clicks and impressions for sites you own. This repo and [Cotlet](https://cotlet.dev/integrations/google-discover-api-mcp-server?utm_source=github&utm_medium=readme&utm_campaign=google-discover&utm_content=faq-api) give you 3 Google Discover tools as a REST API and an MCP server.

**Can I get a Google Discover API key?**
Not from Google, because there is no Discover API. With Cotlet you get your own API key for the Discover feed, for scripts, n8n, Make, Zapier or any HTTP client.

**Is there an official ChatGPT integration for Google Discover?**
No. Google has no Discover connector for ChatGPT or Claude. Cotlet gives ChatGPT, Claude and other AI agents the live Discover feed of any country.

**How do I get Google Discover into ChatGPT?**
Sign up at [cotlet.dev](https://cotlet.dev/signup?app=google-discover&utm_source=github&utm_medium=readme&utm_campaign=google-discover&utm_content=faq-chatgpt) and add Cotlet to ChatGPT, following the steps in your account. No Google account is needed. ChatGPT needs a server on the internet, so this repo alone, running on your computer, does not connect to ChatGPT.

**Can ChatGPT show me what is trending in Google Discover?**
Yes, with Cotlet. Ask for today's Discover feed in a country and topic, and it lists the stories, publishers and images, and spots your own site.

**Can I automate Google Discover with Zapier, Make or n8n?**
Through Cotlet, n8n, Make and Zapier can pull the Discover feed on a schedule into a sheet, Slack or your CMS.

**Can I use it from my phone?**
Yes, with Cotlet: once it is set up, the ChatGPT and Claude apps on your phone can use Google Discover for you.

**Do I need to be technical?**
For Cotlet, no: you add Cotlet to ChatGPT or Claude, with step-by-step instructions in your account. This repo is for people who are fine with Python and a terminal.

**Do I need a Google account?**
No. Neither Cotlet nor this repo signs in to Google. The feed is read the way a phone in that country sees it.

**Is it free?**
This repo is free, also in your own business. Cotlet is free for 7 days with no card, then one-time credit packs from $29, no subscription. [Pricing](https://cotlet.dev/pricing?utm_source=github&utm_medium=readme&utm_campaign=google-discover&utm_content=faq-price).

**Can I watch several countries?**
Yes, with Cotlet: each request takes a country and a language, so one account covers every market you follow.

## How it works

```text
AI agent (MCP) / script (REST, Python) ──▶ google-discover-mcp on your computer ──protobuf──▶ discover-pa.googleapis.com
                                                     ▲
             google-discover-mcp setup --apk ────────┘ reads Chrome's API key from a Chrome for Android APK, once
```

1. Chrome for Android asks `discover-pa.googleapis.com` for its New Tab feed with one gzipped protobuf request. Signed out, it adds Chrome's own API key. The code that builds this request is open source in Chromium (`components/feed`).
2. This server sends the same request, as Chrome 155 on an Android phone, and reads the cards out of the answer. One read holds about 31 cards. No headless browser runs.
3. Google picks the feed's region from the IP the request comes from, and its language from the request. From your own connection you get the feed of your country. A proxy gets you other countries.

**The API key is not in this repo.** It belongs to Chrome, and Google could switch it off once it sits on GitHub. `setup` reads it from a Chrome for Android APK you download, tests it against the feed and saves it on your computer.

## Requirements

- Python 3.11 or newer.
- A Chrome for Android APK or XAPK (`com.android.chrome`), downloaded once. [How](#set-up-chromes-api-key).
- macOS, Linux or Windows.
- For countries other than yours: a proxy with exits in those countries. [Details](#countries-and-proxies).

## Install

From [PyPI](https://pypi.org/project/google-discover-api-mcp/):

```bash
uv tool install google-discover-api-mcp       # or: pipx install google-discover-api-mcp, or: pip install google-discover-api-mcp
google-discover-mcp --version
```

MCP clients can also run it with no install: `uvx google-discover-api-mcp mcp`.

From source:

```bash
git clone https://github.com/cotletdev/google-discover-api-mcp-server.git
cd google-discover-api-mcp-server
python3 -m venv .venv
. .venv/bin/activate              # Windows: .venv\Scripts\activate
pip install -e .
google-discover-mcp --version
```

With [uv](https://docs.astral.sh/uv/): `uv venv && uv pip install -e .`, then `uv run google-discover-mcp ...`.

Setting it up with an AI agent (Claude Code, Codex, Cursor)? Open it in this folder and ask it to set up the repo: [`AGENTS.md`](https://github.com/cotletdev/google-discover-api-mcp-server/blob/main/AGENTS.md) tells it every step.

To update: `uv tool upgrade google-discover-api-mcp` (or `pip install -U google-discover-api-mcp`), from source `git pull && pip install -e .`. We copy every change of the hosted tools into this repo.

## Set up: Chrome's API key

1. Download Chrome for Android. With [apkeep](https://github.com/EFForg/apkeep) from APKPure:

   ```bash
   apkeep -a com.android.chrome -d apk-pure -o 'acknowledge_dangers=true,arch=arm64-v8a' .
   ```

   APKPure is a mirror of Google Play, not Google. `setup` only reads strings out of the file and runs nothing from it. An APK you pulled from your own Android phone (`adb shell pm path com.android.chrome`, then `adb pull`) works too.

2. Run:

   ```bash
   google-discover-mcp setup --apk "com.android.chrome@arm64-v8a.xapk"
   ```

   ```text
   Found 4 API keys in com.android.chrome@arm64-v8a.xapk, Chrome 155.0.8059.84
   Testing each key with one read of the DE feed ...
   Saved 2 working keys of Chrome 155.0.8059.84 to /Users/you/.config/google-discover-api-mcp/settings.json
   Feed country: DE
   ```

   It finds the `AIzaSy...` keys in Chrome's native libraries and the Chrome version in the manifest, tries each key with one read of the feed and keeps those Google takes. It also asks Cloudflare's trace page (`cloudflare.com/cdn-cgi/trace`) once which country your IP is in.

3. Check at any time:

   ```bash
   google-discover-mcp status
   ```

Already have a key? `google-discover-mcp setup --key --chrome-version 155.0.8059.84` asks for it with hidden input. When Google stops taking the keys (every call ends in `target_error` with HTTP 403), download the newest APK and run `setup` again.

## Countries and proxies

Without a proxy every read comes from your IP, so the feed is the one of your country. `country` may be left out; another country gives `invalid_input`.

For other countries, set a proxy whose URL holds `{country}` (US) or `{country_lower}` (us). Most residential proxy providers put the country in the user name:

```bash
export GOOGLE_DISCOVER_PROXY='http://user-{country}-1:password@proxy.example.com:80'
google-discover-mcp call get_discover_feed country=GB
```

Or save it: `google-discover-mcp setup --apk <file> --proxy '<url>'`. A proxy without a placeholder sends everything through one exit; set `GOOGLE_DISCOVER_COUNTRY` to its country.

Any IP gets a feed, but a home IP gives the local news a person there sees. The feed of one country changes with the city of the IP.

## MCP server

The MCP server lists the 3 tools with their input schemas and descriptions written for agents. All are read-only.

### Claude Code

```bash
claude mcp add google-discover -- google-discover-mcp mcp
# without installing first:
claude mcp add google-discover -- uvx google-discover-api-mcp mcp
```

Run `setup` once before the first call.

### Claude Desktop

`~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "google-discover": {
      "command": "uvx",
      "args": ["google-discover-api-mcp", "mcp"]
    }
  }
}
```

### Cursor

`~/.cursor/mcp.json`, the same block as Claude Desktop. A ready copy is in [`mcp.json`](https://github.com/cotletdev/google-discover-api-mcp-server/blob/main/mcp.json).

### Codex

`~/.codex/config.toml`:

```toml
[mcp_servers.google-discover]
command = "uvx"
args = ["google-discover-api-mcp", "mcp"]
```

### Over HTTP

`google-discover-mcp serve` also serves MCP over streamable HTTP at `http://127.0.0.1:8787/mcp`, for clients that take a URL:

```bash
google-discover-mcp serve
claude mcp add --transport http google-discover http://127.0.0.1:8787/mcp
```

Then ask your agent things like:

> *Is example-news.com in the Discover feed right now? Give the position, title and age of each card.*
>
> *Which publishers have the most cards in Discover today?*
>
> *List the video cards in the feed with their positions.*
>
> *Collect 200 Discover cards and tell me which topics most of them are about.*

## REST API

```bash
google-discover-mcp serve          # http://127.0.0.1:8787, MCP at /mcp, docs at /docs
```

Each tool has its own route under `/api/v1/google-discover`, the same paths as the hosted API at cotlet.dev, so code written against one works with the other. Path parts and the query string are arguments.

```bash
curl 'http://127.0.0.1:8787/api/v1/google-discover/feed?limit=10'
curl 'http://127.0.0.1:8787/api/v1/google-discover/feed/domains/example-news.com'
curl 'http://127.0.0.1:8787/api/v1/google-discover/feed/cards?cards=150'
```

Any tool by name, body as its arguments:

```bash
curl -X POST http://127.0.0.1:8787/api/v1/google-discover/tools/check_domain_in_feed -d '{"domain": "example-news.com"}'
```

- `GET /api/v1/google-discover/tools`: every tool with its route, input schema and an example answer.
- `GET /docs`: interactive OpenAPI docs, `GET /openapi.json` the schema, for n8n, Postman or a generated client.

The server listens on `127.0.0.1` only. To reach it from another device of yours, set a token, and every request then needs `Authorization: Bearer <token>`:

```bash
GOOGLE_DISCOVER_MCP_TOKEN=$(openssl rand -hex 24) google-discover-mcp serve --host 0.0.0.0
```

## Python and the example scripts

Straight from Python, no server needed:

```python
from google_discover_api_mcp import call
from google_discover_api_mcp.scripting import write_rows

feed = call("get_discover_feed")
write_rows(feed["cards"], "discover.csv")
print(call("check_domain_in_feed", domain="example-news.com")["in_feed"])
```

Or one tool from the shell: `google-discover-mcp call check_domain_in_feed domain=example-news.com`, or with a JSON object.

Ready scripts in [`examples/`](https://github.com/cotletdev/google-discover-api-mcp-server/blob/main/examples/). Each prints JSON, takes `--out file.csv` or `--out file.json` where it makes sense, and `--help`:

| Script | What it does |
|---|---|
| [`read_feed.py`](https://github.com/cotletdev/google-discover-api-mcp-server/blob/main/examples/read_feed.py) | The feed, every card with position, title, publisher, URL, type and age. `--limit`. |
| [`top_publishers.py`](https://github.com/cotletdev/google-discover-api-mcp-server/blob/main/examples/top_publishers.py) | Publishers with the most cards in the feed. |
| [`check_domain.py`](https://github.com/cotletdev/google-discover-api-mcp-server/blob/main/examples/check_domain.py) | Whether a site is in the feed now, and where. |
| [`watch_domain.py`](https://github.com/cotletdev/google-discover-api-mcp-server/blob/main/examples/watch_domain.py) | A site's cards that entered or dropped out of the feed since the last run. For cron. |
| [`compare_domains.py`](https://github.com/cotletdev/google-discover-api-mcp-server/blob/main/examples/compare_domains.py) | Cards, positions and titles of your site and its competitors. |
| [`video_cards.py`](https://github.com/cotletdev/google-discover-api-mcp-server/blob/main/examples/video_cards.py) | The video cards of the feed. |
| [`collect_cards.py`](https://github.com/cotletdev/google-discover-api-mcp-server/blob/main/examples/collect_cards.py) | Up to 300 different cards from many reads, with how often each appeared. |

```bash
python examples/check_domain.py --domain example-news.com
python examples/collect_cards.py --cards 200 --out discover.csv
```

On a schedule, cron on your own computer works while it is on: `0 * * * * cd ~/google-discover-api-mcp-server && .venv/bin/python examples/watch_domain.py --domain example-news.com`.

## All 3 tools

`country` is an ISO 3166-1 alpha-2 code (US, GB, DE). Leave it out for your own country. `language` is BCP 47 (en-US, de-DE), by default the country's main language. `google-discover-mcp tools` prints this list, `google-discover-mcp tools --json` adds the input schemas.

| Tool | Access | REST route | What it does |
|---|---|---|---|
| `get_discover_feed` | read | `GET /feed` | The cards Google Discover shows right now in a country, in feed order, with no Google account. |
| `check_domain_in_feed` | read | `GET /feed/domains/{domain}` | Whether cards from a domain are in a country's Discover feed now, and at which positions. |
| `collect_discover_cards` | read | `GET /feed/cards` | Up to 300 different cards Discover shows in a country, from many reads, with how often each appeared. |

A read of one country and language is reused for 15 minutes while the server runs. `collect_discover_cards` reads the feed up to 150 times, 8 at a time, for at most 70 seconds, and merges the cards by URL. From one IP the pool runs dry sooner than from many: 40 reads from one IP gave about 210 different US cards in our tests.

Never built, on purpose: follow, hide or "Not interested" on a card, and the personal feed of a Google account. Those need a signed-in account.

## Configuration

| Variable | Default | What it does |
|---|---|---|
| `GOOGLE_DISCOVER_MCP_HOME` | `~/.config/google-discover-api-mcp` | Folder of `settings.json`. |
| `GOOGLE_DISCOVER_API_KEY` | | Chrome API keys, comma-separated, instead of `setup`. |
| `GOOGLE_DISCOVER_CHROME_VERSION` | `155.0.8059.84` | The Chrome version the keys came from. |
| `GOOGLE_DISCOVER_COUNTRY` | found by `setup` | The country of your IP, or of a proxy without a placeholder. |
| `GOOGLE_DISCOVER_PROXY` | | Proxy for every request, e.g. `http://user-{country}:pass@host:port`. |
| `GOOGLE_DISCOVER_MCP_READ_ONLY` | | `1` is the same as `--read-only`. Every tool already only reads. |
| `GOOGLE_DISCOVER_MCP_TOKEN` | | Bearer token required by `serve`; needed to listen beyond `127.0.0.1`. |
| `GOOGLE_DISCOVER_MCP_HOST`, `GOOGLE_DISCOVER_MCP_PORT` | `127.0.0.1`, `8787` | Address of `serve`. |

## Security

- **No account.** Nothing here signs in to Google, and no cookie or password is read.
- **One host.** Tools reach only `discover-pa.googleapis.com`. `setup` also asks `www.cloudflare.com/cdn-cgi/trace` once for your country.
- **Local by default.** `serve` binds to `127.0.0.1` and refuses another address without `GOOGLE_DISCOVER_MCP_TOKEN`.
- **The settings file** (`settings.json`, mode 0600) holds the keys and your proxy URL, which may carry the proxy's password. Keep it out of git.
- **Google's terms.** This reads a Google service with Chrome's key, outside Chrome. Keep the volume to what you need; you answer for how you use it.

## Errors

The REST API answers `{"error": "<code>", "message": "..."}`. The MCP server returns the same code and message as a tool error.

| Status | Code | What to do |
|---|---|---|
| 401 | `auth_required` | No API key saved. Run `google-discover-mcp setup --apk <file>`. |
| 422 | `invalid_input` | An argument is wrong, or `country` is not yours and no proxy has `{country}`. The message says which. |
| 429 | `rate_limited` | Google is limiting your IP. Wait a minute. |
| 502 | `target_error` | Google refused the key (HTTP 403: take the newest APK and run `setup` again), answered with an error, or changed the feed's layout. `git pull` for the latest tools, or [open an issue](https://github.com/cotletdev/google-discover-api-mcp-server/issues). |
| 504 | `timeout` | Google or the proxy did not answer in time. Retry. |

## Self-hosted or hosted

| | This repo | [Cotlet, hosted](https://cotlet.dev/integrations/google-discover-api-mcp-server?utm_source=github&utm_medium=readme&utm_campaign=google-discover&utm_content=compare) |
|---|---|---|
| Tools | the same 3 | the same 3 |
| Runs | on your computer, while it is on | in the cloud, 24/7 |
| Countries | yours, others through your own proxy | any country per call, from a fresh home IP there |
| API key | from a Chrome APK you download, renewed by you | kept working for you, the feed tested daily |
| `collect_discover_cards` | reads from your IP or proxy | each read from another home IP in the country |
| Works with | MCP clients on your machine, local scripts | Claude.ai and ChatGPT connectors, n8n, Make, any HTTP client |
| Who may use it | you and your own business | you, teams, businesses, agencies |
| Price | free | free 7-day trial with 2,000 credits, no card; then one-time packs from $29 for 5,000 credits |

On the hosted version a successful read uses 10 credits, failed calls are free, and there is no Cloud Browser or account to pay for. `collect_discover_cards` makes many reads and costs more. [Full pricing](https://cotlet.dev/pricing).

## FAQ

**Is there a Google Discover MCP server for Claude, ChatGPT or Cursor?**
Yes, this one runs on your machine: `google-discover-mcp mcp` for Claude Code, Claude Desktop, Cursor and Codex. ChatGPT and Claude.ai connectors need a public HTTPS URL, which the [hosted Google Discover MCP server](https://cotlet.dev/integrations/google-discover-api-mcp-server) gives you.

**Is this my personal Discover feed?**
No. No Google account is involved, so your searches do not shape it. It is the default feed of a country and language, the one a phone that is not signed in gets. People who are signed in see feeds tuned to them.

**Is this a Google Discover scraper?**
It does what people want a scraper for, the cards of the feed as rows, but it parses no HTML and drives no phone or emulator. It sends the request Chrome sends and reads the protobuf answer.

**Is it the same data as DiscoverSnoop or another Discover panel?**
No. A panel collects the personal feeds of many users who run its software and sells totals and history. This reads one signed-out feed per call and keeps no history; `watch_domain.py` on a schedule builds your own.

**Why does the feed change between calls?**
Discover changes through the day, and each read draws its 31 cards from a larger pool. Calls inside 15 minutes reuse the last read of that country and language.

**Why is the API key not in the repo?**
It is Chrome's key, not ours. Google can switch off a key it finds on GitHub, and every copy of this repo would stop at once. Reading it from the APK keeps each install on its own.

**Can it run on a VPS or in Docker?**
Yes. Run `setup` there, or set `GOOGLE_DISCOVER_API_KEY`. The feed then follows the server's IP; a proxy gets you the countries you want.

**Can I use it at work or for my clients?**
At work and in your own business, yes, free. You may not offer it to others as a hosted or managed service. For client work, use [Cotlet](https://cotlet.dev?utm_source=github&utm_medium=readme&utm_campaign=google-discover&utm_content=faq-clients) or write to [contact@cotlet.dev](mailto:contact@cotlet.dev).

**Is it open source?**
The source is public under the Elastic License 2.0: free to use and change, also in your own business, but not to resell as a hosted service.

**A tool broke or I need another one.**
[Open an issue](https://github.com/cotletdev/google-discover-api-mcp-server/issues) with the tool name and the error message.

## License

[Elastic License 2.0](https://github.com/cotletdev/google-discover-api-mcp-server/blob/main/LICENSE). In short:

- **Allowed:** using it for yourself and in your own business, free. Changing the code and sharing it under the same license.
- **Not allowed:** offering it to others as a hosted or managed service, removing the license notices, getting around its limits.

---

<p>
  <a href="https://cotlet.dev">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="assets/logo-white.svg">
      <img src="https://raw.githubusercontent.com/cotletdev/google-discover-api-mcp-server/main/assets/logo.svg" alt="Cotlet" width="120">
    </picture>
  </a>
</p>

Maintained by [Cotlet](https://cotlet.dev?utm_source=github&utm_medium=readme&utm_campaign=google-discover&utm_content=footer) ([@cotletdev](https://x.com/cotletdev)). Google, Google Discover and Chrome are trademarks of Google LLC. This project is unofficial and not affiliated with, endorsed or sponsored by Google.
