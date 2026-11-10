"""Query the official AI SDK docs search endpoint.

https://ai-sdk.dev/llms.txt documents this as the preferred discovery path:

    https://ai-sdk.dev/api/search-docs?q=your+query

The response is JSON `{ "query": "...", "results": [{url, title, description, score}, ...] }`.
This script URL-encodes the query, writes the raw JSON to output/temp/, and
prints a compact title/URL/description list. Fetch a result's body with
fetch_doc_page.py (append `.md` is handled there).

Usage:
    python search_docs.py ToolLoopAgent
    python search_docs.py "generating structured output"
    python search_docs.py prepareStep --max-results 5
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote_plus

import requests

SKILL_DIR = Path(__file__).resolve().parent
DEFAULT_OUTPUT_DIR = SKILL_DIR / "output" / "temp"
SEARCH_ENDPOINT = "https://ai-sdk.dev/api/search-docs?q="
REQUEST_TIMEOUT_SECONDS = 30
DEFAULT_MAX_RESULTS = 10


def slug_from_query(query: str) -> str:
    safe = "".join(ch if ch.isalnum() else "-" for ch in query.strip().lower())
    collapsed = "-".join(part for part in safe.split("-") if part)
    return (collapsed or "query")[:80]


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("query", help="Search string, e.g. ToolLoopAgent")
    parser.add_argument(
        "--max-results",
        type=int,
        default=DEFAULT_MAX_RESULTS,
        help="Maximum results to print (default: %(default)s). Full JSON is still written.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory to write the raw JSON to (default: %(default)s)",
    )
    args = parser.parse_args()

    url = SEARCH_ENDPOINT + quote_plus(args.query)
    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
    except requests.RequestException as exc:
        print(f"ERROR: failed to fetch {url}: {exc}", file=sys.stderr)
        return 1

    try:
        payload = response.json()
    except json.JSONDecodeError as exc:
        print(f"ERROR: search endpoint did not return JSON: {exc}", file=sys.stderr)
        return 1

    results = payload.get("results")
    if not isinstance(results, list):
        print("ERROR: unexpected search payload (missing results list)", file=sys.stderr)
        return 1

    args.output_dir.mkdir(parents=True, exist_ok=True)
    out_path = args.output_dir / f"search-{slug_from_query(args.query)}.json"
    fetched_at = datetime.now(timezone.utc).isoformat()
    out_path.write_text(
        json.dumps(
            {"fetched_at": fetched_at, "source": url, **payload}, indent=2, ensure_ascii=False
        )
        + "\n",
        encoding="utf-8",
    )

    shown = results[: args.max_results]
    print(f"Query: {payload.get('query', args.query)}")
    print(f"Wrote {out_path} ({len(results)} hits, showing {len(shown)})")
    print()
    for item in shown:
        title = item.get("title") or "(untitled)"
        item_url = item.get("url") or ""
        description = (item.get("description") or "").strip()
        print(f"- [{title}]({item_url})")
        if description:
            print(f"  {description}")
    if len(results) > len(shown):
        print(f"\n({len(results) - len(shown)} more in {out_path})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
