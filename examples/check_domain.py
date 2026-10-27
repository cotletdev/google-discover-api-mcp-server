#!/usr/bin/env python3
"""Check whether a site is in the Google Discover feed now, and at which positions.

python check_domain.py --domain example-news.com
"""

import argparse
import json

from google_discover_api_mcp.scripting import call, run


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--domain", required=True, help="The site's domain; its subdomains count too")
    parser.add_argument("--country", help="ISO country code; another than yours needs a proxy (README)")
    parser.add_argument("--language", help="BCP 47 language, e.g. en-US")
    args = parser.parse_args()

    result = call("check_domain_in_feed", {"domain": args.domain, "country": args.country, "language": args.language})
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    run(main)
