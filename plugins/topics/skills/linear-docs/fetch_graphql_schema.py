"""Fetch the Linear GraphQL schema (SDL) for grepping type and field names.

The public schema lives in the linear/linear repository (default branch
`master`) at packages/sdk/src/schema.graphql. It is ~1.4 MB / ~55k lines and
is updated almost weekly, so it is NOT committed: it is written to
output/temp/schema.graphql (gitignored) and refreshed when older than 24 hours.

Grep the file for `type Issue `, `input IssueCreateInput`, a field name, etc.
Never read it whole.

Usage:
    python fetch_graphql_schema.py
    python fetch_graphql_schema.py --force
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

SKILL_DIR = Path(__file__).resolve().parent
SCHEMA_URL = (
    "https://raw.githubusercontent.com/linear/linear/master/packages/sdk/src/schema.graphql"
)
OUTPUT_PATH = SKILL_DIR / "output" / "temp" / "schema.graphql"

DEFAULT_FRESHNESS_DAYS = 1.0
REQUEST_TIMEOUT_SECONDS = 120
# A GraphQL SDL file has no frontmatter, so the fetch time is kept in the file's
# first line as a comment (`#` is a comment in SDL and keeps the file valid).
STAMP_PREFIX = "# fetched_at: "


def read_fetched_at(path: Path) -> datetime | None:
    if not path.is_file():
        return None
    with path.open(encoding="utf-8") as f:
        first = f.readline().strip()
    if not first.startswith(STAMP_PREFIX):
        return None
    try:
        return datetime.fromisoformat(first[len(STAMP_PREFIX) :].strip())
    except ValueError:
        return None


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--freshness-days",
        type=float,
        default=DEFAULT_FRESHNESS_DAYS,
        help="Skip re-fetching if the cached schema is younger than this many days (default: %(default)s)",
    )
    parser.add_argument(
        "--force", action="store_true", help="Re-fetch even if the cached schema is still fresh"
    )
    args = parser.parse_args()

    if not args.force:
        fetched_at = read_fetched_at(OUTPUT_PATH)
        if fetched_at is not None:
            age = datetime.now(timezone.utc) - fetched_at
            if age < timedelta(days=args.freshness_days):
                print(
                    f"{OUTPUT_PATH}: already fresh (fetched at {fetched_at.isoformat()}). Use --force to refetch."
                )
                return 0

    try:
        response = requests.get(SCHEMA_URL, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
    except requests.RequestException as exc:
        print(f"ERROR: failed to fetch {SCHEMA_URL}: {exc}", file=sys.stderr)
        return 1
    response.encoding = "utf-8"
    body = response.text
    if "type Query" not in body:
        print(f"ERROR: {SCHEMA_URL} does not look like a GraphQL schema.", file=sys.stderr)
        return 1

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fetched_at = datetime.now(timezone.utc).isoformat()
    OUTPUT_PATH.write_text(
        f"{STAMP_PREFIX}{fetched_at}\n# source: {SCHEMA_URL}\n{body}",
        encoding="utf-8",
        newline="\n",
    )
    print(f"Wrote {OUTPUT_PATH} ({len(body.splitlines())} lines)\nSource: {SCHEMA_URL}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
