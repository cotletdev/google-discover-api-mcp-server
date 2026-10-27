#!/usr/bin/env python3
"""Collect up to 300 different Google Discover cards from many reads, with how often each appeared.

python collect_cards.py --cards 150 --out discover.csv
"""

import argparse

from google_discover_api_mcp.scripting import call, run, write_rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--cards", type=int, default=100, help="How many different cards, at most 300 (default 100)")
    parser.add_argument("--country", help="ISO country code; another than yours needs a proxy (README)")
    parser.add_argument("--language", help="BCP 47 language, e.g. en-US")
    parser.add_argument("--out", help="Save to .csv or .json instead of printing")
    args = parser.parse_args()

    result = call("collect_discover_cards", {"cards": args.cards, "country": args.country, "language": args.language})
    write_rows(result["cards"], args.out)


if __name__ == "__main__":
    run(main)
