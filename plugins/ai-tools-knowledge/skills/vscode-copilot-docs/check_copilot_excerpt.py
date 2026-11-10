#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "pyyaml",
# ]
# ///
"""Check that titles/URLs in the curated Copilot excerpt still match the source llms.txt.

output/copilot-excerpt.md is a hand-curated subset of the llms.txt pointed to by
config.yml's `source` key (see README.md in this directory for when/how to run
this script). Because that source llms.txt is re-downloaded periodically, and
because the excerpt was originally produced by an LLM draft, both entries can
drift or be wrong: a page may get renamed/removed upstream, or the excerpt may
have a typo'd title/URL that was never actually in the source.

This script cross-checks every `- [Title](URL): description` entry in the excerpt
against the source by URL (the more stable key) and reports:

  - MISSING   the excerpt's URL no longer exists in the source llms.txt
  - TITLE     the URL exists in the source but under a different title
  - DESC      the URL/title match but the description text has drifted (informational)

It also lists source entries that look Copilot/AI-relevant (by keyword) but are not
present in the excerpt at all, as candidates a human should consider adding -- this is
a heuristic hint, not a re-run of the original curation judgment.

This script depends on PyYAML (to read config.yml) and is not guaranteed to be on a
bare `python`'s import path -- run it via `uv run check_copilot_excerpt.py`, which
resolves the dependency declared below automatically.

Usage: uv run check_copilot_excerpt.py [--excerpt PATH] [--source PATH]
Exit code: 1 if any MISSING or TITLE mismatch is found, 0 otherwise.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

SKILL_DIR = Path(__file__).resolve().parent
CONFIG_PATH = SKILL_DIR / "config.yml"
DEFAULT_EXCERPT = SKILL_DIR / "output" / "copilot-excerpt.md"


def find_repo_root(start: Path) -> Path:
    """Walk upward from `start` to find the repo root (the directory containing `.git`).

    config.yml's `source` key is repo-root-relative, not relative to this script's own
    directory -- a file-relative path would break both when the source moves *and* when
    this skill directory itself moves, which is twice as fragile as anchoring to the
    (much more stable) repo root.
    """
    for candidate in (start, *start.parents):
        if (candidate / ".git").exists():
            return candidate
    print(f"ERROR: could not find repo root (no .git found above {start})", file=sys.stderr)
    sys.exit(2)


REPO_ROOT = find_repo_root(SKILL_DIR)


def _load_default_source() -> Path:
    """Resolve the excerpt source path from config.yml's `source` key (repo-root-relative)."""
    if not CONFIG_PATH.is_file():
        print(f"ERROR: config file not found: {CONFIG_PATH}", file=sys.stderr)
        sys.exit(2)
    try:
        data = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        print(f"ERROR: {CONFIG_PATH} is not valid YAML: {exc}", file=sys.stderr)
        sys.exit(2)
    source = data.get("source") if isinstance(data, dict) else None
    if not isinstance(source, str) or not source.strip():
        print(f"ERROR: {CONFIG_PATH} must define a non-empty string key 'source'", file=sys.stderr)
        sys.exit(2)
    return (REPO_ROOT / source).resolve()


DEFAULT_SOURCE = _load_default_source()

ENTRY_RE = re.compile(r"^- \[(?P<title>[^\]]+)\]\((?P<url>\S+)\):\s*(?P<desc>.*)$")

CANDIDATE_KEYWORDS = ("copilot", "chat", "agent", " ai ", "ai-", "-ai", "mcp")


def parse_entries(text: str) -> list[dict]:
    entries = []
    for line in text.splitlines():
        match = ENTRY_RE.match(line.strip())
        if match:
            entries.append(match.groupdict())
    return entries


def looks_candidate(entry: dict) -> bool:
    haystack = f"{entry['title']} {entry['url']} {entry['desc']}".lower()
    return any(keyword in haystack for keyword in CANDIDATE_KEYWORDS)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--excerpt", type=Path, default=DEFAULT_EXCERPT)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    args = parser.parse_args()

    if not args.source.is_file():
        print(f"ERROR: source file not found: {args.source}", file=sys.stderr)
        print("Run the vscode-docs skill's download script first.", file=sys.stderr)
        return 2
    if not args.excerpt.is_file():
        print(f"ERROR: excerpt file not found: {args.excerpt}", file=sys.stderr)
        return 2

    excerpt_entries = parse_entries(args.excerpt.read_text(encoding="utf-8"))
    source_entries = parse_entries(args.source.read_text(encoding="utf-8"))
    source_by_url = {e["url"]: e for e in source_entries}
    excerpt_urls = {e["url"] for e in excerpt_entries}

    missing = []
    title_mismatches = []
    desc_drift = []

    for entry in excerpt_entries:
        source_entry = source_by_url.get(entry["url"])
        if source_entry is None:
            missing.append(entry)
            continue
        if source_entry["title"] != entry["title"]:
            title_mismatches.append((entry, source_entry))
        elif source_entry["desc"] != entry["desc"]:
            desc_drift.append((entry, source_entry))

    candidates = [e for e in source_entries if e["url"] not in excerpt_urls and looks_candidate(e)]

    print(
        f"Checked {len(excerpt_entries)} excerpt entries against {len(source_entries)} source entries.\n"
    )

    if missing:
        print(
            f"MISSING ({len(missing)}) -- excerpt URL not found in source llms.txt (renamed/removed upstream, or never existed):"
        )
        for e in missing:
            print(f"  - [{e['title']}]({e['url']})")
        print()

    if title_mismatches:
        print(
            f"TITLE MISMATCH ({len(title_mismatches)}) -- URL exists in source under a different title:"
        )
        for excerpt_e, source_e in title_mismatches:
            print(f"  - excerpt: [{excerpt_e['title']}]({excerpt_e['url']})")
            print(f"    source:  [{source_e['title']}]({source_e['url']})")
        print()

    if desc_drift:
        print(
            f"DESCRIPTION DRIFT ({len(desc_drift)}, informational only) -- title/URL match but description text changed upstream:"
        )
        for excerpt_e, source_e in desc_drift:
            print(f"  - [{excerpt_e['title']}]({excerpt_e['url']})")
            print(f"    excerpt: {excerpt_e['desc']}")
            print(f"    source:  {source_e['desc']}")
        print()

    if candidates:
        print(
            f"POSSIBLE ADDITIONS ({len(candidates)}, informational only) -- source entries with Copilot/AI-ish keywords not in the excerpt; review manually, this is a keyword heuristic, not a re-curation:"
        )
        for e in candidates:
            print(f"  - [{e['title']}]({e['url']}): {e['desc']}")
        print()

    if not missing and not title_mismatches:
        print("OK: every excerpt title/URL matches the source llms.txt.")

    return 1 if (missing or title_mismatches) else 0


if __name__ == "__main__":
    raise SystemExit(main())
