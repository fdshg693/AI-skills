"""Download the VS Code docs index (llms.txt).

Note: unlike code.claude.com, code.visualstudio.com does not publish an
llms-full.txt (it 404s) -- llms.txt is only an index of page URLs with short
descriptions. Full page content must be fetched per-URL with WebFetch.

Standalone copy of the writing-skill-web template
(skills/plugins/cc-knowledge/skills/writing-skill-web/scripts/download_web_reference.py):
writes a YAML frontmatter block (source + fetched_at) on top of the raw body
and skips re-fetching while the cached file is fresh unless --force is given.
Uses only the standard library so it runs with a plain `python`.
"""

from __future__ import annotations

import argparse
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

DEFAULT_URL = "https://code.visualstudio.com/llms.txt"
DEFAULT_OUTPUT = Path(__file__).resolve().parent / "output" / "llms.txt"

DEFAULT_FRESHNESS_DAYS = 1.0
REQUEST_TIMEOUT_SECONDS = 30
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
        with urllib.request.urlopen(url, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            return response.read().decode("utf-8")
    except (urllib.error.URLError, TimeoutError) as exc:
        print(f"ERROR: failed to fetch {url}: {exc}", file=sys.stderr)
        raise SystemExit(1)


def write_output(path: Path, url: str, body: str) -> None:
    fetched_at = datetime.now(timezone.utc).isoformat()
    frontmatter = f"---\nsource: {url}\nfetched_at: {fetched_at}\n---\n\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(frontmatter + body, encoding="utf-8", newline="\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default=DEFAULT_URL, help="Fetch target (default: %(default)s)")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Output file path")
    parser.add_argument(
        "--freshness-days",
        type=float,
        default=DEFAULT_FRESHNESS_DAYS,
        help="Skip re-fetching if the cached file is younger than this many days",
    )
    parser.add_argument("--force", action="store_true", help="Re-fetch even if still fresh")
    args = parser.parse_args()

    if not args.force:
        fetched_at = read_fetched_at(args.output)
        if fetched_at is not None:
            age = datetime.now(timezone.utc) - fetched_at
            if age < timedelta(days=args.freshness_days):
                print(f"{args.output}: already fresh (fetched at {fetched_at.isoformat()}).")
                return

    body = fetch(args.url)
    write_output(args.output, args.url, body)
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
