"""Download the help-center article index for one source (``claude`` or ``chatgpt``).

Writes ``output/<source>-index.md``: a frontmatter block with ``fetched_at``
followed by ``- [title](url): [section] description`` lines grouped under
``## <section>`` headings.  The file is skipped when it is younger than the
source's freshness window (``--force`` refetches).

Sources (see README.md for why each one is fetched this way):

- ``claude``: ``https://support.claude.com/llms.txt``, ``## English`` part only.
  Each article's ``lastmod`` is joined from ``/sitemap.xml`` by article id.
  If the sitemap fails, the index is still written without ``lastmod``.
- ``chatgpt``: help.openai.com has no sitemap or llms.txt, so the server-
  rendered ``/en/collections/<id>`` pages are crawled one at a time with a
  1 second delay (robots.txt ``Crawl-delay: 1``).

Gemini Apps Help is deliberately not a source here (Google rate-limits bulk
fetching).  The skill keeps its article ids in ``gemini.md`` instead.
"""

from __future__ import annotations

import argparse
import re
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlsplit

import requests

import download_url_index as index

SKILL_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = SKILL_DIR / "output"
REQUEST_TIMEOUT_SECONDS = 30
# help.openai.com answers 403 to the default python-requests User-Agent.
BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/130.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}
MAX_DOCUMENT_BYTES = 16 * 1024 * 1024  # the Claude sitemap is ~10 MB
ARTICLE_ID_RE = re.compile(r"/articles/(\d+)")


@dataclass(frozen=True)
class Source:
    name: str
    title: str
    index_url: str
    allowed_host: str
    freshness_days: float

    @property
    def output(self) -> Path:
        return OUTPUT_DIR / f"{self.name}-index.md"


SOURCES: dict[str, Source] = {
    "claude": Source(
        name="claude",
        title="Claude Help Center (support.claude.com, English)",
        index_url="https://support.claude.com/llms.txt",
        allowed_host="support.claude.com",
        freshness_days=3.0,
    ),
    "chatgpt": Source(
        name="chatgpt",
        title="OpenAI Help Center (help.openai.com/en)",
        index_url="https://help.openai.com/en",
        allowed_host="help.openai.com",
        freshness_days=3.0,
    ),
}


@dataclass
class Article:
    url: str
    title: str
    description: str = ""
    section: str = ""
    lastmod: str = ""


# --------------------------------------------------------------------------- fetch


def fetch_text(session: requests.Session, url: str, allowed_host: str) -> str:
    """GET one document, re-validating every redirect against the host allowlist."""

    current = index.validate_url(url, {allowed_host})
    for _ in range(5):
        try:
            response = session.get(current, timeout=REQUEST_TIMEOUT_SECONDS, allow_redirects=False)
        except requests.RequestException as exc:
            raise index.IndexError_(f"failed to fetch {current}: {exc}") from exc
        if 300 <= response.status_code < 400:
            location = response.headers.get("Location")
            if not location:
                raise index.IndexError_(f"redirect without Location header: {current}")
            current = index.validate_url(urljoin(current, location), {allowed_host})
            continue
        if response.status_code != 200:
            raise index.IndexError_(f"HTTP {response.status_code} for {current}")
        if len(response.content) > MAX_DOCUMENT_BYTES:
            raise index.IndexError_(f"document exceeds {MAX_DOCUMENT_BYTES} bytes: {current}")
        response.encoding = response.encoding or "utf-8"
        return response.text
    raise index.IndexError_(f"too many redirects: {url}")


# --------------------------------------------------------------------------- claude

LLMS_LINK_RE = re.compile(r"^\s*-\s*\[((?:[^\]\\]|\\.)+)\]\((https://[^)\s]+)\)\s*(?::\s*(.*))?$")


def parse_claude_llms(body: str) -> list[Article]:
    """Keep only the ``## English`` part; ``### <product>`` headings become sections."""

    articles: list[Article] = []
    seen: set[str] = set()
    in_english = False
    section = ""
    for line in body.splitlines():
        if line.startswith("## "):
            in_english = line[3:].strip() == "English"
            continue
        if not in_english:
            continue
        if line.startswith("### "):
            section = line[4:].strip()
            continue
        match = LLMS_LINK_RE.match(line)
        if not match:
            continue
        title = re.sub(r"\\(.)", r"\1", match.group(1)).strip()
        url = match.group(2)
        if url.endswith(".md"):
            url = url[: -len(".md")]  # cite the HTML page; fetch appends .md again
        url = index.validate_url(url, {"support.claude.com"}, ("https://support.claude.com/en/",))
        if url in seen:
            continue
        seen.add(url)
        articles.append(Article(url, title, (match.group(3) or "").strip(), section))
    return articles


SITEMAP_URL_RE = re.compile(
    r"<loc>\s*(https://support\.claude\.com/en/articles/[^<\s]+)\s*</loc>\s*"
    r"<lastmod>\s*([^<\s]+)\s*</lastmod>"
)


def parse_claude_lastmod(sitemap: str) -> dict[str, str]:
    """Map article id -> lastmod date (YYYY-MM-DD) for English articles."""

    if re.search(r"<!DOCTYPE|<!ENTITY", sitemap, flags=re.IGNORECASE):
        raise index.IndexError_("DTD and entity declarations are not allowed")
    result: dict[str, str] = {}
    for loc, lastmod in SITEMAP_URL_RE.findall(sitemap):
        match = ARTICLE_ID_RE.search(loc)
        if match:
            result[match.group(1)] = lastmod[:10]
    return result


def download_claude(session: requests.Session, source: Source) -> list[Article]:
    articles = parse_claude_llms(fetch_text(session, source.index_url, source.allowed_host))
    if not articles:
        raise index.IndexError_("no '## English' entries found in llms.txt")
    try:
        sitemap = fetch_text(session, "https://support.claude.com/sitemap.xml", source.allowed_host)
        lastmods = parse_claude_lastmod(sitemap)
    except index.IndexError_ as exc:
        print(f"WARNING: lastmod skipped ({exc})", file=sys.stderr)
        lastmods = {}
    for article in articles:
        match = ARTICLE_ID_RE.search(article.url)
        if match:
            article.lastmod = lastmods.get(match.group(1), "")
    return articles


# --------------------------------------------------------------------------- chatgpt

OPENAI_ROOT = "https://help.openai.com/en"
OPENAI_PREFIX = "https://help.openai.com/en/"
COLLECTION_RE = re.compile(r"^/en/collections/(\d+)[^/?#]*$")
ARTICLE_RE = re.compile(r"^/en/articles/(\d+)[^/?#]*$")


@dataclass
class _Link:
    href: str
    texts: list[str] = field(default_factory=list)


class CollectionPageParser(HTMLParser):
    """Collect the page ``<h1>`` and every collection/article link with its text chunks.

    Article cards render as ``<a><span>title</span><span>description</span></a>``,
    so the first non-empty text chunk is the title and the second the description.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.h1 = ""
        self.links: list[_Link] = []
        self._in_h1 = False
        self._current: _Link | None = None
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"svg", "script", "style"}:
            self._skip_depth += 1
        elif tag == "h1" and not self.h1:
            self._in_h1 = True
        elif tag == "a":
            href = dict(attrs).get("href") or ""
            path = urlsplit(urljoin(OPENAI_ROOT, href)).path
            if COLLECTION_RE.match(path) or ARTICLE_RE.match(path):
                self._current = _Link(path)

    def handle_endtag(self, tag: str) -> None:
        if tag in {"svg", "script", "style"} and self._skip_depth:
            self._skip_depth -= 1
        elif tag == "h1":
            self._in_h1 = False
        elif tag == "a" and self._current is not None:
            self.links.append(self._current)
            self._current = None

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        text = " ".join(data.split())
        if not text:
            return
        if self._in_h1:
            self.h1 = f"{self.h1} {text}".strip()
        if self._current is not None:
            self._current.texts.append(text)


def download_chatgpt(
    session: requests.Session,
    source: Source,
    delay_seconds: float = 1.0,
    max_pages: int = 300,
) -> list[Article]:
    articles: dict[str, Article] = {}
    depths: dict[str, int] = {}
    # (url, section path) -- the root page has no section of its own.
    pending: list[tuple[str, tuple[str, ...]]] = [(OPENAI_ROOT, ())]
    seen_collections: set[str] = set()
    fetched = 0
    while pending:
        url, parents = pending.pop(0)
        if fetched >= max_pages:
            raise index.IndexError_(f"collection page limit exceeded: {max_pages}")
        if fetched:
            time.sleep(delay_seconds)
        fetched += 1
        parser = CollectionPageParser()
        parser.feed(fetch_text(session, url, source.allowed_host))
        is_root = url == OPENAI_ROOT
        section = parents if is_root else (*parents, parser.h1 or "?")
        for link in parser.links:
            if match := COLLECTION_RE.match(link.href):
                if match.group(1) in seen_collections:
                    continue
                seen_collections.add(match.group(1))
                pending.append((urljoin(OPENAI_ROOT, link.href), section))
                continue
            match = ARTICLE_RE.match(link.href)
            if not match or is_root:
                continue
            article_id = match.group(1)
            title = link.texts[0] if link.texts else link.href
            description = link.texts[1] if len(link.texts) > 1 else ""
            # Keep the deepest collection that lists the article (most specific section).
            if article_id in articles and depths[article_id] >= len(section):
                continue
            article_url = index.validate_url(
                urljoin(OPENAI_ROOT, link.href), {source.allowed_host}, (OPENAI_PREFIX,)
            )
            articles[article_id] = Article(article_url, title, description, " > ".join(section))
            depths[article_id] = len(section)
    if not articles:
        raise index.IndexError_("no articles found; the help-center markup may have changed")
    return list(articles.values())


# --------------------------------------------------------------------------- output


def _escape(text: str) -> str:
    return text.replace("[", "\\[").replace("]", "\\]")


def format_index(source: Source, articles: list[Article], fetched_at: str) -> str:
    generated_at = datetime.now(timezone.utc).isoformat()
    lines = [
        "---",
        f"source: {source.index_url}",
        f"fetched_at: {fetched_at}",
        f"generated_at: {generated_at}",
        f"articles: {len(articles)}",
        "---",
        "",
        f"# {source.title}",
        "",
    ]
    by_section: dict[str, list[Article]] = {}
    for article in articles:
        by_section.setdefault(article.section or "(no section)", []).append(article)
    for section in sorted(by_section):
        lines += [f"## {section}", ""]
        for article in sorted(by_section[section], key=lambda item: item.title.casefold()):
            suffix = f": {article.description}" if article.description else ""
            if article.lastmod:
                suffix += f" (lastmod: {article.lastmod})"
            lines.append(f"- [{_escape(article.title)}]({article.url}){suffix}")
        lines.append("")
    return "\n".join(lines)


def is_fresh(source: Source, freshness_days: float | None = None) -> bool:
    fetched_at = index.read_fetched_at(source.output)
    days = source.freshness_days if freshness_days is None else freshness_days
    return fetched_at is not None and datetime.now(timezone.utc) - fetched_at < timedelta(days=days)


def download(source: Source, force: bool = False, freshness_days: float | None = None) -> int:
    if not force and is_fresh(source, freshness_days):
        fetched_at = index.read_fetched_at(source.output)
        print(f"{source.name}: fresh (fetched_at {fetched_at.isoformat()}); --force to refetch")
        return 0
    session = requests.Session()
    session.headers.update(BROWSER_HEADERS)
    try:
        if source.name == "claude":
            articles = download_claude(session, source)
        else:
            print(f"{source.name}: crawling collections (about 1 minute)...", file=sys.stderr)
            articles = download_chatgpt(session, source)
    except index.IndexError_ as exc:
        print(f"ERROR: {source.name}: {exc}", file=sys.stderr)
        if source.output.is_file():
            print(f"Keeping the previous snapshot: {source.output}", file=sys.stderr)
        return 1
    fetched_at = datetime.now(timezone.utc).isoformat()
    source.output.parent.mkdir(parents=True, exist_ok=True)
    source.output.write_text(
        format_index(source, articles, fetched_at), encoding="utf-8", newline="\n"
    )
    print(f"{source.name}: wrote {source.output} ({len(articles)} articles)")
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("source", choices=[*SOURCES, "all"], help="Which help center to index")
    parser.add_argument("--force", action="store_true", help="Refetch even when the index is fresh")
    parser.add_argument(
        "--freshness-days",
        type=float,
        default=None,
        help="Override the source's freshness window (claude/chatgpt: 3 days)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    names = list(SOURCES) if args.source == "all" else [args.source]
    return max(download(SOURCES[name], args.force, args.freshness_days) for name in names)


if __name__ == "__main__":
    raise SystemExit(main())
