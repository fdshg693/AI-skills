"""Download Cline's llms.txt and llms-full.txt with a 24-hour cache."""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

DOCS_BASE = "https://docs.cline.bot"
TARGETS = {
    "llms.txt": f"{DOCS_BASE}/llms.txt",
    "llms-full.txt": f"{DOCS_BASE}/llms-full.txt",
}
FRESHNESS = timedelta(days=1)
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


def fetch(url: str) -> str:
    try:
        response = requests.get(
            url,
            timeout=REQUEST_TIMEOUT_SECONDS,
            headers={"User-Agent": "cline-docs-skill/1.0"},
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        print(f"ERROR: failed to fetch {url}: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    return response.text


def write_snapshot(path: Path, url: str, body: str) -> None:
    fetched_at = datetime.now(timezone.utc).isoformat()
    frontmatter = f"---\nsource: {url}\nfetched_at: {fetched_at}\n---\n\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(frontmatter + body, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--force", action="store_true", help="Re-download both files regardless of cache age."
    )
    parser.add_argument(
        "--freshness-days",
        type=float,
        default=1.0,
        help="Reuse snapshots younger than this many days (default: %(default)s).",
    )
    args = parser.parse_args()

    skill_dir = Path(__file__).resolve().parents[1]
    output_dir = skill_dir / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    freshness = timedelta(days=args.freshness_days)

    for filename, url in TARGETS.items():
        output_path = output_dir / filename
        if not args.force:
            fetched_at = read_fetched_at(output_path)
            if fetched_at is not None and datetime.now(timezone.utc) - fetched_at < freshness:
                print(f"{output_path}: fresh snapshot at {fetched_at.isoformat()}")
                continue

        write_snapshot(output_path, url, fetch(url))
        print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
