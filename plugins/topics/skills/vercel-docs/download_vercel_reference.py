"""Download the Vercel documentation snapshot used by this skill.

https://vercel.com/docs publishes an agent-oriented set of machine-readable
resources:

- docs/llms.txt: a short routing index (CLI / MCP / API / main indexes), ~50 lines.
- docs/products.md: a curated list of every Vercel product, ~50 lines.
- docs/sitemap.md: the full semantic index of documentation pages
  (`- [Title](/docs/...) | Type | Lastmod | Summary | Prerequisites | Topics`),
  ~1300 entries / ~400 KB. Grep it instead of reading it whole.
- docs/taxonomy.json: canonical product names, aliases, and deprecations.
- docs/llms-full.txt: a ~9.6 MB concatenated dump of all docs plus the REST API
  reference. NOT fetched by default; pass --include-full when the fallback grep
  in SKILL.md is needed. Its page boundaries use `-----`-fenced metadata
  (`title:` / `source:`) BEFORE the `# Title` heading, so it is NOT the
  (`# Title` / `Source: URL`) layout that extract_doc_section.py expects.

Output files are written to output/ next to this script, each with a YAML
frontmatter block recording its source URL and fetch time. On rerun, a file is
skipped (not re-downloaded) if it was fetched within the last 24 hours; pass
--force to overwrite regardless of age.

Usage:
    python download_vercel_reference.py
    python download_vercel_reference.py --force
    python download_vercel_reference.py --include-full
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

SKILL_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = SKILL_DIR / "output"

# Fetched at every skill start.
TARGETS = [
    ("https://vercel.com/docs/llms.txt", "llms.txt"),
    ("https://vercel.com/docs/products.md", "products.md"),
    ("https://vercel.com/docs/sitemap.md", "sitemap.md"),
    ("https://vercel.com/docs/taxonomy.json", "taxonomy.json"),
]

# Large (several MB) and only a fallback; fetched on demand with --include-full.
FULL_TARGET = ("https://vercel.com/docs/llms-full.txt", "llms-full.txt")

DEFAULT_FRESHNESS_DAYS = 1.0  # docs sites are rarely updated more often than daily
# llms-full.txt is a multi-megabyte dump; give the small indexes a shorter leash
# but allow the full dump enough time to finish on a slow connection.
REQUEST_TIMEOUT_SECONDS = 60
FULL_REQUEST_TIMEOUT_SECONDS = 180
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


def fetch(url: str, timeout: float) -> str:
    try:
        response = requests.get(url, timeout=timeout)
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--freshness-days",
        type=float,
        default=DEFAULT_FRESHNESS_DAYS,
        help="Skip re-fetching a file if it is younger than this many days (default: %(default)s)",
    )
    parser.add_argument(
        "--force", action="store_true", help="Re-fetch even if a cached file is still fresh"
    )
    parser.add_argument(
        "--include-full",
        action="store_true",
        help="Also fetch the ~9.6 MB llms-full.txt dump (skipped by default; only a grep fallback)",
    )
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    targets = list(TARGETS)
    if args.include_full:
        targets.append(FULL_TARGET)

    for url, filename in targets:
        path = OUTPUT_DIR / filename
        if not args.force:
            fetched_at = read_fetched_at(path)
            if fetched_at is not None:
                age = datetime.now(timezone.utc) - fetched_at
                if age < timedelta(days=args.freshness_days):
                    print(
                        f"{filename}: already fresh (fetched at {fetched_at.isoformat()}). Use --force to refetch."
                    )
                    continue

        timeout = (
            FULL_REQUEST_TIMEOUT_SECONDS if filename == FULL_TARGET[1] else REQUEST_TIMEOUT_SECONDS
        )
        body = fetch(url, timeout)
        write_output(path, url, body)
        print(f"Wrote {path.relative_to(SKILL_DIR)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
