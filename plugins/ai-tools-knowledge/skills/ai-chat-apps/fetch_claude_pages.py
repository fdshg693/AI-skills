"""Fetch Claude Help Center articles as Markdown into ``output/temp/``.

Adapted from writing-skill-web's ``scripts/fetch_selected_pages.py``: only
explicit ``--url`` values (no manifest), only ``support.claude.com/en/articles/``,
and the ``.md`` variant of each article is requested (static Markdown, no JS).
ChatGPT and Gemini pages are HTML and are fetched with the web-lookup skill's
``page`` command instead.  Prints one ``<url> -> <file>`` line per page.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

import requests

import download_index as dl
import download_url_index as index

DEFAULT_OUTPUT_DIR = dl.OUTPUT_DIR / "temp"
ALLOWED_HOST = "support.claude.com"
ALLOWED_PREFIX = "https://support.claude.com/en/articles/"
DEFAULT_MAX_PAGES = 10


def to_markdown_url(url: str) -> str:
    canonical = index.validate_url(url, {ALLOWED_HOST}, (ALLOWED_PREFIX,))
    parsed = urlsplit(canonical)
    path = parsed.path.rstrip("/")
    if not path.endswith(".md"):
        path += ".md"
    return f"https://{ALLOWED_HOST}{path}"


def write_page(output_dir: Path, url: str, body: str) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    slug = urlsplit(url).path.rsplit("/", 1)[-1].removesuffix(".md")
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:8]
    path = output_dir / f"claude-{slug[:80]}-{digest}.md"
    fetched_at = datetime.now(timezone.utc).isoformat()
    path.write_text(
        f"---\nsource: {url.removesuffix('.md')}\nfetched_at: {fetched_at}\n---\n\n{body}",
        encoding="utf-8",
        newline="\n",
    )
    return path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "urls", nargs="+", help="support.claude.com/en/articles/... URLs (.md optional)"
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--max-pages", type=int, default=DEFAULT_MAX_PAGES)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if len(args.urls) > args.max_pages:
        print(f"ERROR: {len(args.urls)} URLs; limit is {args.max_pages}", file=sys.stderr)
        return 2
    try:
        md_urls = [to_markdown_url(url) for url in args.urls]
    except index.IndexError_ as exc:
        print(f"ERROR: {exc} (only {ALLOWED_PREFIX}... is supported)", file=sys.stderr)
        return 2
    session = requests.Session()
    session.headers.update(dl.BROWSER_HEADERS)
    failures = 0
    for url in md_urls:
        try:
            body = dl.fetch_text(session, url, ALLOWED_HOST)
            print(f"{url.removesuffix('.md')} -> {write_page(args.output_dir, url, body)}")
        except (index.IndexError_, OSError) as exc:
            failures += 1
            print(f"ERROR: {url}: {exc}", file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
