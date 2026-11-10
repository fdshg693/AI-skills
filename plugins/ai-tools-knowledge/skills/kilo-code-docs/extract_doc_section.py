"""Extract one page's section from output/llms.txt by URL/slug/path.

output/llms.txt concatenates every Kilo Code docs page using this repeating
marker format (confirmed by fetching the live file -- note the Source line
comes BEFORE the title here, the reverse of the more common "# Title /
Source: URL" convention):

    ## Source: /some/page-path

    ---
    title: "..."
    ---

    # <Title>

    <body>

    ---

    ## Source: /next/page-path
    ...

Usage:
    python extract_doc_section.py https://kilo.ai/docs/ai-providers/alibaba
    python extract_doc_section.py ai-providers/alibaba automate/agent-manager
    python extract_doc_section.py ai-providers/alibaba --summarize-threshold 4000 --model glm-5.2
    python extract_doc_section.py ai-providers/alibaba --no-summarize
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent
DEFAULT_INPUT = SKILL_DIR / "output" / "llms.txt"
DEFAULT_BASE_URL = "https://kilo.ai/docs/"

DEFAULT_OUTPUT_DIR = SKILL_DIR / "output" / "temp"

# Kilo docs pages vary a lot in size (roughly 400 to 37,000 chars in the
# snapshot this skill was built from), unlike some doc sites where every
# page is small -- so the aim-based summarization fallback below is worth
# keeping enabled by default.
DEFAULT_SUMMARIZE_THRESHOLD_CHARS = 6000
DEFAULT_SUMMARIZE_MODEL = "minimax-m3"  # see the aim-cli skill for model choices

# Note the reversed order vs. the more common "# Title\nSource: URL" pattern:
# here "## Source: /path" comes first, then an optional frontmatter block,
# then "# Title". The whole thing (frontmatter + title + body) is captured
# as one blob; the title is pulled out of it separately below.
SECTION_RE = re.compile(
    r"^## Source: (?P<path>/\S+)\n\n(?P<blob>.*?)(?=\n\n+---\n\n## Source: /\S+\n|\Z)",
    re.DOTALL | re.MULTILINE,
)
TITLE_RE = re.compile(r"^# (?P<title>.+)$", re.MULTILINE)

SUMMARIZE_PROMPT_TEMPLATE = (
    "Summarize the following documentation page for a developer who needs to "
    "act on it. Preserve concrete facts: code samples, commands, config keys, "
    "parameter names/types, defaults, and caveats/warnings. Omit marketing "
    "language and repetition. Do not invent information that isn't in the "
    "source.\n\n# {title}\nSource: {source}\n\n{body}"
)


def parse_sections(text: str, base_url: str) -> dict[str, tuple[str, str, str]]:
    """resolved URL -> (title, source, body)."""
    root = base_url.rstrip("/")
    sections: dict[str, tuple[str, str, str]] = {}
    for match in SECTION_RE.finditer(text):
        path = match.group("path").strip()
        blob = match.group("blob").strip()
        title_match = TITLE_RE.search(blob)
        title = title_match.group("title").strip() if title_match else path
        source = root + path
        sections[source] = (title, source, blob)
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
    segment -- several Kilo doc sections share a leaf name (e.g.
    troubleshooting) across unrelated subdirectories."""
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
        help="Target URL(s), path(s), or slug(s), e.g. 'ai-providers/alibaba'",
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help="output/llms.txt-style file to read (default: %(default)s)",
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
