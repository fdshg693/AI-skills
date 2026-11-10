"""Extract Cline documentation sections from output/llms-full.txt."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

SOURCE_RE = re.compile(r"^Source:\s*(\S+)\s*$")


def normalize(value: str) -> str:
    """Return a comparable docs path, accepting a slug or a full URL."""
    parsed = urlparse(value)
    path = parsed.path if parsed.scheme else value
    path = path.strip().strip("/")
    if path.endswith(".md"):
        path = path[:-3]
    return path


def find_sections(lines: list[str]) -> list[tuple[int, int, str, str]]:
    """Find H1 + nearby Source markers; body H1s without Source are ignored."""
    markers: list[tuple[int, str, str]] = []
    for index, line in enumerate(lines):
        if not line.startswith("# "):
            continue
        for candidate in lines[index + 1 : index + 5]:
            match = SOURCE_RE.match(candidate.rstrip("\r\n"))
            if match:
                markers.append((index, line[2:].strip(), match.group(1)))
                break

    sections: list[tuple[int, int, str, str]] = []
    for marker_index, (start, title, source) in enumerate(markers):
        end = markers[marker_index + 1][0] if marker_index + 1 < len(markers) else len(lines)
        sections.append((start, end, title, source))
    return sections


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("slugs", nargs="+", help="Cline docs slug(s) or full source URL(s).")
    parser.add_argument(
        "--input",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "output" / "llms-full.txt",
        help="Full snapshot to read.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "output" / "temp",
        help="Directory for extracted sections.",
    )
    args = parser.parse_args()

    if not args.input.is_file():
        print(f"ERROR: snapshot not found: {args.input}", file=sys.stderr)
        raise SystemExit(1)

    lines = args.input.read_text(encoding="utf-8").splitlines(keepends=True)
    sections = find_sections(lines)
    if not sections:
        print("ERROR: no '# Title' + nearby 'Source:' section markers found", file=sys.stderr)
        raise SystemExit(1)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    for requested in args.slugs:
        target = normalize(requested)
        match = next((section for section in sections if normalize(section[3]) == target), None)
        if match is None:
            print(f"ERROR: no section matched {requested}", file=sys.stderr)
            raise SystemExit(2)

        start, end, title, source = match
        filename = target.replace("/", "__") or "index"
        output_path = args.output_dir / f"{filename}.txt"
        output_path.write_text("".join(lines[start:end]), encoding="utf-8")
        print(f"{title}: {source}")
        print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
