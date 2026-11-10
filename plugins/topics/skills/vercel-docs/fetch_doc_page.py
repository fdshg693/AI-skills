"""Fetch one or more Vercel docs pages as Markdown.

https://vercel.com serves each docs URL as Markdown when `.md` is appended
(confirmed via https://vercel.com/docs/llms.txt). This is the body-retrieval
path for this skill: the docs' llms-full.txt concatenates pages with
`-----`-fenced metadata (`title:` / `source:`) BEFORE the `# Title` heading, so
it is not the (`# Title` / `Source: URL`) layout that extract_doc_section.py
expects -- appending `.md` to a page URL is simpler and per-page accurate.

Given a sitemap path, a `/docs/...` path, or an absolute URL, this writes the
page to output/temp/<slug>.txt (always) and, when the body exceeds
--summarize-threshold characters, also writes a summary via the `aim` CLI.
The full-text path is printed even when a summary is produced.

Usage:
    python fetch_doc_page.py docs/functions
    python fetch_doc_page.py docs/functions docs/environment-variables
    python fetch_doc_page.py https://vercel.com/docs/functions
    python fetch_doc_page.py docs/functions --no-summarize
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

import requests

SKILL_DIR = Path(__file__).resolve().parent
DEFAULT_BASE_URL = "https://vercel.com/"
DEFAULT_OUTPUT_DIR = SKILL_DIR / "output" / "temp"

# One Vercel docs page can be large; 6000 is the writing-skill-web default that
# keeps one page + prompt inside a typical model context.
DEFAULT_SUMMARIZE_THRESHOLD_CHARS = 6000
DEFAULT_SUMMARIZE_MODEL = "glm-5.3-flash"  # current aim CLI default; see aim-cli skill
DEFAULT_FRESHNESS_DAYS = 1.0
REQUEST_TIMEOUT_SECONDS = 60
FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)

SUMMARIZE_PROMPT_TEMPLATE = (
    "Summarize the following documentation page for a developer who needs to "
    "act on it. Preserve concrete facts: code samples, commands, config keys, "
    "parameter names/types, defaults, and caveats/warnings. Omit marketing "
    "language and repetition. Do not invent information that isn't in the "
    "source.\n\n# {title}\nSource: {source}\n\n{body}"
)


def markdown_url(url_or_slug: str, base_url: str) -> str:
    raw = url_or_slug.strip()
    if raw.startswith("http://") or raw.startswith("https://"):
        url = raw
    else:
        url = base_url.rstrip("/") + "/" + raw.lstrip("/")
    # Drop query/fragment (?from=llms-txt etc.) so appending `.md` stays valid.
    parts = urlsplit(url)
    url = urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))
    if url.endswith(".html"):
        url = url[: -len(".html")]
    if not url.endswith(".md"):
        url = url + ".md"
    return url


def slug_from_url(url: str, base_url: str) -> str:
    """Filename-safe slug that keeps the full path, not just the last segment."""
    rel = url[len(base_url) :] if url.startswith(base_url) else url.rsplit("://", 1)[-1]
    if rel.endswith(".md"):
        rel = rel[: -len(".md")]
    return rel.strip("/").replace("/", "__")


def canonical_source(md_url: str) -> str:
    if md_url.endswith(".md"):
        return md_url[: -len(".md")]
    return md_url


def read_fetched_at(path: Path) -> datetime | None:
    if not path.is_file():
        return None
    match = FRONTMATTER_RE.match(path.read_text(encoding="utf-8"))
    if not match:
        return None
    for line in match.group(1).splitlines():
        key, _, value = line.partition(":")
        if key.strip() == "fetched_at":
            try:
                return datetime.fromisoformat(value.strip())
            except ValueError:
                return None
    return None


def fetch(url: str) -> str:
    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
    except requests.RequestException as exc:
        print(f"ERROR: failed to fetch {url}: {exc}", file=sys.stderr)
        raise SystemExit(1)
    return response.text


def title_from_body(body: str) -> str:
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("title:"):
            return stripped[len("title:") :].strip().strip('"').strip("'")
        if stripped.startswith("# "):
            return stripped[2:].strip().strip("`")
    return "(untitled)"


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
        help="Docs URL(s) or path(s), e.g. 'docs/functions' (trailing .md optional)",
    )
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help="Site origin used to resolve slugs (default: %(default)s)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory to write fetched pages to (default: %(default)s)",
    )
    parser.add_argument(
        "--freshness-days",
        type=float,
        default=DEFAULT_FRESHNESS_DAYS,
        help="Skip re-fetching a page if its cache is younger than this many days (default: %(default)s)",
    )
    parser.add_argument(
        "--force", action="store_true", help="Re-fetch even if a cached page is still fresh"
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

    args.output_dir.mkdir(parents=True, exist_ok=True)

    for raw in args.urls:
        md_url = markdown_url(raw, args.base_url)
        source = canonical_source(md_url)
        slug = slug_from_url(md_url, args.base_url)
        out_path = args.output_dir / f"{slug}.txt"

        if not args.force:
            fetched_at = read_fetched_at(out_path)
            if fetched_at is not None:
                age = datetime.now(timezone.utc) - fetched_at
                if age < timedelta(days=args.freshness_days):
                    print(
                        f"{out_path}: already fresh (fetched at {fetched_at.isoformat()}). Use --force to refetch."
                    )
                    continue

        body = fetch(md_url)
        title = title_from_body(body)
        fetched_at = datetime.now(timezone.utc).isoformat()
        out_path.write_text(
            f"---\nsource: {source}\nfetched_at: {fetched_at}\n---\n\n{body}",
            encoding="utf-8",
        )

        if args.no_summarize or len(body) <= args.summarize_threshold:
            print(f"Wrote {out_path} ({len(body)} chars)\nSource: {source}")
            continue

        print(f"Wrote full text ({len(body)} chars) -> {out_path}")
        print(f"Source: {source}")
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
