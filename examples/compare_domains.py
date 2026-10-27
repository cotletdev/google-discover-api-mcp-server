#!/usr/bin/env python3
"""Compare your site with competitors in the Google Discover feed: cards, titles and positions of each.

python compare_domains.py example-news.com example-daily.com
"""

import argparse

from google_discover_api_mcp.scripting import call, run, write_rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("domains", nargs="+", help="Domains to count; subdomains count too")
    parser.add_argument("--country", help="ISO country code; another than yours needs a proxy (README)")
    parser.add_argument("--out", help="Save to .csv or .json instead of printing")
    args = parser.parse_args()

    feed = call("get_discover_feed", {"country": args.country})
    rows = []
    for domain in args.domains:
        mine = [c for c in feed["cards"] if c["domain"] == domain or c["domain"].endswith(f".{domain}")]
        rows.append(
            {
                "domain": domain,
                "cards": len(mine),
                "positions": [c["position"] for c in mine],
                "titles": [c["title"] for c in mine],
            }
        )
    write_rows(rows, args.out)


if __name__ == "__main__":
    run(main)
