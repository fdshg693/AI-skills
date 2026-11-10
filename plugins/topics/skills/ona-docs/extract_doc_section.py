"""Extract one docs page's section from output/docs/llms-full.txt.

output/docs/llms-full.txt (https://ona.com/docs/llms-full.txt) follows the
repeating pattern:

    # <Title>
    Source: <URL>

    <body>
    # <Title>
    Source: <URL>
    ...

(confirmed by sampling the file; see inspect_section_markers.py in the
writing-skill-web meta-skill for the check this was run through). Given a
URL or slug found in output/docs/llms.txt, this pulls just that page's
section instead of grepping the ~87k-line full dump.

The full extracted section is ALWAYS written to output/temp/<slug>.txt and
its path is always printed, so the full text stays available even when a
summary is produced. When the extracted body is larger than
--summarize-threshold characters (default DEFAULT_SUMMARIZE_THRESHOLD_CHARS),
the body is additionally summarized via the `aim` CLI (see the aim-cli
skill) and written to output/temp/<slug>.summary.md. Pass --no-summarize to
always get the full text only.

Usage:
    python extract_doc_section.py https://ona.com/docs/ona/agents-md
    python extract_doc_section.py ona/agents-md ona/agents/codex
    python extract_doc_section.py ona/agents-md --summarize-threshold 4000 --model glm-5.2
    python extract_doc_section.py ona/agents-md --no-summarize
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_INPUT = Path(__file__).resolve().parent / "output" / "docs" / "llms-full.txt"
DEFAULT_BASE_URL = "https://ona.com/docs/"

DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent / "output" / "temp"

# Bodies longer than this (in characters) get summarized via `aim` instead of
# only being written out in full. Chosen to comfortably fit a single-page
# body in a model's context alongside the summarization prompt.
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
    segment -- Ona docs paths can share a trailing segment (e.g. several
    .../overview pages) across unrelated sections, which would otherwise
    collide."""
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


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "urls",
        nargs="+",
        help="Target URL(s) or slug(s), e.g. 'ona/agents-md' (trailing .md optional)",
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

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
