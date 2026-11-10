"""Copy-and-adapt template for a static web reference snapshot (llms.txt-style).

Copy this file into a new skill's directory and adjust DEFAULT_URL /
DEFAULT_OUTPUT for that skill's target page (or just pass --url/--output).
Fetches a URL, records a YAML frontmatter block (source + fetched_at) on top
of the raw response body, and skips re-fetching if the existing file is
still fresh (default: within the last 24 hours) unless --force is given.

The vscode-docs / github-copilot-docs skills carry adapted copies of this
file. It is written as a standalone, copy-and-adapt script rather than an
importable shared module: a plain
`skills/plugins/*/skills/<name>/` skill directory has no shared
`scripts/` folder one level up to import from.

Usage:
    python download_web_reference.py --url https://example.com/llms.txt
    python download_web_reference.py --force
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

# Adjust these two when copying this file into a new skill.
DEFAULT_URL = "https://example.com/llms.txt"
DEFAULT_OUTPUT = Path(__file__).resolve().parent / "output" / "reference.md"

DEFAULT_FRESHNESS_DAYS = 1.0  # docs sites are rarely updated more often than daily
REQUEST_TIMEOUT_SECONDS = 30  # fail fast instead of hanging on a slow/dead host
FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)


def read_fetched_at(path: Path) -> datetime | None:
    if not path.is_file():
        return None
    match = FRONTMATTER_RE.match(path.read_text(encoding="utf-8"))
    if not match:
        return None
    for line in match.group(1).splitlines():
        key, _, value = line.partition(":")
        if key.strip() == "fetched_at":
            try:
                return datetime.fromisoformat(value.strip())
            except ValueError:
                return None
    return None


def fetch(url: str) -> str:
    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
    except requests.RequestException as exc:
        print(f"ERROR: failed to fetch {url}: {exc}", file=sys.stderr)
        raise SystemExit(1)
    return response.text


def write_output(path: Path, url: str, body: str) -> None:
    fetched_at = datetime.now(timezone.utc).isoformat()
    frontmatter = f"---\nsource: {url}\nfetched_at: {fetched_at}\n---\n\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(frontmatter + body, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default=DEFAULT_URL, help="Fetch target (default: %(default)s)")
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Output file path (default: %(default)s)",
    )
    parser.add_argument(
        "--freshness-days",
        type=float,
        default=DEFAULT_FRESHNESS_DAYS,
        help="Skip re-fetching if the cached file is younger than this many days (default: %(default)s)",
    )
    parser.add_argument(
        "--force", action="store_true", help="Re-fetch even if the cached file is still fresh"
    )
    args = parser.parse_args()

    if not args.force:
        fetched_at = read_fetched_at(args.output)
        if fetched_at is not None:
            age = datetime.now(timezone.utc) - fetched_at
            if age < timedelta(days=args.freshness_days):
                print(
                    f"{args.output}: already fresh (fetched at {fetched_at.isoformat()}). Use --force to refetch."
                )
                return

    body = fetch(args.url)
    write_output(args.output, args.url, body)
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
