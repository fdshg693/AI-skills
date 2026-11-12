"""Download the Linear documentation index snapshot used by this skill.

https://linear.app/llms.txt is the site-wide agent index. It has three sections:

- `## Website`: marketing / about / careers pages (~50). Normally not used.
- `## Documentation`: the user docs (~105 pages under /docs/, grouped by `###`
  categories such as Getting started, Planning, Issues and cycles, Integrations).
- `## Developers`: the developer docs (~26 pages under /developers/: GraphQL,
  pagination, filtering, rate limiting, webhooks, OAuth, agents, SDK).

Every link is already a `https://linear.app/...md` URL, which returns the page
as Markdown (see fetch_doc_page.py).

Not fetched, on purpose:
- /docs/llms.txt, /developers/llms.txt and their -full variants return 404.
- https://linear.app/llms-full.txt returns HTTP 200, but the body is the SPA's
  HTML fallback, not a dump. A status code alone is therefore NOT proof that a
  file exists; this script checks the Content-Type and the first line.
- sitemap.xml lists the same pages without titles or categories.

Output is written to output/llms.txt next to this script, with a YAML
frontmatter block recording its source URL and fetch time. On rerun, the file
is skipped if it was fetched within the last 24 hours; pass --force to
overwrite regardless of age.

Usage:
    python download_linear_reference.py
    python download_linear_reference.py --force
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

INDEX_URL = "https://linear.app/llms.txt"
INDEX_FILENAME = "llms.txt"
EXPECTED_FIRST_LINE = "# Linear"

DEFAULT_FRESHNESS_DAYS = 1.0
REQUEST_TIMEOUT_SECONDS = 60
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


def fetch_index(url: str) -> str:
    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
    except requests.RequestException as exc:
        print(f"ERROR: failed to fetch {url}: {exc}", file=sys.stderr)
        raise SystemExit(1)

    content_type = response.headers.get("Content-Type", "")
    response.encoding = response.encoding or "utf-8"
    body = response.text
    first_line = body.lstrip(chr(0xFEFF)).lstrip().splitlines()[0] if body.strip() else ""
    if "text/plain" not in content_type or first_line.strip() != EXPECTED_FIRST_LINE:
        print(
            f"ERROR: {url} did not return the expected llms.txt "
            f"(Content-Type={content_type!r}, first line={first_line[:80]!r}). "
            "The site may have served an HTML fallback; keeping the existing snapshot.",
            file=sys.stderr,
        )
        raise SystemExit(1)
    return body


def write_output(path: Path, url: str, body: str) -> None:
    fetched_at = datetime.now(timezone.utc).isoformat()
    frontmatter = f"---\nsource: {url}\nfetched_at: {fetched_at}\n---\n\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(frontmatter + body, encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--freshness-days",
        type=float,
        default=DEFAULT_FRESHNESS_DAYS,
        help="Skip re-fetching if the snapshot is younger than this many days (default: %(default)s)",
    )
    parser.add_argument(
        "--force", action="store_true", help="Re-fetch even if the snapshot is still fresh"
    )
    args = parser.parse_args()

    path = OUTPUT_DIR / INDEX_FILENAME
    if not args.force:
        fetched_at = read_fetched_at(path)
        if fetched_at is not None:
            age = datetime.now(timezone.utc) - fetched_at
            if age < timedelta(days=args.freshness_days):
                print(
                    f"{INDEX_FILENAME}: already fresh (fetched at {fetched_at.isoformat()}). Use --force to refetch."
                )
                return 0

    body = fetch_index(INDEX_URL)
    write_output(path, INDEX_URL, body)
    print(f"Wrote {path.relative_to(SKILL_DIR)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
