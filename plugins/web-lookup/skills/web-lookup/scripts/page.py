"""`page`: fetch a URL locally and keep only the main text as Markdown.

HTTP with `requests` (generic User-Agent, no browser impersonation), main-text
extraction with trafilatura. No JavaScript is run, so JS-rendered values and
login walls are not handled here (page.md tells the agent when to switch to a
browser). A failed URL is reported, never retried through Tavily automatically:
whether a URL may be sent to a third party is the agent's call.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from importlib import metadata

import requests

CONNECT_TIMEOUT = 10.0
READ_TIMEOUT = 30.0
MAX_BYTES = 5 * 1024 * 1024
MIN_CHARS = 200
_CHUNK_SIZE = 64 * 1024

_HTML_TYPES = ("text/html", "application/xhtml+xml")
_CHARSET_PARAM = re.compile(r"charset\s*=\s*[\"']?([\w.:-]+)", re.IGNORECASE)
_META_CHARSET = re.compile(rb"<meta[^>]+charset\s*=", re.IGNORECASE)
_META_SNIFF_BYTES = 4096

_BULLET_BREAK = re.compile(r"^([ \t]*[-*+])[ \t]*\n[ \t]*(?=\S)", re.MULTILINE)
_BLANK_RUNS = re.compile(r"\n[ \t]*(?:\n[ \t]*){2,}")
_TRAILING_SPACE = re.compile(r"[ \t]+$", re.MULTILINE)


def _user_agent() -> str:
    try:
        return f"web-lookup/{metadata.version('web-lookup')}"
    except metadata.PackageNotFoundError:
        return "web-lookup"


REQUEST_HEADERS = {
    "User-Agent": _user_agent(),
    "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ja,en;q=0.8",
}


class PageError(Exception):
    """A URL that produced no usable page. `str(exc)` is the index wording."""


@dataclass(frozen=True)
class PageResult:
    url: str
    title: str = ""
    content: str = ""
    failure: str = ""

    @property
    def ok(self) -> bool:
        return not self.failure


@dataclass(frozen=True)
class Fetched:
    final_url: str
    body: bytes
    charset: str | None


def _charset_of(content_type: str) -> str | None:
    match = _CHARSET_PARAM.search(content_type)
    return match.group(1) if match else None


def fetch(url: str, *, session: requests.Session | None = None) -> Fetched:
    """GET `url` with a size cap; raise PageError with the index wording on failure."""
    getter = session or requests
    try:
        response = getter.get(
            url,
            headers=REQUEST_HEADERS,
            timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
            stream=True,
            allow_redirects=True,
        )
    except requests.Timeout as exc:
        raise PageError("failed (timeout)") from exc
    except requests.ConnectionError as exc:
        raise PageError("failed (connection error)") from exc
    except requests.RequestException as exc:
        raise PageError(f"failed ({type(exc).__name__})") from exc

    with response:
        if not 200 <= response.status_code < 300:
            raise PageError(f"failed (HTTP {response.status_code})")
        content_type = response.headers.get("Content-Type", "")
        media_type = content_type.split(";", 1)[0].strip().lower()
        if media_type and media_type not in _HTML_TYPES:
            raise PageError(f"failed (content-type {media_type})")

        chunks: list[bytes] = []
        size = 0
        try:
            for chunk in response.iter_content(_CHUNK_SIZE):
                size += len(chunk)
                if size > MAX_BYTES:
                    raise PageError("failed (too large)")
                chunks.append(chunk)
        except requests.Timeout as exc:
            raise PageError("failed (timeout)") from exc
        except requests.RequestException as exc:
            raise PageError(f"failed ({type(exc).__name__})") from exc

    return Fetched(response.url or url, b"".join(chunks), _charset_of(content_type))


def _parse(body: bytes, header_charset: str | None):
    """Parse bytes, never `response.text` (requests guesses ISO-8859-1 without a charset)."""
    import lxml.html

    encoding = None
    if not _META_CHARSET.search(body[:_META_SNIFF_BYTES]):
        if header_charset:
            encoding = header_charset
        else:
            try:
                body.decode("utf-8")
                encoding = "utf-8"
            except UnicodeDecodeError:
                encoding = None  # let libxml2 guess
    parser = lxml.html.HTMLParser(encoding=encoding) if encoding else None
    try:
        return lxml.html.fromstring(body, parser=parser)
    except LookupError:  # unknown charset name in the header
        return lxml.html.fromstring(body)


def flatten_lists_in_table_cells(tree) -> None:
    """Replace each list inside `td`/`th` with its items joined by ` / `.

    trafilatura drops lists inside table cells (the cell comes out empty).
    """
    import lxml.html

    def _is_outermost(node, cell) -> bool:
        for ancestor in node.iterancestors():
            if ancestor is cell:
                return True
            if ancestor.tag in ("ul", "ol"):
                return False
        return True

    for cell in list(tree.iter("td", "th")):
        outermost = [node for node in cell.iter("ul", "ol") if _is_outermost(node, cell)]
        for node in outermost:
            items = [" ".join(li.text_content().split()) for li in node.iter("li")]
            items = [item for item in items if item]
            replacement = lxml.html.Element("span")
            replacement.text = " / ".join(items)
            replacement.tail = node.tail
            node.getparent().replace(node, replacement)


def normalize_whitespace(markdown: str) -> str:
    text = _TRAILING_SPACE.sub("", markdown)
    text = _BULLET_BREAK.sub(r"\1 ", text)
    text = _BLANK_RUNS.sub("\n\n", text)
    return text.strip()


def _title_of(tree, final_url: str) -> str:
    import trafilatura

    title = ""
    try:
        meta = trafilatura.extract_metadata(tree, default_url=final_url)
        title = (meta.title or "") if meta else ""
    except Exception:  # metadata is best effort
        title = ""
    if not title.strip():
        title = tree.findtext(".//title") or ""
    title = " ".join(title.split())
    return title or final_url


def extract(body: bytes, final_url: str, *, charset: str | None = None) -> tuple[str, str]:
    """Return `(title, markdown body)` from HTML bytes. The body may be empty."""
    import trafilatura

    tree = _parse(body, charset)
    title = _title_of(tree, final_url)
    flatten_lists_in_table_cells(tree)
    markdown = trafilatura.extract(
        tree,
        url=final_url,
        output_format="markdown",
        include_tables=True,
        include_links=False,
        include_images=False,
        include_comments=False,
        favor_recall=True,
    )
    return title, normalize_whitespace(markdown or "")


def fetch_page(url: str, *, session: requests.Session | None = None) -> PageResult:
    try:
        fetched = fetch(url, session=session)
        title, markdown = extract(fetched.body, fetched.final_url, charset=fetched.charset)
    except PageError as exc:
        return PageResult(url=url, failure=str(exc))
    except Exception as exc:  # unparsable HTML must not abort the other URLs
        return PageResult(url=url, failure=f"failed (extract error: {type(exc).__name__})")
    if len(markdown) < MIN_CHARS:
        return PageResult(url=url, failure=f"too short ({len(markdown)} chars)")
    content = f"# {title}\n\nURL: {fetched.final_url}\n\n{markdown}\n"
    return PageResult(url=url, title=title, content=content)


def fetch_pages(urls: Iterable[str]) -> list[PageResult]:
    with requests.Session() as session:
        return [fetch_page(url, session=session) for url in urls]
