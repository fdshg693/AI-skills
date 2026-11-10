"""Cached, selective reference access for the Claude Agent SDK docs.

The Claude Code docs site publishes a small llms.txt index and individual
Markdown pages.  This CLI caches the index and only downloads pages explicitly
requested by slug, avoiding the multi-megabyte llms-full.txt dump.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

SKILL_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = SKILL_DIR / "output"
INDEX_PATH = OUTPUT_DIR / "llms.txt"
PAGES_DIR = OUTPUT_DIR / "pages"

INDEX_URL = "https://code.claude.com/docs/llms.txt"
DOCS_PREFIX = "https://code.claude.com/docs/en/"
FRESHNESS = timedelta(days=1)
REQUEST_TIMEOUT_SECONDS = 30
FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
INDEX_LINK_RE = re.compile(
    r"\[(?P<title>[^\]]+)\]\((?P<url>https://code\.claude\.com/docs/en/agent-sdk/[^)\s]+)\)"
)


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


def is_fresh(path: Path) -> bool:
    fetched_at = read_fetched_at(path)
    return fetched_at is not None and datetime.now(timezone.utc) - fetched_at < FRESHNESS


def cached_body(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(text)
    return text[match.end() :] if match else text


def fetch(url: str) -> str:
    request = Request(url, headers={"User-Agent": "claude-agent-sdk-skill/1.0"})
    try:
        with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            return response.read().decode("utf-8")
    except (HTTPError, URLError, TimeoutError) as exc:
        if "CERTIFICATE_VERIFY_FAILED" in str(exc):
            curl = shutil.which("curl")
            if curl:
                try:
                    result = subprocess.run(
                        [
                            curl,
                            "--fail",
                            "--location",
                            "--silent",
                            "--show-error",
                            "--max-time",
                            str(REQUEST_TIMEOUT_SECONDS),
                            url,
                        ],
                        capture_output=True,
                        check=True,
                        timeout=REQUEST_TIMEOUT_SECONDS + 5,
                    )
                    return result.stdout.decode("utf-8")
                except (
                    OSError,
                    subprocess.CalledProcessError,
                    subprocess.TimeoutExpired,
                ) as curl_exc:
                    raise RuntimeError(
                        f"failed to fetch {url}: {exc}; curl fallback: {curl_exc}"
                    ) from exc
        raise RuntimeError(f"failed to fetch {url}: {exc}") from exc


def write_cache(path: Path, url: str, body: str) -> None:
    fetched_at = datetime.now(timezone.utc).isoformat()
    content = f"---\nsource: {url}\nfetched_at: {fetched_at}\n---\n\n{body}"
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(content, encoding="utf-8")
    temporary.replace(path)


def ensure_cached(path: Path, url: str, force: bool) -> str:
    if not force and is_fresh(path):
        print(f"SKIP {path.relative_to(SKILL_DIR)} (fresh cache)")
        return cached_body(path)

    try:
        body = fetch(url)
    except RuntimeError:
        if path.is_file():
            print(
                f"WARNING: using stale cache {path.relative_to(SKILL_DIR)}",
                file=sys.stderr,
            )
            return cached_body(path)
        raise

    write_cache(path, url, body)
    print(f"WROTE {path.relative_to(SKILL_DIR)}")
    return body


def slug_from_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.netloc != "code.claude.com":
        raise ValueError(f"unsupported docs URL: {url}")
    path = parsed.path
    prefix = "/docs/en/"
    if not path.startswith(prefix):
        raise ValueError(f"unsupported docs URL: {url}")
    slug = path[len(prefix) :].strip("/")
    if slug.endswith(".md"):
        slug = slug[:-3]
    if not slug.startswith("agent-sdk/"):
        raise ValueError(f"URL is outside agent-sdk/: {url}")
    parts = slug.split("/")
    if any(
        not part or part in {".", ".."} or not re.fullmatch(r"[A-Za-z0-9_-]+", part)
        for part in parts
    ):
        raise ValueError(f"invalid page slug: {slug}")
    return slug


def url_from_slug(raw_slug: str) -> str:
    if raw_slug.startswith(("http://", "https://")):
        return raw_slug
    slug = raw_slug.strip("/")
    if not slug.startswith("agent-sdk/"):
        slug = f"agent-sdk/{slug}"
    return f"{DOCS_PREFIX}{slug}.md"


def index_entries(index_text: str) -> dict[str, tuple[str, str]]:
    entries: dict[str, tuple[str, str]] = {}
    for match in INDEX_LINK_RE.finditer(index_text):
        url = match.group("url")
        entries[slug_from_url(url)] = (match.group("title").strip(), url)
    return entries


def get_index(force: bool) -> dict[str, tuple[str, str]]:
    body = ensure_cached(INDEX_PATH, INDEX_URL, force)
    entries = index_entries(body)
    if not entries:
        raise RuntimeError("the cached llms.txt contains no agent-sdk pages")
    return entries


def page_path(slug: str) -> Path:
    return PAGES_DIR / f"{slug}.md"


def command_index(args: argparse.Namespace) -> int:
    entries = get_index(args.force)
    print(f"{len(entries)} Agent SDK pages in the cached index:")
    for slug, (title, url) in entries.items():
        print(f"- {slug}: {title} ({url})")
    return 0


def command_download(args: argparse.Namespace) -> int:
    entries = get_index(args.force)
    if args.all:
        slugs = list(entries)
    else:
        slugs = args.slug
        if not slugs:
            raise SystemExit("download requires --slug ... or --all")

    for raw_slug in slugs:
        url = url_from_slug(raw_slug)
        slug = slug_from_url(url)
        title, indexed_url = entries.get(slug, (slug, url))
        if indexed_url != url and raw_slug.startswith(("http://", "https://")):
            url = indexed_url
        print(f"Fetching {slug}: {title}")
        ensure_cached(page_path(slug), url, args.force)
    return 0


def iter_page_files(slugs: list[str] | None) -> list[Path]:
    if slugs:
        return [page_path(slug_from_url(url_from_slug(slug))) for slug in slugs]
    return sorted(PAGES_DIR.glob("agent-sdk/*.md"))


def command_grep(args: argparse.Namespace) -> int:
    flags = re.IGNORECASE if args.ignore_case else 0
    pattern_text = re.escape(args.pattern) if args.fixed_strings else args.pattern
    try:
        pattern = re.compile(pattern_text, flags)
    except re.error as exc:
        raise SystemExit(f"invalid regex: {exc} (use --fixed-strings for literals)")

    files = iter_page_files(args.slug)
    matches = 0
    for path in files:
        if not path.is_file():
            continue
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        body_start = 0
        while body_start < len(lines) and lines[body_start].strip() != "---":
            body_start += 1
        if body_start < len(lines):
            body_start += 1
            while body_start < len(lines) and lines[body_start].strip() != "---":
                body_start += 1
            body_start += 1

        file_matches = [i for i in range(body_start, len(lines)) if pattern.search(lines[i])]
        if not file_matches:
            continue

        source = "unknown"
        for line in lines[:body_start]:
            if line.startswith("source:"):
                source = line.partition(":")[2].strip()
                break
        print(f"\n== {path.relative_to(SKILL_DIR)} ({source}) ==")
        for line_number in file_matches:
            matches += 1
            start = max(body_start, line_number - args.context)
            end = min(len(lines), line_number + args.context + 1)
            for context_line in range(start, end):
                marker = ">" if context_line == line_number else " "
                print(f"{marker}{context_line + 1:>6}: {lines[context_line]}")
            if matches >= args.max_matches:
                print(f"\nStopped after {args.max_matches} matches.")
                return 0

    if matches == 0:
        print(
            "No matches in downloaded pages. Download the relevant slug first; "
            "see reference-map.md for keywords and page choices."
        )
        return 1
    print(f"\n{matches} match(es) shown.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Cache and search only the Claude Agent SDK documentation pages you need."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    index_parser = subparsers.add_parser("index", help="Refresh and list the small SDK URL index.")
    index_parser.add_argument("--force", action="store_true", help="Ignore the 24-hour cache.")
    index_parser.set_defaults(function=command_index)

    download_parser = subparsers.add_parser(
        "download", help="Download selected SDK pages into the per-page cache."
    )
    download_parser.add_argument(
        "--slug",
        action="append",
        default=[],
        help="Page slug, e.g. agent-sdk/python (repeatable; .md and full URLs also work).",
    )
    download_parser.add_argument(
        "--all",
        action="store_true",
        help="Download every page in the index (use sparingly; selection is preferred).",
    )
    download_parser.add_argument("--force", action="store_true", help="Ignore the 24-hour cache.")
    download_parser.set_defaults(function=command_download)

    grep_parser = subparsers.add_parser(
        "grep", help="Search downloaded pages and show each match with its source URL."
    )
    grep_parser.add_argument("pattern", help="Regex pattern, unless --fixed-strings is used.")
    grep_parser.add_argument("--slug", action="append", help="Restrict search to a slug.")
    grep_parser.add_argument("-i", "--ignore-case", action="store_true")
    grep_parser.add_argument("-F", "--fixed-strings", action="store_true")
    grep_parser.add_argument("-C", "--context", type=int, default=2)
    grep_parser.add_argument("--max-matches", type=int, default=100)
    grep_parser.set_defaults(function=command_grep)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    try:
        return args.function(args)
    except (RuntimeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
