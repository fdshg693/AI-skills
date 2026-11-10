#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "pyyaml",
# ]
# ///
"""Generate an initial draft of output/copilot-excerpt.md from the source llms.txt
(path defined in config.yml) by asking an AI model (via the `aim` CLI) which entries
are about GitHub Copilot / AI agent features in VS Code.

check_copilot_excerpt.py and verify_agent_relevance.py both assume output/copilot-excerpt.md
already exists -- it was originally produced by hand-reviewing an LLM draft (see
README.md). This script automates producing that initial draft, e.g. for regenerating
the excerpt from scratch after a major reorganization of the upstream docs where most
of the existing curation no longer applies.

To avoid the title/description drift problem check_copilot_excerpt.py exists to catch,
this script does NOT let the AI rewrite entries. It only asks the AI to decide, per
entry, whether to include it (see prompts/prompt_generate_excerpt.md); the output
markdown is then assembled by this script itself from the original entries in the
source llms.txt (path defined in config.yml), verbatim, grouped under their
source `## Section` headings in source order. This is the same "driver logic decides
formatting, AI only judges" split used by verify_agent_relevance.py.

The source llms.txt has hundreds of entries. Sending all of them to the model in a
single call degrades judgment quality (long lists make models skim/miss entries), so
this script batches entries into chunks of CHUNK_SIZE and calls `aim` once per chunk,
unioning the included URLs across chunks. This means judging N entries costs
ceil(N / CHUNK_SIZE) model calls, not 1 -- expected and intentional.

The result is an UNREVIEWED DRAFT. A human must read it end-to-end and fix any
miscuration before it replaces the real output/copilot-excerpt.md -- this script
refuses to overwrite an existing file unless --force is given.

Usage: uv run generate_copilot_excerpt.py [--model {mini-m3,gpt-120b,glm-5.2,gpt-luna}]
                                           [--source PATH] [--out PATH] [--prompt PATH] [--force]
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import check_copilot_excerpt as base
import extract_uncurated_entries as eu

SKILL_DIR = Path(__file__).resolve().parent
DEFAULT_PROMPT = SKILL_DIR / "prompts" / "prompt_generate_excerpt.md"

CHUNK_SIZE = 50
SUSPICIOUS_RATIO = 0.4  # a general-docs chunk being mostly Copilot-relevant is implausible

URL_RE = re.compile(r"https?://\S+")
FETCHED_AT_RE = re.compile(r"^fetched_at:\s*(\S+)", re.MULTILINE)


def chunk_entries(entries: list[dict], size: int) -> list[list[dict]]:
    return [entries[i : i + size] for i in range(0, len(entries), size)]


def render_chunk(entries_chunk: list[dict]) -> str:
    """Render a chunk of entries back to `## Section` / `- [Title](URL): desc` lines,
    the same shape the AI would see in the full llms.txt, so the prompt's instructions
    (written against that shape) still apply per-chunk."""
    lines = []
    current_section = None
    for entry in entries_chunk:
        if entry["section"] != current_section:
            lines.append(f"## {entry['section']}")
            current_section = entry["section"]
        lines.append(f"- [{entry['title']}]({entry['url']}): {entry['desc']}")
    return "\n".join(lines) + "\n"


def call_aim(model: str, prompt: str, source_text: str) -> str:
    full_prompt = f"{prompt}\n---\n\n{source_text}"
    result = subprocess.run(
        ["aim", "--model", model],
        input=full_prompt,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if result.returncode != 0:
        raise RuntimeError(f"aim CLI failed (exit {result.returncode}): {result.stderr.strip()}")
    return result.stdout


def extract_urls(ai_output: str) -> set[str]:
    urls = set()
    for match in URL_RE.finditer(ai_output):
        urls.add(match.group(0).rstrip(").,:;\"'>"))
    return urls


def _looks_suspicious(chunk_included: set[str], chunk: list[dict]) -> bool:
    return len(chunk) >= 5 and len(chunk_included) > len(chunk) * SUSPICIOUS_RATIO


def _judge_chunk(
    model: str, prompt: str, chunk: list[dict], chunk_source_urls: set[str]
) -> tuple[set[str], set[str]]:
    ai_output = call_aim(model, prompt, render_chunk(chunk))
    ai_urls = extract_urls(ai_output)
    return ai_urls & chunk_source_urls, ai_urls - chunk_source_urls


def build_excerpt(
    entries: list[dict], included_urls: set[str], source_rel: str, fetched_at: str, model: str
) -> tuple[str, int]:
    generated_at = datetime.now(timezone.utc).isoformat()
    lines = [
        "---",
        f"source: {source_rel}",
        f"extracted_from_fetched_at: {fetched_at}",
        f"generated_at: {generated_at}",
        f"generated_by: generate_copilot_excerpt.py (aim --model {model})",
        "note: >",
        "  DRAFT generated automatically by asking an AI model which entries in",
        "  vscode-docs/output/llms.txt relate to GitHub Copilot / AI features in VS",
        "  Code. This has NOT been reviewed by a human yet -- treat it as a starting",
        "  point, not a replacement for the curated output/copilot-excerpt.md. Review",
        "  every entry, then run check_copilot_excerpt.py to confirm titles/URLs match,",
        "  before using it to replace the real file.",
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
            lines.append(f"## {entry['section']}")
            lines.append("")
            current_section = entry["section"]
        lines.append(f"- [{entry['title']}]({entry['url']}): {entry['desc']}")
        included_count += 1
    return "\n".join(lines) + "\n", included_count


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--model",
        default="mini-m3",
        choices=["mini-m3", "gpt-120b", "glm-5.2", "gpt-luna"],
        help=(
            "default mini-m3 (cheapest). In manual testing this model was flaky on this "
            "task -- across repeated identical calls it sometimes returned an empty "
            "response, and at least once dumped the entire input chunk back as "
            "'included' despite explicit instructions not to. The suspicious-chunk "
            "retry/warning below exists specifically to catch that failure mode; it "
            "does not require switching the default model."
        ),
    )
    parser.add_argument("--source", type=Path, default=base.DEFAULT_SOURCE)
    parser.add_argument("--out", type=Path, default=base.DEFAULT_EXCERPT)
    parser.add_argument("--prompt", type=Path, default=DEFAULT_PROMPT)
    parser.add_argument("--force", action="store_true", help="overwrite --out if it already exists")
    args = parser.parse_args()

    if not args.source.is_file():
        print(f"ERROR: source file not found: {args.source}", file=sys.stderr)
        print("Run the vscode-docs skill's download script first.", file=sys.stderr)
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
        return 2

    source_text = args.source.read_text(encoding="utf-8")
    fetched_at_match = FETCHED_AT_RE.search(source_text)
    fetched_at = fetched_at_match.group(1) if fetched_at_match else "(unknown)"

    entries = eu.parse_entries_with_section(source_text)
    if not entries:
        print(f"ERROR: no entries parsed from source file: {args.source}", file=sys.stderr)
        return 2

    prompt = args.prompt.read_text(encoding="utf-8")
    chunks = chunk_entries(entries, CHUNK_SIZE)
    print(
        f"Calling aim --model {args.model} to judge {len(entries)} source entries "
        f"in {len(chunks)} chunks of up to {CHUNK_SIZE} ..."
    )

    included_urls: set[str] = set()
    unknown_urls: set[str] = set()
    suspicious_chunks: list[int] = []
    for i, chunk in enumerate(chunks, start=1):
        chunk_source_urls = {e["url"] for e in chunk}
        try:
            chunk_included, chunk_unknown = _judge_chunk(
                args.model, prompt, chunk, chunk_source_urls
            )
        except RuntimeError as exc:
            print(f"ERROR: chunk {i}/{len(chunks)} failed: {exc}", file=sys.stderr)
            return 2

        if _looks_suspicious(chunk_included, chunk):
            print(
                f"  chunk {i}/{len(chunks)}: {len(chunk_included)}/{len(chunk)} included looks "
                "implausibly high (a general docs chunk being mostly Copilot-relevant is unlikely -- "
                "this matched a real failure mode in testing where the model echoed the whole "
                "input back instead of judging it). Retrying once ...",
                file=sys.stderr,
            )
            try:
                retry_included, retry_unknown = _judge_chunk(
                    args.model, prompt, chunk, chunk_source_urls
                )
            except RuntimeError as exc:
                print(f"ERROR: chunk {i}/{len(chunks)} retry failed: {exc}", file=sys.stderr)
                return 2
            if len(retry_included) < len(chunk_included):
                chunk_included, chunk_unknown = retry_included, retry_unknown
            if _looks_suspicious(chunk_included, chunk):
                suspicious_chunks.append(i)

        included_urls |= chunk_included
        unknown_urls |= chunk_unknown
        print(f"  chunk {i}/{len(chunks)} ({len(chunk)} entries): included {len(chunk_included)}")

    if suspicious_chunks:
        print(
            f"\nWARNING: chunk(s) {suspicious_chunks} still look implausibly high after a retry -- "
            "review their entries by hand before trusting this draft.",
            file=sys.stderr,
        )

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

    source_rel = Path(os.path.relpath(args.source.resolve(), base.REPO_ROOT)).as_posix()

    excerpt_text, included_count = build_excerpt(
        entries, included_urls, source_rel, fetched_at, args.model
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(excerpt_text, encoding="utf-8")

    print(f"Included {included_count}/{len(entries)} source entries -> {args.out}")
    print(
        "\nThis is an UNREVIEWED DRAFT. A human must read it end-to-end, fix any "
        "mis-curated entries, then run check_copilot_excerpt.py to confirm titles/URLs "
        "match before treating it as the real output/copilot-excerpt.md."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
