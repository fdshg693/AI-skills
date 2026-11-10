"""Download and normalize an XML sitemap or ``llms.txt`` URL index.

This is a copy-and-adapt template.  It keeps the complete normalized URL list
and a compact path tree as separate Markdown artifacts so callers can grep the
list without injecting it all into context.  Only HTTPS URLs on the explicit
allowlist are fetched; the source host is used when no allowlist is supplied.
"""

from __future__ import annotations

import argparse
import ipaddress
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urljoin, urlsplit, urlunsplit
from xml.etree import ElementTree

import requests

DEFAULT_URL = "https://example.com/sitemap.xml"
DEFAULT_OUTPUT = Path(__file__).resolve().parent / "output" / "urls.md"
DEFAULT_TREE_OUTPUT = Path(__file__).resolve().parent / "output" / "url-tree.md"
DEFAULT_FRESHNESS_DAYS = 1.0
REQUEST_TIMEOUT_SECONDS = 30
MAX_DOCUMENT_BYTES = 8 * 1024 * 1024
MAX_DOCUMENTS = 100
MAX_SITEMAP_DEPTH = 3
MAX_ENTRIES = 100_000
FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
MARKDOWN_LINK_RE = re.compile(r"\[([^\]]+)\]\((https?://[^)\s]+)\)")
PLAIN_URL_RE = re.compile(r"https://[^\s<>\])}\\\"']+")
TRAILING_PUNCTUATION = ".,;:!?)]}>'\""


@dataclass(frozen=True)
class UrlEntry:
    url: str
    title: str
    description: str = ""
    lastmod: str = ""


class IndexError_(ValueError):
    """Raised for malformed or unsafe index input."""


def canonicalize_url(raw_url: str, base_url: str | None = None) -> str:
    """Return a fragment-free canonical HTTPS URL, or raise ``IndexError_``."""

    value = urljoin(base_url, raw_url.strip()) if base_url else raw_url.strip()
    parsed = urlsplit(value)
    if parsed.scheme.lower() != "https" or not parsed.hostname:
        raise IndexError_(f"only HTTPS URLs are allowed: {raw_url}")
    if parsed.username or parsed.password:
        raise IndexError_(f"credentials are not allowed in URLs: {raw_url}")
    try:
        port = parsed.port
    except ValueError as exc:
        raise IndexError_(f"invalid port in URL: {raw_url}") from exc
    hostname = parsed.hostname.lower().rstrip(".")
    host_for_netloc = f"[{hostname}]" if ":" in hostname else hostname
    if port == 443:
        netloc = host_for_netloc
    elif port is None:
        netloc = host_for_netloc
    else:
        netloc = f"{host_for_netloc}:{port}"
    path = parsed.path or "/"
    return urlunsplit(("https", netloc, path, parsed.query, ""))


def _is_private_host(hostname: str) -> bool:
    lowered = hostname.lower().rstrip(".")
    if lowered in {"localhost", "localhost.localdomain", "ip6-localhost"}:
        return True
    try:
        address = ipaddress.ip_address(lowered)
    except ValueError:
        return False
    return (
        address.is_private
        or address.is_loopback
        or address.is_link_local
        or address.is_reserved
        or address.is_unspecified
    )


def validate_url(url: str, allowed_hosts: set[str], allowed_prefixes: tuple[str, ...] = ()) -> str:
    canonical = canonicalize_url(url)
    parsed = urlsplit(canonical)
    host = parsed.hostname or ""
    normalized_hosts = {item.lower().rstrip(".") for item in allowed_hosts}
    if _is_private_host(host):
        raise IndexError_(f"private, loopback, or link-local host is not allowed: {url}")
    if normalized_hosts and host not in normalized_hosts:
        raise IndexError_(f"host is outside the allowlist: {url}")
    if allowed_prefixes and not any(canonical.startswith(prefix) for prefix in allowed_prefixes):
        raise IndexError_(f"URL is outside the allowed prefix: {url}")
    return canonical


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower()


def _text(element: ElementTree.Element | None) -> str:
    return (element.text or "").strip() if element is not None else ""


def _title_from_url(url: str) -> str:
    path = urlsplit(url).path.rstrip("/")
    segment = path.rsplit("/", 1)[-1] or urlsplit(url).hostname or url
    return re.sub(r"[-_]+", " ", segment).strip().title() or url


def parse_sitemap_xml(body: str, source_url: str) -> tuple[str, list[str | UrlEntry]]:
    """Parse a sitemap document and return ``(kind, children_or_entries)``."""

    if re.search(r"<!DOCTYPE|<!ENTITY", body, flags=re.IGNORECASE):
        raise IndexError_("DTD and entity declarations are not allowed")
    try:
        root = ElementTree.fromstring(body)
    except ElementTree.ParseError as exc:
        raise IndexError_(f"malformed sitemap XML: {exc}") from exc
    root_name = _local_name(root.tag)
    if root_name == "sitemapindex":
        children: list[str | UrlEntry] = []
        for sitemap in root:
            if _local_name(sitemap.tag) != "sitemap":
                continue
            loc = _text(next((node for node in sitemap if _local_name(node.tag) == "loc"), None))
            if loc:
                children.append(urljoin(source_url, loc))
        return "index", children
    if root_name != "urlset":
        raise IndexError_(f"unsupported sitemap root: {root_name}")
    entries: list[str | UrlEntry] = []
    seen_urls: set[str] = set()
    for item in root:
        if _local_name(item.tag) != "url":
            continue
        loc = _text(next((node for node in item if _local_name(node.tag) == "loc"), None))
        if not loc:
            continue
        lastmod = _text(next((node for node in item if _local_name(node.tag) == "lastmod"), None))
        canonical = canonicalize_url(urljoin(source_url, loc))
        if canonical in seen_urls:
            continue
        seen_urls.add(canonical)
        entries.append(UrlEntry(canonical, _title_from_url(loc), lastmod=lastmod))
    return "urlset", entries


def _description_from_line(line: str, match_end: int) -> str:
    description = line[match_end:].strip()
    description = re.sub(r"^\s*[:\-|]+\s*", "", description)
    return description


def parse_llms_text(body: str, source_url: str) -> list[UrlEntry]:
    """Parse Markdown links and plain HTTPS URLs from an ``llms.txt`` body."""

    entries: list[UrlEntry] = []
    seen: set[str] = set()
    in_frontmatter = False
    for line in body.splitlines():
        if line.strip() == "---":
            in_frontmatter = not in_frontmatter
            continue
        if in_frontmatter:
            continue
        matches = list(MARKDOWN_LINK_RE.finditer(line))
        if not matches:
            matches = list(PLAIN_URL_RE.finditer(line))
        for match in matches:
            raw_url = match.group(2) if match.lastindex else match.group(0)
            raw_url = raw_url.rstrip(TRAILING_PUNCTUATION)
            try:
                url = canonicalize_url(urljoin(source_url, raw_url))
            except IndexError_:
                continue
            if url in seen:
                continue
            seen.add(url)
            title = match.group(1).strip() if match.lastindex else _title_from_url(url)
            description = _description_from_line(line, match.end())
            entries.append(UrlEntry(url, title or _title_from_url(url), description))
    return entries


def _is_xml(body: str, source_url: str) -> bool:
    return urlsplit(source_url).path.lower().endswith(
        (".xml", ".xml.gz")
    ) or body.lstrip().startswith("<")


def parse_index(body: str, source_url: str) -> tuple[list[UrlEntry], list[str]]:
    """Parse one document into entries and child sitemap URLs."""

    if _is_xml(body, source_url):
        kind, values = parse_sitemap_xml(body, source_url)
        if kind == "index":
            return [], [str(value) for value in values]
        return [value for value in values if isinstance(value, UrlEntry)], []
    return parse_llms_text(body, source_url), []


def _fetch_document(url: str, allowed_hosts: set[str]) -> tuple[str, str]:
    current_url = url
    for _ in range(5):  # Bound redirects so an index cannot create an unbounded chain.
        try:
            response = requests.get(
                current_url, timeout=REQUEST_TIMEOUT_SECONDS, allow_redirects=False
            )
            if 300 <= getattr(response, "status_code", 200) < 400:
                location = (getattr(response, "headers", {}) or {}).get("Location")
                if not location:
                    raise IndexError_(f"redirect without Location header: {current_url}")
                current_url = validate_url(urljoin(current_url, location), allowed_hosts)
                continue
            response.raise_for_status()
        except requests.RequestException as exc:
            raise IndexError_(f"failed to fetch {current_url}: {exc}") from exc
        final_url = validate_url(getattr(response, "url", None) or current_url, allowed_hosts)
        body_bytes = getattr(response, "content", None)
        if body_bytes is not None and len(body_bytes) > MAX_DOCUMENT_BYTES:
            raise IndexError_(f"index document exceeds {MAX_DOCUMENT_BYTES} bytes: {final_url}")
        body = response.text
        if len(body.encode("utf-8")) > MAX_DOCUMENT_BYTES:
            raise IndexError_(f"index document exceeds {MAX_DOCUMENT_BYTES} bytes: {final_url}")
        return final_url, body
    raise IndexError_(f"too many redirects: {url}")


def download_entries(
    source_url: str,
    allowed_hosts: set[str] | None = None,
    include_prefixes: tuple[str, ...] = (),
    max_documents: int = MAX_DOCUMENTS,
    max_depth: int = MAX_SITEMAP_DEPTH,
) -> list[UrlEntry]:
    """Fetch and recursively normalize a source index with bounded traversal."""

    source = canonicalize_url(source_url)
    hosts = allowed_hosts or {urlsplit(source).hostname or ""}
    entries: list[UrlEntry] = []
    seen_documents: set[str] = set()
    seen_urls: set[str] = set()
    pending: list[tuple[str, int]] = [(source, 0)]
    while pending:
        document_url, depth = pending.pop(0)
        document_url = validate_url(document_url, hosts)
        if document_url in seen_documents:
            continue
        if len(seen_documents) >= max_documents:
            raise IndexError_(f"sitemap document limit exceeded: {max_documents}")
        if depth > max_depth:
            raise IndexError_(f"sitemap nesting depth exceeded: {max_depth}")
        seen_documents.add(document_url)
        final_url, body = _fetch_document(document_url, hosts)
        parsed_entries, children = parse_index(body, final_url)
        for child in children:
            pending.append((validate_url(child, hosts), depth + 1))
        for entry in parsed_entries:
            url = validate_url(entry.url, hosts, include_prefixes)
            if url in seen_urls:
                continue
            seen_urls.add(url)
            entries.append(UrlEntry(url, entry.title, entry.description, entry.lastmod))
            if len(entries) > MAX_ENTRIES:
                raise IndexError_(f"normalized entry limit exceeded: {MAX_ENTRIES}")
    return sorted(entries, key=lambda item: item.url)


def _frontmatter(source: str, fetched_at: str, generated_at: str) -> str:
    return f"---\nsource: {source}\nfetched_at: {fetched_at}\ngenerated_at: {generated_at}\n---\n\n"


def format_entries(entries: list[UrlEntry], source: str, fetched_at: str) -> str:
    generated_at = datetime.now(timezone.utc).isoformat()
    lines = [_frontmatter(source, fetched_at, generated_at), "# URL Index", ""]
    for entry in entries:
        suffix = f": {entry.description}" if entry.description else ""
        if entry.lastmod:
            suffix = (
                f"{suffix} (lastmod: {entry.lastmod})" if suffix else f" (lastmod: {entry.lastmod})"
            )
        lines.append(f"- [{entry.title.replace(']', '\\]')}]({entry.url}){suffix}")
    return "\n".join(lines) + "\n"


def build_url_tree(urls: list[str], max_depth: int = 3) -> list[str]:
    """Render a compact tree; nodes at ``max_depth`` collapse descendants."""

    @dataclass
    class Node:
        count: int = 0
        children: dict[str, "Node"] | None = None

        def __post_init__(self) -> None:
            if self.children is None:
                self.children = {}

    roots: dict[str, Node] = {}
    for value in sorted(set(urls)):
        parsed = urlsplit(value)
        host_node = roots.setdefault(parsed.netloc, Node())
        host_node.count += 1
        node = host_node
        segments = [segment for segment in parsed.path.split("/") if segment]
        if parsed.query:
            segments.append("?" + parsed.query)
        for segment in segments:
            node = node.children.setdefault(segment, Node())
            node.count += 1

    lines: list[str] = ["# URL Tree", ""]

    def visit(label: str, node: Node, indent: int, depth: int) -> None:
        suffix = (
            "/" if node.children and label not in {"/", "…"} and not label.startswith("?") else ""
        )
        lines.append(f"{'  ' * indent}- `{label}{suffix}` ({node.count})")
        if depth >= max_depth:
            if node.children:
                lines.append(f"{'  ' * (indent + 1)}- `…` ({node.count})")
            return
        for child_label, child in sorted(node.children.items()):
            visit(child_label, child, indent + 1, depth + 1)

    for host, node in sorted(roots.items()):
        lines.append(f"- `{host}/` ({node.count})")
        for label, child in sorted(node.children.items()):
            visit(label, child, 1, 1)
    return lines


def format_tree(entries: list[UrlEntry], source: str, fetched_at: str, max_depth: int) -> str:
    generated_at = datetime.now(timezone.utc).isoformat()
    header = _frontmatter(source, fetched_at, generated_at)
    return header + "\n".join(build_url_tree([entry.url for entry in entries], max_depth)) + "\n"


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


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--url", default=DEFAULT_URL, help="Index URL (default: %(default)s)")
    parser.add_argument(
        "--output", type=Path, default=DEFAULT_OUTPUT, help="Complete URL list output"
    )
    parser.add_argument(
        "--tree-output", type=Path, default=DEFAULT_TREE_OUTPUT, help="Compact tree output"
    )
    parser.add_argument(
        "--allowed-host", action="append", default=[], help="Allowed HTTPS host (repeatable)"
    )
    parser.add_argument(
        "--include-prefix", action="append", default=[], help="Only retain URLs with this prefix"
    )
    parser.add_argument("--max-tree-depth", type=int, default=3)
    parser.add_argument("--freshness-days", type=float, default=DEFAULT_FRESHNESS_DAYS)
    parser.add_argument("--force", action="store_true", help="Refetch even when output is fresh")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if not args.force:
        fetched_at = read_fetched_at(args.output)
        if (
            fetched_at is not None
            and args.tree_output.is_file()
            and datetime.now(timezone.utc) - fetched_at < timedelta(days=args.freshness_days)
        ):
            print(
                f"{args.output}: already fresh (fetched at {fetched_at.isoformat()}). Use --force to refetch."
            )
            return 0
    try:
        source = canonicalize_url(args.url)
        hosts = set(args.allowed_host) or {urlsplit(source).hostname or ""}
        entries = download_entries(source, hosts, tuple(args.include_prefix))
    except (IndexError_, requests.RequestException) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    fetched_at = datetime.now(timezone.utc).isoformat()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.tree_output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(format_entries(entries, source, fetched_at), encoding="utf-8")
    args.tree_output.write_text(
        format_tree(entries, source, fetched_at, args.max_tree_depth), encoding="utf-8"
    )
    print(f"Wrote {args.output} ({len(entries)} URLs)")
    print(f"Wrote {args.tree_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
