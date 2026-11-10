"""Copy-and-adapt template: grep an llms-full.txt-style dump and report,
for every matching line, which page (# Title / Source: URL) it belongs to.

A plain Grep over llms-full.txt only tells you the matching line and its
line number -- not which URL that line came from, because the file
concatenates many pages with no per-line source marker. This script walks
the file tracking the most recent (# Title / Source: URL) heading pair seen
so far, and attaches it to every match.

Only use this template after confirming the target file actually follows
the repeating (# Title / Source: URL) pattern -- run
inspect_section_markers.py on the downloaded file first and check its
verdict. The heading-detection heuristic here is the same as
inspect_section_markers.py / extract_doc_section.py: a heading line only
counts if a source line follows within MAX_PAIR_GAP_LINES, so stray lines
in body text that happen to start with "# " (e.g. code-sample headings)
don't get misdetected as a new section.

Copy this file into the new skill's directory and adjust DEFAULT_INPUT
(or pass --input instead of editing the default).

Usage:
    python grep_doc_sections.py "some search pattern"
    python grep_doc_sections.py "some search pattern" --input output/llms-full.txt
    python grep_doc_sections.py "ERROR_CODE_\\d+" --ignore-case --max-matches 50
    python grep_doc_sections.py "exact literal string" --fixed-strings
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

DEFAULT_INPUT = Path(__file__).resolve().parent / "output" / "llms-full.txt"
DEFAULT_H1_PATTERN = r"^# (?P<title>.+)$"
DEFAULT_SOURCE_PATTERN = r"^Source:\s*(?P<url>\S+)$"
MAX_PAIR_GAP_LINES = 3  # keep in sync with inspect_section_markers.py
DEFAULT_MAX_MATCHES = 200


def find_current_section(
    lines: list[str], index: int, h1_re: re.Pattern, source_re: re.Pattern
) -> tuple[str, str] | None:
    """If lines[index] is a heading immediately (within MAX_PAIR_GAP_LINES)
    followed by a source line, return (title, url); otherwise None."""
    h1_match = h1_re.match(lines[index])
    if not h1_match:
        return None
    for j in range(index + 1, min(index + 1 + MAX_PAIR_GAP_LINES, len(lines))):
        source_match = source_re.match(lines[j])
        if source_match:
            return h1_match.group("title").strip(), source_match.group("url").strip()
    return None


def scan(
    path: Path,
    pattern_re: re.Pattern,
    h1_re: re.Pattern,
    source_re: re.Pattern,
    max_matches: int,
) -> tuple[list[tuple[int, str, str | None, str | None]], int]:
    """Returns (matches, total_match_count_before_truncation).

    Each match is (lineno, line_text, current_title_or_None, current_url_or_None).
    """
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()

    current_title: str | None = None
    current_url: str | None = None
    matches: list[tuple[int, str, str | None, str | None]] = []
    total = 0

    for i, line in enumerate(lines):
        section = find_current_section(lines, i, h1_re, source_re)
        if section is not None:
            current_title, current_url = section

        if pattern_re.search(line):
            total += 1
            if len(matches) < max_matches:
                matches.append((i + 1, line, current_title, current_url))

    return matches, total


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("pattern", help="Search pattern (regex by default; see --fixed-strings)")
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help="llms-full.txt-style file to search (default: %(default)s)",
    )
    parser.add_argument("-i", "--ignore-case", action="store_true", help="Case-insensitive match")
    parser.add_argument(
        "-F",
        "--fixed-strings",
        action="store_true",
        help="Treat pattern as a literal string, not a regex",
    )
    parser.add_argument(
        "--max-matches",
        type=int,
        default=DEFAULT_MAX_MATCHES,
        help="Stop collecting after this many matches (default: %(default)s)",
    )
    parser.add_argument(
        "--h1-pattern",
        default=DEFAULT_H1_PATTERN,
        help="Regex for the heading marker line; must have a 'title' group (default: %(default)r)",
    )
    parser.add_argument(
        "--source-pattern",
        default=DEFAULT_SOURCE_PATTERN,
        help="Regex for the source-URL marker line; must have a 'url' group (default: %(default)r)",
    )
    args = parser.parse_args()

    if not args.input.is_file():
        raise SystemExit(f"Input file not found: {args.input}")

    flags = re.IGNORECASE if args.ignore_case else 0
    pattern_text = re.escape(args.pattern) if args.fixed_strings else args.pattern
    try:
        pattern_re = re.compile(pattern_text, flags)
    except re.error as exc:
        raise SystemExit(
            f"Invalid --pattern regex: {exc} (use --fixed-strings for a literal search)"
        )

    h1_re = re.compile(args.h1_pattern)
    source_re = re.compile(args.source_pattern)

    matches, total = scan(args.input, pattern_re, h1_re, source_re, args.max_matches)

    if not matches:
        print(f"No matches for {args.pattern!r} in {args.input}")
        return 1

    current_url_group: str | None = "__unset__"
    for lineno, text, title, url in matches:
        if url != current_url_group:
            current_url_group = url
            print()
            if url is None:
                print("== (no Source seen yet at this point in the file) ==")
            else:
                print(f"== {url} ({title}) ==")
        print(f"{lineno:>8}: {text}")

    print()
    print(
        f"{len(matches)} match(es) shown"
        + ("" if total == len(matches) else f" ({total} total; increase --max-matches for more)")
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
