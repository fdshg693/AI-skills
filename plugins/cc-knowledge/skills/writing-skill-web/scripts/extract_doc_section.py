"""Copy-and-adapt template: extract one page's section from a llms-full.txt-
style dump that follows the repeating pattern:

    # <Title>
    Source: <URL>

    <body>
    # <Title>
    Source: <URL>
    ...

Only use this template after confirming the target file actually follows
that pattern -- run inspect_section_markers.py on the downloaded file first
and check its verdict.

Copy this file into the new skill's directory and adjust DEFAULT_INPUT /
DEFAULT_BASE_URL (or pass --input/--base-url instead of editing defaults).

The full extracted section is ALWAYS written to output/temp/<slug>.txt and
its path is always printed, so the full text stays available even when a
summary is produced. When the extracted body is larger than
--summarize-threshold characters (default DEFAULT_SUMMARIZE_THRESHOLD_CHARS),
the body is additionally summarized via the `aim` CLI (see the aim-cli
skill) and written to output/temp/<slug>.summary.md. This keeps a single
huge page from blowing up the context window while still leaving the full
text one path away for verification. Pass --no-summarize to always get the
full text only.

Real examples that follow this exact pattern, for reference:
- skills/plugins/cc-knowledge/skills/claude-code-docs/extract_doc_section.py (code.claude.com)
- skills/plugins/topics/skills/openrouter-docs/extract_doc_section.py (openrouter.ai) --
  also shows how to disambiguate collisions where the URL's last path
  segment repeats across pages (e.g. many .../README source URLs): key
  and name output files by the *full* path, not just the last segment.

Usage:
    python extract_doc_section.py https://example.com/docs/some-page
    python extract_doc_section.py some-page other/nested-page
    python extract_doc_section.py --input output/llms-full.txt --base-url https://example.com/docs/ some-page
    python extract_doc_section.py some-page --summarize-threshold 4000 --model glm-5.2
    python extract_doc_section.py some-page --no-summarize
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# Adjust these two when copying this file into a new skill.
DEFAULT_INPUT = Path(__file__).resolve().parent / "output" / "llms-full.txt"
DEFAULT_BASE_URL = "https://example.com/docs/"

DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent / "output" / "temp"

# Bodies longer than this (in characters) get summarized via `aim` instead of
# only being written out in full. Chosen to comfortably fit a single-page
# body in a model's context alongside the summarization prompt; adjust per
# skill if the target site's pages run unusually large or small.
DEFAULT_SUMMARIZE_THRESHOLD_CHARS = 6000
DEFAULT_SUMMARIZE_MODEL = "minimax-m3"  # see aim-cli skill for model choices

SECTION_RE = re.compile(
    r"^# (?P<title>[^\n]+)\nSource: (?P<source>\S+)\n\n(?P<body>.*?)(?=\n# [^\n]+\nSource: \S+\n|\Z)",
    re.DOTALL | re.MULTILINE,
)

SUMMARIZE_PROMPT_TEMPLATE = (
    "Summarize the following documentation page for a developer who needs to "
    "act on it. Preserve concrete facts: code samples, commands, config keys, "
    "parameter names/types, defaults, and caveats/warnings. Omit marketing "
    "language and repetition. Do not invent information that isn't in the "
    "source.\n\n# {title}\nSource: {source}\n\n{body}"
)


def parse_sections(text: str) -> dict[str, tuple[str, str, str]]:
    """source URL -> (title, source, body)."""
    sections: dict[str, tuple[str, str, str]] = {}
    for match in SECTION_RE.finditer(text):
        title = match.group("title").strip()
        source = match.group("source").strip()
        body = match.group("body").strip()
        sections[source] = (title, source, body)
    return sections


def resolve_url(url_or_slug: str, base_url: str) -> str:
    if url_or_slug.startswith("http://") or url_or_slug.startswith("https://"):
        url = url_or_slug
    else:
        url = base_url + url_or_slug.strip("/")
    if url.endswith(".md"):
        url = url[: -len(".md")]
    return url


def slug_from_url(url: str, base_url: str) -> str:
    """Filename-safe slug that keeps the full path, not just the last
    segment -- many doc sites reuse leaf names (e.g. README) across
    unrelated subdirectories, which would otherwise collide."""
    rel = url[len(base_url) :] if url.startswith(base_url) else url.rsplit("://", 1)[-1]
    return rel.strip("/").replace("/", "__")


def summarize_via_aim(model: str, title: str, source: str, body: str) -> str:
    prompt = SUMMARIZE_PROMPT_TEMPLATE.format(title=title, source=source, body=body)
    try:
        result = subprocess.run(
            ["aim", "--model", model],
            input=prompt,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
    except FileNotFoundError:
        raise RuntimeError("`aim` CLI not found on PATH (see the aim-cli skill)")
    if result.returncode != 0:
        raise RuntimeError(f"aim CLI failed (exit {result.returncode}): {result.stderr.strip()}")
    return result.stdout.strip()


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "urls",
        nargs="+",
        help="Target URL(s) or slug(s), e.g. 'guides/some-page' (trailing .md optional)",
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help="llms-full.txt-style file to read (default: %(default)s)",
    )
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help="Base URL prefix used to resolve slugs (default: %(default)s)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory to write extracted sections to (default: %(default)s)",
    )
    parser.add_argument(
        "--summarize-threshold",
        type=int,
        default=DEFAULT_SUMMARIZE_THRESHOLD_CHARS,
        help="Summarize bodies longer than this many characters via aim CLI (default: %(default)s)",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_SUMMARIZE_MODEL,
        help="aim CLI model to use for summarization (default: %(default)s)",
    )
    parser.add_argument(
        "--no-summarize", action="store_true", help="Always write full text only, never summarize"
    )
    args = parser.parse_args()

    if not args.input.is_file():
        raise SystemExit(f"Input file not found: {args.input}")

    sections = parse_sections(args.input.read_text(encoding="utf-8"))
    args.output_dir.mkdir(parents=True, exist_ok=True)

    for raw in args.urls:
        url = resolve_url(raw, args.base_url)
        section = sections.get(url)
        if section is None:
            print(f"Not found: {url}")
            continue

        title, source, body = section
        slug = slug_from_url(source, args.base_url)

        # Full text is always written and its path always printed, even when
        # a summary is also produced below -- the full text must stay one
        # path away for verification.
        out_path = args.output_dir / f"{slug}.txt"
        out_path.write_text(f"# {title}\nSource: {source}\n\n{body}\n", encoding="utf-8")

        if args.no_summarize or len(body) <= args.summarize_threshold:
            print(f"Wrote {out_path}")
            continue

        print(f"Wrote full text ({len(body)} chars) -> {out_path}")
        print(
            f"Body exceeds --summarize-threshold ({args.summarize_threshold} chars); calling aim --model {args.model} to summarize ..."
        )
        try:
            summary = summarize_via_aim(args.model, title, source, body)
        except RuntimeError as exc:
            print(
                f"WARNING: summarization failed ({exc}); use the full text above directly.",
                file=sys.stderr,
            )
            continue

        summary_path = args.output_dir / f"{slug}.summary.md"
        summary_path.write_text(
            "\n".join(
                [
                    "---",
                    f"source: {source}",
                    f"title: {title}",
                    f"original_length_chars: {len(body)}",
                    f"full_text: {out_path.name}",
                    f"summarized_at: {datetime.now(timezone.utc).isoformat()}",
                    f"summarized_by: {Path(__file__).name} (aim --model {args.model})",
                    "---",
                    "",
                    summary,
                    "",
                ]
            ),
            encoding="utf-8",
        )
        print(f"Wrote summary -> {summary_path}")
        print(f"(full text for verification if needed -> {out_path})")


if __name__ == "__main__":
    main()
