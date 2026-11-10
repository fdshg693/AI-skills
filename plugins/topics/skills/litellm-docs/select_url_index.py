"""Select a bounded URL manifest from a normalized URL-index Markdown file."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_INPUT = Path(__file__).resolve().parent / "output" / "docs-urls.md"
DEFAULT_OUTPUT = Path(__file__).resolve().parent / "output" / "selection.json"
ENTRY_RE = re.compile(r"^\s*- \[([^]]+)\]\((https://[^)\s]+)\)(?::\s*(.*))?\s*$")
FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)


def read_entries(path: Path) -> list[dict[str, str]]:
    """Read the deterministic ``- [title](url): description`` entry schema."""

    entries: list[dict[str, str]] = []
    seen: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        match = ENTRY_RE.match(line)
        if not match:
            continue
        title, url, description = match.groups()
        if url in seen:
            continue
        seen.add(url)
        entries.append({"url": url, "title": title, "description": description or ""})
    return entries


def _matches_prefix(url: str, prefixes: list[str]) -> bool:
    return not prefixes or any(url.startswith(prefix) for prefix in prefixes)


def select_entries(
    entries: list[dict[str, str]],
    include_prefixes: list[str] | None = None,
    exclude_prefixes: list[str] | None = None,
    keywords: list[str] | None = None,
    exclude_keywords: list[str] | None = None,
    limit: int | None = None,
) -> list[dict[str, str]]:
    include_prefixes = include_prefixes or []
    exclude_prefixes = exclude_prefixes or []
    keywords = [value.casefold() for value in (keywords or [])]
    exclude_keywords = [value.casefold() for value in (exclude_keywords or [])]
    selected: list[dict[str, str]] = []
    for entry in entries:
        url = entry["url"]
        haystack = " ".join(entry.values()).casefold()
        if not _matches_prefix(url, include_prefixes):
            continue
        if any(url.startswith(prefix) for prefix in exclude_prefixes):
            continue
        if keywords and not any(keyword in haystack for keyword in keywords):
            continue
        if exclude_keywords and any(keyword in haystack for keyword in exclude_keywords):
            continue
        selected.append(dict(entry))
        if limit is not None and len(selected) >= limit:
            break
    return selected


def write_manifest(
    path: Path,
    source: Path,
    entries: list[dict[str, str]],
    filters: dict[str, object],
) -> None:
    payload = {
        "schema": "url-selection-manifest/v1",
        "source": str(source),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "filters": filters,
        "entries": entries,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="Normalized URL list")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Manifest JSON output")
    parser.add_argument("--include-prefix", action="append", default=[])
    parser.add_argument("--exclude-prefix", action="append", default=[])
    parser.add_argument(
        "--keyword", action="append", default=[], help="Case-insensitive keyword (repeatable)"
    )
    parser.add_argument("--exclude-keyword", action="append", default=[])
    parser.add_argument("--limit", type=int, default=None, help="Maximum selected entries")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if not args.input.is_file():
        print(f"ERROR: input file not found: {args.input}", file=sys.stderr)
        return 2
    if args.limit is not None and args.limit < 1:
        print("ERROR: --limit must be positive", file=sys.stderr)
        return 2
    entries = read_entries(args.input)
    filters = {
        "include_prefixes": args.include_prefix,
        "exclude_prefixes": args.exclude_prefix,
        "keywords": args.keyword,
        "exclude_keywords": args.exclude_keyword,
        "limit": args.limit,
    }
    selected = select_entries(
        entries,
        **{
            "include_prefixes": args.include_prefix,
            "exclude_prefixes": args.exclude_prefix,
            "keywords": args.keyword,
            "exclude_keywords": args.exclude_keyword,
            "limit": args.limit,
        },
    )
    write_manifest(args.output, args.input, selected, filters)
    print(f"Wrote {args.output} ({len(selected)} URLs)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
