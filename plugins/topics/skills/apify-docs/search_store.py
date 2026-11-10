"""Search Apify Store for Actors via the public Store API (no token needed).

Calls GET https://api.apify.com/v2/store?search=<query> (documented at
https://docs.apify.com/api/v2/store-get.md and in apify.com/llms.txt) and
prints one compact block per Actor: `<username>/<name>`, title, pricing
model, 30-day users, rating, and a truncated description. Read an Actor's
full README / input / pricing with `webref_cli.py fetch-page
https://apify.com/<username>/<name>`.

Usage:
    python search_store.py "google maps"
    python search_store.py instagram --limit 5
    python search_store.py "linkedin profile" --json
"""

from __future__ import annotations

import argparse
import json
import sys

import requests

STORE_API_URL = "https://api.apify.com/v2/store"
REQUEST_TIMEOUT_SECONDS = 30
DEFAULT_LIMIT = 10
DESCRIPTION_MAX_CHARS = 200


def search(query: str, limit: int) -> dict:
    try:
        response = requests.get(
            STORE_API_URL,
            params={"search": query, "limit": limit},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        print(f"ERROR: Store search failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
    return response.json().get("data", {})


def format_item(item: dict) -> str:
    stats = item.get("stats") or {}
    pricing = (item.get("currentPricingInfo") or {}).get("pricingModel", "?")
    rating = item.get("actorReviewRating")
    rating_text = f"{rating:.2f} ({item.get('actorReviewCount', 0)} reviews)" if rating else "-"
    description = (item.get("description") or "").strip()
    if len(description) > DESCRIPTION_MAX_CHARS:
        description = description[:DESCRIPTION_MAX_CHARS].rstrip() + "..."
    actor_id = f"{item.get('username')}/{item.get('name')}"
    return "\n".join(
        [
            f"- {actor_id} — {item.get('title')}",
            f"  url: https://apify.com/{actor_id}",
            f"  pricing: {pricing} | users(30d): {stats.get('totalUsers30Days', '?')} | rating: {rating_text}",
            f"  {description}",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("query", help="Search keywords, e.g. 'google maps'")
    parser.add_argument(
        "--limit",
        type=int,
        default=DEFAULT_LIMIT,
        help="Max Actors to return (default: %(default)s)",
    )
    parser.add_argument("--json", action="store_true", help="Print the raw API `data` object")
    args = parser.parse_args()

    data = search(args.query, args.limit)
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return 0

    items = data.get("items", [])
    print(f"Store search '{args.query}': showing {len(items)} of {data.get('total', '?')} Actors")
    for item in items:
        print(format_item(item))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
