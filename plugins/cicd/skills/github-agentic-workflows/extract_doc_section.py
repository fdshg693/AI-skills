"""Extract one official GAW prompt/reference section by file name or URL."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

DEFAULT_INPUT = Path(__file__).resolve().parent / "output" / "llms-full.txt"
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent / "output" / "sections"
SECTION_RE = re.compile(
    r"^<!-- file: (?P<file>[^>]+) -->\n\n(?P<body>.*?)(?=\n<!-- file: [^>]+ -->\n|\Z)",
    re.DOTALL | re.MULTILINE,
)


def parse_sections(text: str) -> dict[str, str]:
    return {
        match.group("file").strip(): match.group("body").strip()
        for match in SECTION_RE.finditer(text)
    }


def resolve_file(value: str) -> str:
    marker = value.rstrip("/").split("/")[-1]
    return marker if marker.endswith(".md") else f"{marker}.md"


def safe_name(file_name: str) -> str:
    return file_name.replace("/", "__").replace(".", "_")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "urls", nargs="+", help="Raw source URL(s) or file names from llms-full.txt"
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()
    if not args.input.is_file():
        raise SystemExit(f"Input file not found: {args.input}")

    sections = parse_sections(args.input.read_text(encoding="utf-8", errors="replace"))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for raw_value in args.urls:
        file_name = resolve_file(raw_value)
        section = sections.get(file_name)
        if section is None:
            print(f"Not found: {file_name}")
            continue
        source_url = f"https://raw.githubusercontent.com/github/gh-aw/main/.github/aw/{file_name}"
        output = args.output_dir / f"{safe_name(file_name)}"
        output.write_text(
            f"<!-- file: {file_name} -->\nSource: {source_url}\n\n{section}\n", encoding="utf-8"
        )
        print(f"Wrote {output}")


if __name__ == "__main__":
    main()
