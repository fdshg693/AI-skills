"""Download and cache the official GitHub Agentic Workflows references.

The two official exports are fetched independently and written under output/
with source and fetched_at metadata. Fresh files are reused for 24 hours;
pass --force when a deliberate refresh is needed.
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BASE_URL = "https://github.github.com/gh-aw"
DEFAULT_REFERENCES = {
    "llms.txt": f"{BASE_URL}/llms.txt",
    "llms-full.txt": f"{BASE_URL}/llms-full.txt",
}
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent / "output"
DEFAULT_FRESHNESS_HOURS = 24.0
REQUEST_TIMEOUT_SECONDS = 30
USER_AGENT = "github-agentic-workflows-skill/1.0"
FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)


def read_fetched_at(path: Path) -> datetime | None:
    if not path.is_file():
        return None
    match = FRONTMATTER_RE.match(path.read_text(encoding="utf-8", errors="replace"))
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
    request = Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            return response.read().decode(charset, errors="replace")
    except HTTPError as exc:
        print(f"ERROR: failed to fetch {url}: HTTP {exc.code}", file=sys.stderr)
        raise SystemExit(1) from exc
    except (URLError, TimeoutError, OSError) as exc:
        print(f"ERROR: failed to fetch {url}: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


def write_output(path: Path, url: str, body: str) -> None:
    fetched_at = datetime.now(timezone.utc).isoformat()
    frontmatter = f"---\nsource: {url}\nfetched_at: {fetched_at}\n---\n\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(frontmatter + body, encoding="utf-8")


def is_fresh(path: Path, freshness_hours: float) -> bool:
    fetched_at = read_fetched_at(path)
    if fetched_at is None:
        return False
    age = datetime.now(timezone.utc) - fetched_at
    return age < timedelta(hours=freshness_hours)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument(
        "--freshness-hours",
        type=float,
        default=DEFAULT_FRESHNESS_HOURS,
        help="Reuse a snapshot younger than this many hours (default: %(default)s)",
    )
    parser.add_argument(
        "--force", action="store_true", help="Fetch all references even when cached files are fresh"
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.freshness_hours < 0:
        raise SystemExit("--freshness-hours must be non-negative")

    for filename, url in DEFAULT_REFERENCES.items():
        output = args.output_dir / filename
        if not args.force and is_fresh(output, args.freshness_hours):
            print(f"{output}: fresh; use --force to refresh")
            continue
        write_output(output, url, fetch(url))
        print(f"Wrote {output}")


if __name__ == "__main__":
    main()
