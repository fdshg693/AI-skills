"""Check the section markers used by the GAW llms-full.txt export."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

DEFAULT_LIMIT = 10


def scan(path: Path, marker_pattern: str, limit: int) -> list[tuple[int, str]]:
    marker_re = re.compile(marker_pattern)
    markers: list[tuple[int, str]] = []
    with path.open(encoding="utf-8", errors="replace") as file:
        for line_number, line in enumerate(file, start=1):
            text = line.rstrip("\n")
            if len(markers) < limit and marker_re.match(text):
                markers.append((line_number, text))
            if len(markers) >= limit:
                break
    return markers


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path)
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    parser.add_argument("--marker-pattern", default=r"^<!-- file: [^>]+ -->$")
    args = parser.parse_args()
    if not args.file.is_file():
        raise SystemExit(f"File not found: {args.file}")

    markers = scan(args.file, args.marker_pattern, args.limit)
    print(f"-- first {len(markers)} section markers --")
    for line_number, text in markers:
        print(f"{line_number:>8}: {text}")

    if markers:
        print("\nLooks consistent: extract_doc_section.py can be used with file names or raw URLs.")
    else:
        print("\nNo section markers found: inspect the raw file before extracting sections.")


if __name__ == "__main__":
    main()
