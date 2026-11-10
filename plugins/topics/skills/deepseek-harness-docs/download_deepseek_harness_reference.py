"""Download an English-only DeepSeek Harness llms.txt snapshot.

The upstream index has parallel ``## 简体中文`` and ``## English`` sections.
This script stores only the complete English section, beginning at its heading
and ending before the next level-two heading. It refuses to overwrite the
cache if the required heading is missing or ambiguous, preventing a malformed
upstream response from silently mixing languages into the skill's reference.

The output starts with source and fetched_at frontmatter. A snapshot fetched
within the last 24 hours is reused unless ``--force`` is supplied.
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

SKILL_DIR = Path(__file__).resolve().parent
SOURCE_URL = "https://deepseek-harness.github.io/deepseek-harness/llms.txt"
OUTPUT_PATH = SKILL_DIR / "output" / "llms.en.txt"
DEFAULT_FRESHNESS_DAYS = 1.0  # Documentation normally changes less often than daily.
REQUEST_TIMEOUT_SECONDS = 30  # Avoid hanging during skill startup on a dead host.
FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
ENGLISH_HEADING = "## English"


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


def fetch_source() -> str:
    try:
        response = requests.get(SOURCE_URL, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        return response.content.decode("utf-8")
    except (requests.RequestException, UnicodeDecodeError) as exc:
        print(f"ERROR: failed to fetch {SOURCE_URL}: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


def extract_english_section(source: str) -> str:
    lines = source.splitlines(keepends=True)
    matches = [index for index, line in enumerate(lines) if line.strip() == ENGLISH_HEADING]
    if len(matches) != 1:
        print(
            f"ERROR: expected exactly one {ENGLISH_HEADING!r} heading, found {len(matches)}.",
            file=sys.stderr,
        )
        raise SystemExit(1)

    start = matches[0]
    end = len(lines)
    for index in range(start + 1, len(lines)):
        if lines[index].startswith("## "):
            end = index
            break

    section = "".join(lines[start:end]).strip()
    if not section or not any(line.startswith("- [") for line in section.splitlines()):
        print("ERROR: the English section contains no documentation entries.", file=sys.stderr)
        raise SystemExit(1)
    return section + "\n"


def write_output(english_section: str) -> None:
    fetched_at = datetime.now(timezone.utc).isoformat()
    frontmatter = f"---\nsource: {SOURCE_URL}\nfetched_at: {fetched_at}\nlanguage: English\n---\n\n"
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(frontmatter + english_section, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--freshness-days",
        type=float,
        default=DEFAULT_FRESHNESS_DAYS,
        help="Reuse a snapshot younger than this many days (default: %(default)s).",
    )
    parser.add_argument(
        "--force", action="store_true", help="Download even when the cache is fresh."
    )
    args = parser.parse_args()

    if not args.force:
        fetched_at = read_fetched_at(OUTPUT_PATH)
        if fetched_at is not None:
            age = datetime.now(timezone.utc) - fetched_at
            if age < timedelta(days=args.freshness_days):
                print(
                    f"output/llms.en.txt: already fresh (fetched at {fetched_at.isoformat()}). "
                    "Use --force to refetch."
                )
                return 0

    write_output(extract_english_section(fetch_source()))
    print("Wrote output/llms.en.txt")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
