#!/usr/bin/env python3
"""Read the Google Discover feed: every card with position, title, publisher, URL, type and age.

python read_feed.py --limit 10 --out feed.csv
"""

import argparse

from google_discover_api_mcp.scripting import call, run, write_rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--country", help="ISO country code; another than yours needs a proxy (README)")
    parser.add_argument("--language", help="BCP 47 language, e.g. en-GB (default: the country's main one)")
    parser.add_argument("--limit", type=int, help="Only the top N cards")
    parser.add_argument("--out", help="Save to .csv or .json instead of printing")
    args = parser.parse_args()

    feed = call("get_discover_feed", {"country": args.country, "language": args.language, "limit": args.limit})
    write_rows(feed["cards"], args.out)


if __name__ == "__main__":
    run(main)
