"""Download the Ona (ona.com) llms.txt / llms-full.txt snapshots.

ona.com publishes two independent pairs of these files:

- https://ona.com/llms.txt + /llms-full.txt: marketing/company content
  (leadership, history, customers, use cases, comparisons, blog, guides).
  Both files are already prose (not a bare link index) and carry no
  per-page `# Title` / `Source: URL` markers -- they are meant to be read
  or grepped directly.
- https://ona.com/docs/llms.txt + /docs/llms-full.txt: technical
  documentation. docs/llms.txt is a flat link index (~500 entries).
  docs/llms-full.txt is a large full-text dump that DOES follow the
  repeating `# Title` / `Source: URL` section-marker pattern, so
  extract_doc_section.py can pull one page at a time instead of grepping
  the whole file.

Output files are written to output/, split by source: the company/marketing
pair under output/company/, the docs pair under output/docs/ -- both source
sites happen to name their files llms.txt/llms-full.txt, so the subdirectory
is what keeps the two pairs from colliding. Each file carries a YAML
frontmatter block recording its source URL and fetch time. On rerun, a file
is skipped (not re-downloaded) if it was fetched within the last 24 hours;
pass --force to overwrite regardless of age.

Usage:
    python download_ona_reference.py
    python download_ona_reference.py --force
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

TARGETS = [
    ("https://ona.com/llms.txt", OUTPUT_DIR / "company" / "llms.txt"),
    ("https://ona.com/llms-full.txt", OUTPUT_DIR / "company" / "llms-full.txt"),
    ("https://ona.com/docs/llms.txt", OUTPUT_DIR / "docs" / "llms.txt"),
    ("https://ona.com/docs/llms-full.txt", OUTPUT_DIR / "docs" / "llms-full.txt"),
]

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
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for url, path in TARGETS:
        if not args.force:
            fetched_at = read_fetched_at(path)
            if fetched_at is not None:
                age = datetime.now(timezone.utc) - fetched_at
                if age < timedelta(days=args.freshness_days):
                    print(
                        f"{path.relative_to(SKILL_DIR)}: already fresh (fetched at {fetched_at.isoformat()}). Use --force to refetch."
                    )
                    continue

        body = fetch(url)
        write_output(path, url, body)
        print(f"Wrote {path.relative_to(SKILL_DIR)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
