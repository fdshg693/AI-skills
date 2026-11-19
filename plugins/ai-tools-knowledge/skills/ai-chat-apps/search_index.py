"""Search the help-center indexes by keyword and print matching articles.

Every keyword must appear (case-insensitive) in the title, description,
section or URL slug unless ``--any`` is given.  A stale or missing index is
refreshed first (only for the sources being searched); if the refresh fails
the previous snapshot is searched and a warning is printed.
"""

from __future__ import annotations

import argparse
import re
import sys

import download_index as dl
import download_url_index as index

ENTRY_RE = re.compile(r"^- \[((?:[^\]\\]|\\.)+)\]\((https://[^)\s]+)\)(.*)$")


def read_index(source: dl.Source) -> list[tuple[str, str, str, str]]:
    """Return ``(section, title, url, rest)`` for each entry line."""

    entries: list[tuple[str, str, str, str]] = []
    section = ""
    for line in source.output.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            section = line[3:].strip()
            continue
        match = ENTRY_RE.match(line)
        if match:
            title = re.sub(r"\\(.)", r"\1", match.group(1))
            entries.append((section, title, match.group(2), match.group(3)))
    return entries


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "keywords", nargs="+", help="English keywords (help centers are indexed in English)"
    )
    parser.add_argument("--source", choices=[*dl.SOURCES, "all"], default="all")
    parser.add_argument("--any", action="store_true", help="Match any keyword instead of all")
    parser.add_argument("--limit", type=int, default=30)
    parser.add_argument(
        "--no-refresh", action="store_true", help="Never download; search the snapshot as is"
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    names = list(dl.SOURCES) if args.source == "all" else [args.source]
    keywords = [word.casefold() for word in args.keywords]
    match_fn = any if args.any else all
    total = 0
    for name in names:
        source = dl.SOURCES[name]
        if not args.no_refresh and not dl.is_fresh(source):
            dl.download(source)
        if not source.output.is_file():
            print(f"# {name}: index missing and could not be downloaded", file=sys.stderr)
            continue
        fetched_at = index.read_fetched_at(source.output)
        hits = [
            entry
            for entry in read_index(source)
            if match_fn(word in " ".join(entry).casefold() for word in keywords)
        ]
        stamp = fetched_at.date().isoformat() if fetched_at else "unknown"
        print(f"# {name} (index fetched {stamp}): {len(hits)} hit(s)")
        for section, title, url, rest in hits[: args.limit]:
            print(f"- [{section}] {title} <{url}>{rest}")
        if len(hits) > args.limit:
            print(f"  ... {len(hits) - args.limit} more; add keywords or raise --limit")
        total += len(hits)
    return 0 if total else 3


if __name__ == "__main__":
    raise SystemExit(main())
