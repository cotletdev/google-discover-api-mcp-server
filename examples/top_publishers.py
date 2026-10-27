#!/usr/bin/env python3
"""Count the cards of each publisher in the Google Discover feed, most cards first.

python top_publishers.py --top 10
"""

import argparse
from collections import Counter

from google_discover_api_mcp.scripting import call, run, write_rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--country", help="ISO country code; another than yours needs a proxy (README)")
    parser.add_argument("--language", help="BCP 47 language, e.g. de-DE")
    parser.add_argument("--top", type=int, default=10, help="How many publishers to list (default 10)")
    parser.add_argument("--out", help="Save to .csv or .json instead of printing")
    args = parser.parse_args()

    feed = call("get_discover_feed", {"country": args.country, "language": args.language})
    counts = Counter((card["publisher"], card["domain"]) for card in feed["cards"])
    rows = [
        {"publisher": publisher, "domain": domain, "cards": n, "country": feed["country"]}
        for (publisher, domain), n in counts.most_common(args.top)
    ]
    write_rows(rows, args.out)


if __name__ == "__main__":
    run(main)
