# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""Search the local snapshot of Playwright's docs sources (output/docs/**/*.md).

The snapshot is ~3 MB across ~180 files, so reading it wholesale is not an option.
This gives four ways in:

  search    uv run search_playwright_docs.py "storage state" reuse
  api       uv run search_playwright_docs.py --api Locator.click
  sections  uv run search_playwright_docs.py --sections api/class-locator.md
  show      uv run search_playwright_docs.py --show api/class-locator.md#Locator.click

Search matches every term (case-insensitive, AND) on the same line, ranks files by
hit count -- headings and titles count extra -- and prints `path:line` hits with
snippets. release-notes-*.md are demoted so guides win; search them explicitly with
--path "release-notes-*". Filter with --lang / --path, widen with --any or --regex.

Standard library only; run sync_playwright_docs.py first to create the snapshot.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import re
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = SKILL_DIR / "output"
DOCS_DIR = OUTPUT_DIR / "docs"
META_PATH = OUTPUT_DIR / "_meta.json"

HEADING_RE = re.compile(r"^(#{1,4})\s+(.*)$")
# `## async method: Locator.click`, `## property: Page.clock`, `## event: Page.close`
MEMBER_RE = re.compile(r"^##\s+(?:async\s+)?(method|property|event)\s*:\s*(\S+)")
MAX_SECTION_LINES = 400
# release-notes-*.md mention every feature many times over; without a penalty they
# outrank the guide that actually explains the feature on nearly every query.
RELEASE_NOTES_PENALTY = 4
FENCE_RE = re.compile(r"^\s*```")


def headings(lines: list[str]):
    """Yield (index, level, text, member name or '') for real headings only.

    `# Navigate to a page` inside a ```python fence is a comment, not a heading.
    """
    in_fence = False
    for index, line in enumerate(lines):
        if FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        match = HEADING_RE.match(line)
        if not match:
            continue
        member = MEMBER_RE.match(line)
        yield index, len(match.group(1)), match.group(2), member.group(2) if member else ""


def load_meta() -> dict:
    if not META_PATH.is_file():
        raise RuntimeError("snapshot missing. Run: uv run sync_playwright_docs.py --force")
    return json.loads(META_PATH.read_text(encoding="utf-8"))


def doc_files(lang: str | None, path_filters: list[str]) -> list[tuple[str, dict]]:
    """(relative path, meta entry) for every snapshot file passing the filters."""
    meta = load_meta()
    out: list[tuple[str, dict]] = []
    for entry in meta.get("files", []):
        rel = entry["output"][len("docs/") :]
        if lang:
            langs = entry.get("langs") or []
            # A file with no language suffix documents all languages.
            if langs and lang not in langs:
                continue
        if path_filters and not any(
            fnmatch.fnmatch(rel, pat) or pat.lower() in rel.lower() for pat in path_filters
        ):
            continue
        out.append((rel, entry))
    return out


def read_doc(rel: str) -> list[str]:
    path = DOCS_DIR / rel
    if not path.is_file():
        raise RuntimeError(f"not in snapshot: {rel}")
    return path.read_text(encoding="utf-8", errors="replace").splitlines()


def build_matcher(terms: list[str], use_regex: bool, match_any: bool):
    if use_regex:
        patterns = [re.compile(t, re.IGNORECASE) for t in terms]
        test = lambda line: [bool(p.search(line)) for p in patterns]  # noqa: E731
    else:
        lowered = [t.lower() for t in terms]
        test = lambda line: [t in line.lower() for t in lowered]  # noqa: E731

    def matches(line: str) -> bool:
        results = test(line)
        return any(results) if match_any else all(results)

    return matches


def search(args: argparse.Namespace) -> int:
    matches = build_matcher(args.terms, args.regex, args.any)
    results: list[tuple[int, str, str, list[tuple[int, str]]]] = []

    for rel, entry in doc_files(args.lang, args.path):
        lines = read_doc(rel)
        heading_lines = {index for index, _, _, _ in headings(lines)}
        hits: list[tuple[int, str]] = []
        score = 0
        for number, line in enumerate(lines, start=1):
            if not matches(line):
                continue
            hits.append((number, line.strip()))
            score += 3 if number - 1 in heading_lines else 1
        if entry.get("title") and matches(entry["title"]):
            score += 5
        if Path(rel).name.startswith("release-notes"):
            score = max(1, score // RELEASE_NOTES_PENALTY)
        if not hits:
            continue
        results.append((score, rel, entry.get("title", ""), hits))

    if not results:
        print("No matches. Try fewer terms, --any, or --regex.")
        return 1

    results.sort(key=lambda r: (-r[0], r[1]))
    shown = results[: args.limit]
    for score, rel, title, hits in shown:
        print(f"\n== {rel} — {title}  ({len(hits)} hits, score {score})")
        for number, text in hits[: args.per_file]:
            if len(text) > 200:
                text = text[:200] + " …"
            print(f"  {rel}:{number}: {text}")
        if len(hits) > args.per_file:
            print(f"  … {len(hits) - args.per_file} more hit(s) in this file")

    if len(results) > len(shown):
        print(f"\n… {len(results) - len(shown)} more file(s) matched (raise --limit)")
    print(
        "\nRead a section instead of the whole file: "
        f"--show {shown[0][1]}#<heading>   |   list headings: --sections {shown[0][1]}"
    )
    return 0


def find_api(args: argparse.Namespace) -> int:
    """Locate `Class.member` API entries across the snapshot."""
    query = args.api.lower()
    cls, _, member = query.partition(".")
    found: list[tuple[str, int, str, str]] = []

    for rel, _entry in doc_files(args.lang, args.path):
        lines = read_doc(rel)
        for index, _level, _text, name in headings(lines):
            if not name:
                continue
            kind = MEMBER_RE.match(lines[index]).group(1)
            number = index + 1
            lowered = name.lower()
            if member:
                hit = lowered == query or lowered.startswith(query)
            else:
                hit = lowered.split(".")[0] == cls
            if hit:
                found.append((rel, number, kind, name))

    if not found:
        print(f"No API entry matching '{args.api}'. Try --api {cls} to list the class.")
        return 1

    for rel, number, kind, name in found:
        print(f"{rel}:{number}: {kind} {name}")
    print(f"\n{len(found)} entry(ies). Read one with: --show {found[0][0]}#{found[0][3]}")
    return 0


def list_sections(rel: str) -> int:
    for index, level, text, _name in headings(read_doc(rel)):
        print(f"{index + 1:>6}: {'  ' * (level - 1)}{text}")
    return 0


def show(target: str) -> int:
    """Print a snapshot file, or one section of it (`path#heading-substring`)."""
    rel, _, wanted = target.partition("#")
    lines = read_doc(rel)

    if not wanted:
        for number, line in enumerate(lines, start=1):
            print(f"{number:>6}: {line}")
        return 0

    needle = wanted.lower()
    start: int | None = None
    level = 0
    for index, heading_level, text, name in headings(lines):
        candidates = [text.lower()] + ([name.lower()] if name else [])
        if start is None:
            if any(needle == c or needle in c for c in candidates):
                start = index
                level = heading_level
        elif heading_level <= level:
            end = index
            break
    else:
        end = len(lines)

    if start is None:
        print(f"No heading matching '{wanted}' in {rel}. Use --sections {rel}.")
        return 1

    body = lines[start:end]
    truncated = len(body) > MAX_SECTION_LINES
    for number, line in enumerate(body[:MAX_SECTION_LINES], start=start + 1):
        print(f"{number:>6}: {line}")
    if truncated:
        print(
            f"… section truncated at {MAX_SECTION_LINES} lines "
            f"(ends at line {end}); read {rel} directly for the rest"
        )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("terms", nargs="*", help="Search terms (all must match a line).")
    parser.add_argument("--api", metavar="Class[.member]", help="Find API entries.")
    parser.add_argument("--show", metavar="PATH[#HEADING]", help="Print a file/section.")
    parser.add_argument("--sections", metavar="PATH", help="List a file's headings.")
    parser.add_argument(
        "--lang",
        choices=("js", "python", "java", "csharp"),
        help="Keep only files for this language (plus language-neutral ones).",
    )
    parser.add_argument(
        "--path",
        action="append",
        default=[],
        metavar="GLOB",
        help="Restrict to paths matching a glob or substring (repeatable).",
    )
    parser.add_argument("--any", action="store_true", help="Match any term, not all.")
    parser.add_argument("--regex", action="store_true", help="Treat terms as regexes.")
    parser.add_argument("--limit", type=int, default=12, help="Max files to print.")
    parser.add_argument("--per-file", type=int, default=6, help="Max hits per file.")
    args = parser.parse_args()

    try:
        if args.show:
            return show(args.show)
        if args.sections:
            return list_sections(args.sections)
        if args.api:
            return find_api(args)
        if not args.terms:
            parser.print_help()
            return 2
        return search(args)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
