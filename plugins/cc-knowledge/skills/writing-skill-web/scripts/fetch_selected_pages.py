"""Fetch only explicitly selected URL-index entries into ``output/temp``.

The manifest produced by ``select_url_index.py`` is intentionally the only
bulk input accepted.  Every URL and redirect is checked against the HTTPS host
allowlist and optional prefix before a response body is written.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

import requests

import download_url_index as index

DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent / "output" / "temp"
DEFAULT_MAX_PAGES = 20
REQUEST_TIMEOUT_SECONDS = 30
MAX_PAGE_BYTES = 4 * 1024 * 1024


def read_manifest(path: Path) -> list[str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    raw_entries = payload.get("entries", []) if isinstance(payload, dict) else payload
    if not isinstance(raw_entries, list):
        raise ValueError("manifest entries must be a list")
    urls: list[str] = []
    seen: set[str] = set()
    for entry in raw_entries:
        raw_url = entry.get("url") if isinstance(entry, dict) else entry
        if not isinstance(raw_url, str):
            raise ValueError("manifest entries must contain string URLs")
        if raw_url not in seen:
            seen.add(raw_url)
            urls.append(raw_url)
    return urls


def _safe_filename(url: str) -> str:
    parsed = urlsplit(url)
    slug = (parsed.path.strip("/") or "index").replace("/", "__")
    if parsed.query:
        slug += "__query"
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:12]
    return f"{slug[:100]}--{digest}.md"


def fetch_page(
    url: str, allowed_hosts: set[str], allowed_prefixes: tuple[str, ...]
) -> tuple[str, str]:
    """Fetch one page and return its final URL and UTF-8 body."""

    checked_url = index.validate_url(url, allowed_hosts, allowed_prefixes)
    current_url = checked_url
    for _ in range(5):  # Bound redirects before following any new URL.
        try:
            response = requests.get(
                current_url, timeout=REQUEST_TIMEOUT_SECONDS, allow_redirects=False
            )
            if 300 <= getattr(response, "status_code", 200) < 400:
                location = (getattr(response, "headers", {}) or {}).get("Location")
                if not location:
                    raise index.IndexError_(f"redirect without Location header: {current_url}")
                current_url = index.validate_url(
                    index.urljoin(current_url, location), allowed_hosts, allowed_prefixes
                )
                continue
            response.raise_for_status()
        except requests.RequestException as exc:
            raise index.IndexError_(f"failed to fetch {current_url}: {exc}") from exc
        final_url = index.validate_url(
            getattr(response, "url", None) or current_url, allowed_hosts, allowed_prefixes
        )
        raw_body = getattr(response, "content", None)
        if raw_body is not None and len(raw_body) > MAX_PAGE_BYTES:
            raise index.IndexError_(f"page exceeds {MAX_PAGE_BYTES} bytes: {final_url}")
        body = response.text
        if len(body.encode("utf-8")) > MAX_PAGE_BYTES:
            raise index.IndexError_(f"page exceeds {MAX_PAGE_BYTES} bytes: {final_url}")
        return final_url, body
    raise index.IndexError_(f"too many redirects: {url}")


def write_page(output_dir: Path, url: str, body: str) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / _safe_filename(url)
    fetched_at = datetime.now(timezone.utc).isoformat()
    text = f"---\nsource: {url}\nfetched_at: {fetched_at}\n---\n\n{body}"
    path.write_text(text, encoding="utf-8")
    return path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--url", action="append", default=[], help="Explicit page URL (repeatable)")
    parser.add_argument("--manifest", type=Path, help="Selection manifest JSON")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--allowed-host", action="append", default=[])
    parser.add_argument("--include-prefix", action="append", default=[])
    parser.add_argument("--max-pages", type=int, default=DEFAULT_MAX_PAGES)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if not args.url and args.manifest is None:
        print("ERROR: provide --url or --manifest", file=sys.stderr)
        return 2
    if args.url and args.manifest is not None:
        print("ERROR: --url and --manifest cannot be combined", file=sys.stderr)
        return 2
    if args.max_pages < 1:
        print("ERROR: --max-pages must be positive", file=sys.stderr)
        return 2
    try:
        urls = list(args.url) if args.url else read_manifest(args.manifest)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: invalid manifest: {exc}", file=sys.stderr)
        return 2
    if len(urls) > args.max_pages:
        print(
            f"ERROR: selection contains {len(urls)} URLs; limit is {args.max_pages}",
            file=sys.stderr,
        )
        return 2
    try:
        canonical_urls = [index.canonicalize_url(url) for url in urls]
        hosts = set(args.allowed_host) or {urlsplit(url).hostname or "" for url in canonical_urls}
        if not canonical_urls:
            print("No URLs selected")
            return 0
        for url in canonical_urls:
            index.validate_url(url, hosts, tuple(args.include_prefix))
    except index.IndexError_ as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    failures = 0
    for url in canonical_urls:
        try:
            final_url, body = fetch_page(url, hosts, tuple(args.include_prefix))
            path = write_page(args.output_dir, final_url, body)
            print(f"Fetched {final_url} -> {path}")
        except (index.IndexError_, OSError) as exc:
            failures += 1
            print(f"ERROR: {url}: {exc}", file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
