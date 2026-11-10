"""Sample the first N heading/source marker lines in a llms-full.txt-style file.

Many llms-full.txt-style docs dumps concatenate per-page sections as:

    # <Title>
    Source: <URL>

    <body>
    # <Title>
    Source: <URL>
    ...

Before writing a per-URL section-extraction script (see extract_doc_section.py
in this directory), sample the first few marker lines to confirm the file
actually follows this repeating (heading, source) pattern -- and that every
heading is immediately followed by a source line (rather than the heading
pattern also matching unrelated in-body headings, which would break a naive
extraction regex).

Usage:
    python inspect_section_markers.py path/to/llms-full.txt
    python inspect_section_markers.py path/to/llms-full.txt --limit 20
    python inspect_section_markers.py path/to/llms-full.txt --h1-pattern "^## " --source-pattern "^URL:"
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

DEFAULT_LIMIT = 10
DEFAULT_H1_PATTERN = r"^# .+"
DEFAULT_SOURCE_PATTERN = r"^Source:\s*\S+"
MAX_PAIR_GAP_LINES = 3  # a source line should follow its heading within a few lines


def scan(
    path: Path, h1_pattern: str, source_pattern: str, limit: int
) -> tuple[list[tuple[int, str]], list[tuple[int, str]]]:
    h1_re = re.compile(h1_pattern)
    source_re = re.compile(source_pattern)

    h1_hits: list[tuple[int, str]] = []
    source_hits: list[tuple[int, str]] = []

    with path.open(encoding="utf-8", errors="replace") as f:
        for lineno, line in enumerate(f, start=1):
            stripped = line.rstrip("\n")
            if len(h1_hits) < limit and h1_re.match(stripped):
                h1_hits.append((lineno, stripped))
            if len(source_hits) < limit and source_re.match(stripped):
                source_hits.append((lineno, stripped))
            if len(h1_hits) >= limit and len(source_hits) >= limit:
                break

    return h1_hits, source_hits


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("file", type=Path, help="Path to the downloaded llms-full.txt-style file")
    parser.add_argument(
        "--limit",
        type=int,
        default=DEFAULT_LIMIT,
        help="Number of marker lines to show per pattern (default: %(default)s)",
    )
    parser.add_argument(
        "--h1-pattern",
        default=DEFAULT_H1_PATTERN,
        help="Regex for the heading marker line (default: %(default)r)",
    )
    parser.add_argument(
        "--source-pattern",
        default=DEFAULT_SOURCE_PATTERN,
        help="Regex for the source-URL marker line (default: %(default)r)",
    )
    args = parser.parse_args()

    if not args.file.is_file():
        raise SystemExit(f"File not found: {args.file}")

    h1_hits, source_hits = scan(args.file, args.h1_pattern, args.source_pattern, args.limit)

    print(f"-- first {len(h1_hits)} lines matching heading pattern {args.h1_pattern!r} --")
    for lineno, text in h1_hits:
        print(f"{lineno:>8}: {text}")

    print()
    print(f"-- first {len(source_hits)} lines matching source pattern {args.source_pattern!r} --")
    for lineno, text in source_hits:
        print(f"{lineno:>8}: {text}")

    print()
    pair_gaps = [
        b - a for (a, _), (b, _) in zip(h1_hits, source_hits) if 0 < b - a <= MAX_PAIR_GAP_LINES
    ]
    consistent = bool(h1_hits) and len(pair_gaps) == len(h1_hits) == len(source_hits)

    if consistent:
        print(
            "Looks consistent: every sampled heading is followed by a source line within "
            f"{MAX_PAIR_GAP_LINES} lines -- the (# Title / Source: URL) pair pattern likely "
            "holds across the file. Copy extract_doc_section.py and adjust "
            "DEFAULT_INPUT/DEFAULT_BASE_URL for this site."
        )
    else:
        print(
            "Inconsistent pairing detected (counts differ or a heading isn't followed by a "
            "source line nearby) -- inspect the raw file manually before assuming the "
            "(# Title / Source: URL) pattern holds uniformly. The heading pattern may be "
            "matching unrelated in-body headings, or the source marker keyword may differ."
        )


if __name__ == "__main__":
    main()
