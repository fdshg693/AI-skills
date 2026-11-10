"""Extract one docs page's section from output/llms-full.txt.

https://ccusage.com/llms-full.txt is a VitePress dump: pages are
concatenated with a repeating YAML frontmatter marker rather than the
`# Title` / `Source: URL` pattern used by some other sites:

    ---
    url: /guide/daily-reports.md
    ---
    # Daily Reports
    <body>
    ---
    url: /guide/weekly-reports.md
    ---
    ...

(confirmed by sampling the file; inspect_section_markers.py defaults in
this directory are set to `url:` then `# ` h1). Given a URL or slug found
in output/llms.txt, this pulls just that page's section instead of
grepping the whole dump.

The full extracted section is ALWAYS written to output/temp/<slug>.txt and
its path is always printed, so the full text stays available even when a
summary is produced. When the extracted body is larger than
--summarize-threshold characters (default DEFAULT_SUMMARIZE_THRESHOLD_CHARS),
the body is additionally summarized via the `aim` CLI (see the aim-cli
skill) and written to output/temp/<slug>.summary.md. Pass --no-summarize to
always get the full text only.

Usage:
    python extract_doc_section.py https://ccusage.com/guide/daily-reports
    python extract_doc_section.py guide/daily-reports guide/cost-modes
    python extract_doc_section.py guide/daily-reports --summarize-threshold 4000 --model glm-5.2
    python extract_doc_section.py guide/daily-reports --no-summarize
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_INPUT = Path(__file__).resolve().parent / "output" / "llms-full.txt"
DEFAULT_BASE_URL = "https://ccusage.com/"

DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent / "output" / "temp"

# Bodies longer than this (in characters) get summarized via `aim` instead of
# only being written out in full. Chosen to comfortably fit a single-page
# body in a model's context alongside the summarization prompt.
DEFAULT_SUMMARIZE_THRESHOLD_CHARS = 6000
DEFAULT_SUMMARIZE_MODEL = "minimax-m3"  # see aim-cli skill for model choices

# Page boundaries are `url: /path.md` lines (inside VitePress YAML
# frontmatter). Trailing `---` before the next page is stripped from the body.
URL_LINE_RE = re.compile(r"^url: (\S+)\s*$", re.MULTILINE)
H1_RE = re.compile(r"^# ([^#\n][^\n]*)\n")
# A page body is followed by its closing `---` and the next page's opening
# `---`; strip one or more trailing YAML fences.
TRAILING_FENCE_RE = re.compile(r"(?:\n---\s*)+\n?\s*$")

SUMMARIZE_PROMPT_TEMPLATE = (
    "Summarize the following documentation page for a developer who needs to "
    "act on it. Preserve concrete facts: code samples, commands, config keys, "
    "parameter names/types, defaults, and caveats/warnings. Omit marketing "
    "language and repetition. Do not invent information that isn't in the "
    "source.\n\n# {title}\nSource: {source}\n\n{body}"
)


def canonicalize(url_or_path: str, base_url: str) -> str:
    """Map a site-relative `url:` field, slug, or absolute URL onto a
    canonical https://ccusage.com/<path> form (no trailing slash, no .md)."""
    raw = url_or_path.strip()
    if raw.startswith("http://") or raw.startswith("https://"):
        url = raw
    else:
        url = base_url.rstrip("/") + "/" + raw.lstrip("/")
    if url.endswith(".md"):
        url = url[: -len(".md")]
    return url.rstrip("/") or base_url.rstrip("/")


def parse_sections(text: str, base_url: str) -> dict[str, tuple[str, str, str]]:
    """canonical URL -> (title, canonical URL, body)."""
    matches = list(URL_LINE_RE.finditer(text))
    sections: dict[str, tuple[str, str, str]] = {}
    for i, match in enumerate(matches):
        url_field = match.group(1)
        chunk_start = match.end()
        chunk_end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        chunk = text[chunk_start:chunk_end]
        # After `url: /path.md` the YAML fence closes with `---`.
        chunk = re.sub(r"^\s*---\s*\n", "", chunk, count=1)
        title = ""
        title_match = H1_RE.match(chunk)
        if title_match:
            title = title_match.group(1).strip()
            body = chunk[title_match.end() :]
        else:
            body = chunk
        body = TRAILING_FENCE_RE.sub("", body).strip()
        source = canonicalize(url_field, base_url)
        sections[source] = (title, source, body)
    return sections


def resolve_url(url_or_slug: str, base_url: str) -> str:
    return canonicalize(url_or_slug, base_url)


def slug_from_url(url: str, base_url: str) -> str:
    """Filename-safe slug that keeps the full path, not just the last
    segment -- even a small docs site can reuse leaf names across
    unrelated subdirectories."""
    rel = url[len(base_url) :] if url.startswith(base_url) else url.rsplit("://", 1)[-1]
    return rel.strip("/").replace("/", "__") or "index"


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
        help="Target URL(s) or slug(s), e.g. 'guide/daily-reports' (trailing .md optional)",
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

    sections = parse_sections(args.input.read_text(encoding="utf-8"), args.base_url)
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
