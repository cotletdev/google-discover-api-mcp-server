#!/usr/bin/env python3
"""Watch a site in the Google Discover feed: what entered and what dropped out since the last run. For cron.

python watch_domain.py --domain example-news.com --state discover-state.json
"""

import argparse
import json
from pathlib import Path

from google_discover_api_mcp.scripting import call, run


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--domain", required=True, help="The site's domain; its subdomains count too")
    parser.add_argument("--country", action="append", help="ISO country code, repeatable (default: yours)")
    parser.add_argument("--state", default="discover-state.json", help="File with the cards of the last run")
    args = parser.parse_args()

    state_file = Path(args.state)
    before: dict[str, dict[str, str]] = json.loads(state_file.read_text()) if state_file.exists() else {}
    now: dict[str, dict[str, str]] = {}
    report = []
    for country in args.country or [None]:
        result = call("check_domain_in_feed", {"domain": args.domain, "country": country})
        key = result["country"]
        now[key] = {card["url"]: card["title"] for card in result["cards"]}
        old = before.get(key, {})
        report.append(
            {
                "country": key,
                "in_feed": result["in_feed"],
                "positions": [card["position"] for card in result["cards"]],
                "entered": [title for url, title in now[key].items() if url not in old],
                "dropped": [title for url, title in old.items() if url not in now[key]],
            }
        )
    state_file.write_text(json.dumps(now, indent=2, ensure_ascii=False))
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    run(main)
