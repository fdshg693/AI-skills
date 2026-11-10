"""Copy-and-adapt template: generate an AI-curated excerpt of an llms.txt index.

Copy this file -- together with check_llms_excerpt.py and
prompt_generate_excerpt.template.md -- into a new skill's directory and adjust
the DEFAULT_* constants below. Fill in the <<...>> placeholders of the prompt
template (save it as e.g. prompts/prompt_generate_excerpt.md).

When to use (see writing-skill-web web-patterns-reference.md section 1.6): the source
llms.txt index is 200+ lines, or -- even well under 200 lines -- only a small
fraction of its entries is relevant to the skill's purpose.

How it works ("driver logic decides formatting, AI only judges"):
  1. Parse every `- [Title](URL): description` entry (grouped under
     `## Section` headings) from the source llms.txt.
  2. Send the prompt + the raw source text to an AI model via the `aim` CLI
     (see the aim-cli skill). The prompt instructs the model to answer
     with ONLY the URLs of the entries to include, one per line, copied
     verbatim from the source.
  3. Assemble the excerpt from the ORIGINAL source entries, verbatim, grouped
     under their source `## Section` headings in source order. The AI never
     rewrites titles/descriptions, so every structured `- [Title](URL)` entry
     in the output can be validated against the source by
     check_llms_excerpt.py.
  4. URLs in the AI output that do not exist in the source (hallucinated or
     mistyped) are dropped with a warning.

The result is an UNREVIEWED DRAFT. Review it, then run check_llms_excerpt.py.
Fix any problem it reports by editing the excerpt file directly -- do NOT
re-run the AI model: regeneration is nondeterministic and can break other
entries, while the checker output already pinpoints exactly what to fix.

Usage: python generate_llms_excerpt.py [--model NAME] [--source PATH]
                                       [--out PATH] [--prompt PATH] [--force]
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# --- adapt these constants when copying into a new skill ---------------------
SKILL_DIR = Path(__file__).resolve().parent
DEFAULT_SOURCE = SKILL_DIR / "output" / "llms.txt"
DEFAULT_OUT = SKILL_DIR / "output" / "excerpt.md"
DEFAULT_PROMPT = SKILL_DIR / "prompts" / "prompt_generate_excerpt.md"
DEFAULT_MODEL = "minimax-m3"  # cheap default; pick per the aim-cli skill
# ------------------------------------------------------------------------------

# `- [Title](URL): description` with the description optional. Adjust only if
# the source index uses a different entry format, and keep in sync with
# check_llms_excerpt.py's ENTRY_RE.
ENTRY_RE = re.compile(r"^- \[(?P<title>[^\]]+)\]\((?P<url>\S+)\)(?::\s*(?P<desc>.*))?$")
SECTION_RE = re.compile(r"^## +(?P<name>.+?)\s*$")
URL_RE = re.compile(r"https?://\S+")
FETCHED_AT_RE = re.compile(r"^fetched_at:\s*(\S+)", re.MULTILINE)


def parse_entries_with_section(text: str) -> list[dict]:
    entries = []
    section = ""
    for line in text.splitlines():
        stripped = line.strip()
        section_match = SECTION_RE.match(stripped)
        if section_match:
            section = section_match.group("name")
            continue
        entry_match = ENTRY_RE.match(stripped)
        if entry_match:
            entry = entry_match.groupdict()
            entry["desc"] = entry["desc"] or ""
            entry["section"] = section
            entries.append(entry)
    return entries


def call_aim(model: str, prompt: str, source_text: str) -> str:
    full_prompt = f"{prompt}\n---\n\n{source_text}"
    try:
        result = subprocess.run(
            ["aim", "--model", model],
            input=full_prompt,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
    except FileNotFoundError:
        raise RuntimeError("`aim` CLI not found on PATH (see the aim-cli skill)")
    if result.returncode != 0:
        raise RuntimeError(f"aim CLI failed (exit {result.returncode}): {result.stderr.strip()}")
    return result.stdout


def extract_urls(ai_output: str) -> set[str]:
    urls = set()
    for match in URL_RE.finditer(ai_output):
        urls.add(match.group(0).rstrip(").,:;\"'>"))
    return urls


def format_entry(entry: dict) -> str:
    if entry["desc"]:
        return f"- [{entry['title']}]({entry['url']}): {entry['desc']}"
    return f"- [{entry['title']}]({entry['url']})"


def build_excerpt(
    entries: list[dict], included_urls: set[str], source_rel: str, fetched_at: str, model: str
) -> tuple[str, int]:
    generated_at = datetime.now(timezone.utc).isoformat()
    lines = [
        "---",
        f"source: {source_rel}",
        f"extracted_from_fetched_at: {fetched_at}",
        f"generated_at: {generated_at}",
        f"generated_by: {Path(__file__).name} (aim --model {model})",
        "note: >",
        "  DRAFT generated automatically by asking an AI model which entries in the",
        "  source llms.txt are relevant to this skill. This has NOT been reviewed",
        "  yet -- review every entry, then run the check script to confirm the",
        "  format and that titles/URLs match the source. Fix problems by editing",
        "  this file directly (do not re-run the AI model).",
        "---",
        "",
    ]
    current_section = None
    included_count = 0
    for entry in entries:
        if entry["url"] not in included_urls:
            continue
        if entry["section"] != current_section:
            if current_section is not None:
                lines.append("")
            if entry["section"]:
                lines.append(f"## {entry['section']}")
                lines.append("")
            current_section = entry["section"]
        lines.append(format_entry(entry))
        included_count += 1
    return "\n".join(lines) + "\n", included_count


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--prompt", type=Path, default=DEFAULT_PROMPT)
    parser.add_argument("--force", action="store_true", help="overwrite --out if it already exists")
    args = parser.parse_args()

    if not args.source.is_file():
        print(f"ERROR: source file not found: {args.source}", file=sys.stderr)
        print("Run this skill's download script first.", file=sys.stderr)
        return 2
    if args.out.exists() and not args.force:
        print(
            f"ERROR: {args.out} already exists. Pass --force to overwrite, or --out "
            "to write a draft elsewhere for review (recommended).",
            file=sys.stderr,
        )
        return 2
    if not args.prompt.is_file():
        print(f"ERROR: prompt file not found: {args.prompt}", file=sys.stderr)
        print(
            "Copy prompt_generate_excerpt.template.md and fill in its placeholders.",
            file=sys.stderr,
        )
        return 2

    source_text = args.source.read_text(encoding="utf-8")
    fetched_at_match = FETCHED_AT_RE.search(source_text)
    fetched_at = fetched_at_match.group(1) if fetched_at_match else "(unknown)"

    entries = parse_entries_with_section(source_text)
    if not entries:
        print(f"ERROR: no entries parsed from source file: {args.source}", file=sys.stderr)
        print("If the index uses a different entry format, adjust ENTRY_RE.", file=sys.stderr)
        return 2

    prompt = args.prompt.read_text(encoding="utf-8")
    if "<<" in prompt:
        print(
            f"ERROR: prompt file still contains unfilled <<...>> placeholders: {args.prompt}",
            file=sys.stderr,
        )
        return 2

    print(f"Calling aim --model {args.model} to judge {len(entries)} source entries ...")
    try:
        ai_output = call_aim(args.model, prompt, source_text)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    source_urls = {e["url"] for e in entries}
    ai_urls = extract_urls(ai_output)
    included_urls = ai_urls & source_urls
    unknown_urls = ai_urls - source_urls
    if unknown_urls:
        print(
            f"WARNING: ignoring {len(unknown_urls)} URL(s) from AI output not present "
            "in source (hallucinated or mistyped):",
            file=sys.stderr,
        )
        for url in sorted(unknown_urls):
            print(f"  - {url}", file=sys.stderr)

    if not included_urls:
        print(
            "ERROR: AI output contained no URLs matching the source. Aborting without "
            "writing output.",
            file=sys.stderr,
        )
        return 2

    source_rel = Path(os.path.relpath(args.source.resolve(), args.out.resolve().parent)).as_posix()

    excerpt_text, included_count = build_excerpt(
        entries, included_urls, source_rel, fetched_at, args.model
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(excerpt_text, encoding="utf-8")

    print(f"Included {included_count}/{len(entries)} source entries -> {args.out}")
    print(
        "\nThis is an UNREVIEWED DRAFT. Review every entry, then run the check "
        "script to confirm the format and that titles/URLs match the source. Fix "
        "any problem by editing the excerpt file directly (do not re-run the AI model)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
