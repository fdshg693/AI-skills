"""Extract sections from output/llms-full.txt by title.

Codex llms-full.txt is a concatenated Markdown file whose page sections are
identified by top-level "# Title" headings. Use output/llms.txt to resolve a
URL or slug to the page title, then extract the matching title from
llms-full.txt.
"""

from __future__ import annotations

import argparse
import difflib
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

SKILL_DIR = Path(__file__).resolve().parent
INDEX_FILE = SKILL_DIR / "output" / "llms.txt"
FULL_FILE = SKILL_DIR / "output" / "llms-full.txt"
OUTPUT_DIR = SKILL_DIR / "output" / "temp"

BASE_URL = "https://developers.openai.com/codex/"
FRONTMATTER_RE = re.compile(r"\A---\n.*?\n---\n\n?", re.DOTALL)
INDEX_ENTRY_RE = re.compile(
    r"^- \[(?P<title>[^\]]+)\]\((?P<url>https://developers\.openai\.com/codex/[^)]+)\):?\s*(?P<desc>.*)$",
    re.MULTILINE,
)
SECTION_RE = re.compile(
    r"^# (?P<title>[^\n]+)\n(?P<body>.*?)(?=^# [^\n]+\n|\Z)",
    re.DOTALL | re.MULTILINE,
)


@dataclass(frozen=True)
class IndexEntry:
    title: str
    url: str
    slug: str


@dataclass(frozen=True)
class Section:
    title: str
    body: str


def strip_frontmatter(text: str) -> str:
    return FRONTMATTER_RE.sub("", text, count=1)


def normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def slug_from_url(url: str) -> str:
    path = urlparse(url).path
    if path.startswith("/codex/"):
        path = path[len("/codex/") :]
    if path.endswith(".md"):
        path = path[:-3]
    return path.strip("/")


def filename_part(value: str) -> str:
    value = slug_from_url(value) if value.startswith(("http://", "https://")) else value
    value = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip("/ "))
    value = re.sub(r"-+", "-", value).strip("-")
    return value or "section"


def read_index() -> list[IndexEntry]:
    if not INDEX_FILE.is_file():
        raise SystemExit(f"Index file not found: {INDEX_FILE}")

    text = strip_frontmatter(INDEX_FILE.read_text(encoding="utf-8"))
    entries: list[IndexEntry] = []
    for match in INDEX_ENTRY_RE.finditer(text):
        url = match.group("url").strip()
        entries.append(
            IndexEntry(
                title=match.group("title").strip(),
                url=url,
                slug=slug_from_url(url),
            )
        )
    return entries


def read_sections() -> list[Section]:
    if not FULL_FILE.is_file():
        raise SystemExit(f"Full documentation file not found: {FULL_FILE}")

    text = strip_frontmatter(FULL_FILE.read_text(encoding="utf-8"))
    return [
        Section(title=match.group("title").strip(), body=match.group("body").strip())
        for match in SECTION_RE.finditer(text)
    ]


def resolve_title(raw: str, entries: list[IndexEntry]) -> tuple[str, str | None]:
    raw = raw.strip()
    raw_slug = slug_from_url(raw) if raw.startswith(("http://", "https://")) else raw.strip("/")
    raw_norm = normalize(raw)
    raw_slug_norm = normalize(raw_slug)

    for entry in entries:
        if raw == entry.url or raw_slug == entry.slug:
            return entry.title, entry.url

    for entry in entries:
        if raw_norm == normalize(entry.title) or raw_slug_norm == normalize(entry.slug):
            return entry.title, entry.url

    return raw, None


def find_section(title: str, sections: list[Section]) -> Section | None:
    title_norm = normalize(title)
    for section in sections:
        if normalize(section.title) == title_norm:
            return section

    title_by_norm = {normalize(section.title): section for section in sections}
    matches = difflib.get_close_matches(title_norm, title_by_norm.keys(), n=1, cutoff=0.82)
    if matches:
        return title_by_norm[matches[0]]

    return None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "targets",
        nargs="+",
        help='Page title, URL, or slug. Examples: "Agent Skills", skills, config-reference',
    )
    args = parser.parse_args()

    entries = read_index()
    sections = read_sections()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for raw in args.targets:
        title, source_url = resolve_title(raw, entries)
        section = find_section(title, sections)
        if section is None:
            print(f"Not found by title: {title} (from {raw})")
            continue

        entry = next(
            (item for item in entries if normalize(item.title) == normalize(section.title)), None
        )
        source = source_url or (entry.url if entry else None)
        stem = filename_part(source or section.title)
        out_path = OUTPUT_DIR / f"{stem}.txt"

        source_line = f"Source: {source}\n" if source else ""
        out_path.write_text(f"# {section.title}\n{source_line}\n{section.body}\n", encoding="utf-8")
        print(f"Wrote {out_path.relative_to(SKILL_DIR)}")


if __name__ == "__main__":
    main()
