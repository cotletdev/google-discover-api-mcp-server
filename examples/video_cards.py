#!/usr/bin/env python3
"""List the video cards of the Google Discover feed with their titles and positions.

python video_cards.py
"""

import argparse

from google_discover_api_mcp.scripting import call, run, write_rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--country", help="ISO country code; another than yours needs a proxy (README)")
    parser.add_argument("--out", help="Save to .csv or .json instead of printing")
    args = parser.parse_args()

    feed = call("get_discover_feed", {"country": args.country})
    write_rows([card for card in feed["cards"] if card["type"] == "video"], args.out)


if __name__ == "__main__":
    run(main)
