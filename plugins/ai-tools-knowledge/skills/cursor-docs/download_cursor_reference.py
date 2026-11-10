"""Download the Cursor docs index (llms.txt).

cursor.com/llms.txt is a hierarchical index of documentation page URLs
grouped under section headings (Get Started, Agent, Customizing, ...).
It has no descriptions per line and there is no llms-full.txt (it renders
the marketing homepage instead of a text dump) -- full page content must be
fetched per-URL with WebFetch. Each indexed URL already ends in `.md`
(e.g. https://cursor.com/docs/agent/overview.md), so WebFetch gets clean
markdown directly without needing to strip HTML chrome.

Standalone copy-and-adapt of ../../../claude-plugins/meta/skills/writing-skill-web/scripts/download_web_reference.py's
freshness-check contract (source + fetched_at frontmatter, 24h default
freshness window, --force to bypass).
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

SKILL_DIR = Path(__file__).resolve().parent
DEFAULT_URL = "https://cursor.com/llms.txt"
DEFAULT_OUTPUT = SKILL_DIR / "output" / "llms.txt"

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
