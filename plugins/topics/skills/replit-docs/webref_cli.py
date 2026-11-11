"""Bounded Replit documentation index, search, and page retrieval.

The 24-hour snapshot is a single atomic JSON file. Limits allow headroom over
the observed 14 indexes, 2,678 pages and 2.4 MB English full text (2026-11).
Documents are untrusted data, not instructions. No proxy is used: DNS answers
are checked and the TLS connection is pinned to a checked public address.
"""

from __future__ import annotations

import argparse
import hashlib
import http.client
import ipaddress
import json
import os
import re
import socket
import ssl
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urljoin, urlsplit, urlunsplit

BASE = "https://docs.replit.com/"
ROOT = BASE + "llms.txt"
FULL = BASE + "llms-full.txt"
OUTPUT = Path(__file__).resolve().parent / "output"
MAX_INDEXES, MAX_DEPTH, MAX_PAGES = 64, 8, 10000
MAX_INDEX_BYTES, MAX_FULL_BYTES, MAX_PAGE_BYTES = 2_000_000, 10_000_000, 2_000_000
MAX_TOTAL_INDEX_BYTES, MAX_REDIRECTS = 20_000_000, 5
TIMEOUT = 30
LINK = re.compile(r"^- \[([^\]\n]+)\]\(([^\s)]+)\)([^\n]*)", re.MULTILINE)
MARKER = re.compile(r"^# ([^\n]+)\nSource: (\S+)\s*$", re.MULTILINE)
SOURCE = re.compile(r"^Source:.*$", re.MULTILINE)


def validate_url(url: str) -> str:
    p = urlsplit(url)
    if (
        p.scheme != "https"
        or p.hostname != "docs.replit.com"
        or p.username is not None
        or p.password is not None
        or p.port not in (None, 443)
        or p.query
        or p.fragment
        or not p.path.startswith("/")
        or any(ord(c) < 33 for c in url)
        or "\\" in p.path
        or "%" in p.path
        or any(x in (".", "..") for x in p.path.split("/"))
    ):
        raise ValueError(f"disallowed URL: {url}")
    return urlunsplit(("https", "docs.replit.com", p.path, "", ""))


def public_addresses(host: str) -> list[str]:
    addresses = list(
        dict.fromkeys(item[4][0] for item in socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM))
    )
    if not addresses or any(not ipaddress.ip_address(addr).is_global for addr in addresses):
        raise ValueError("DNS returned a non-public address")
    return addresses


class PinnedHTTPS(http.client.HTTPSConnection):
    def connect(self) -> None:
        address = public_addresses(self.host)[0]
        raw = socket.create_connection((address, self.port), self.timeout)
        try:
            self.sock = self._context.wrap_socket(raw, server_hostname=self.host)
        except BaseException:
            raw.close()
            raise


def fetch(url: str, limit: int) -> tuple[str, str, str | None]:
    for _ in range(MAX_REDIRECTS + 1):
        url = validate_url(url)
        p = urlsplit(url)
        conn = PinnedHTTPS(p.hostname, timeout=TIMEOUT, context=ssl.create_default_context())
        try:
            conn.request(
                "GET",
                p.path,
                headers={"User-Agent": "replit-docs-skill/1.0", "Accept-Encoding": "identity"},
            )
            response = conn.getresponse()
            if response.status in (301, 302, 303, 307, 308):
                location = response.getheader("Location")
                if not location:
                    raise ValueError("redirect without Location")
                url = validate_url(urljoin(url, location))
                continue
            if response.status != 200:
                raise ValueError(f"HTTP {response.status}: {url}")
            length = response.getheader("Content-Length")
            if length is not None and (not length.isdigit() or int(length) > limit):
                raise ValueError(f"invalid or oversized Content-Length: {url}")
            body = response.read(limit + 1)
            if len(body) > limit or (length is not None and len(body) != int(length)):
                raise ValueError(f"oversized or incomplete response: {url}")
            if response.getheader("Content-Encoding", "identity").lower() != "identity":
                raise ValueError("unsupported Content-Encoding")
            text = body.decode("utf-8")
            if not text.strip() or text.lstrip().lower().startswith(("<!doctype html", "<html")):
                raise ValueError(f"empty or HTML response: {url}")
            return text, url, response.getheader("Last-Modified")
        finally:
            conn.close()
    raise ValueError("redirect limit exceeded")


def parse_sections(text: str, known_pages: set[str]) -> list[dict[str, str]]:
    matches = list(MARKER.finditer(text))
    sources = list(SOURCE.finditer(text))
    if not matches or len(matches) != len(sources) or text[: matches[0].start()].strip():
        raise ValueError("full text Source boundary format changed; use individual pages")
    sections, seen = [], set()
    for i, match in enumerate(matches):
        url = validate_url(match.group(2))
        canonical = url.removesuffix(".md")
        if canonical in seen or canonical not in known_pages:
            raise ValueError(f"duplicate or unknown Source: {url}; use individual pages")
        seen.add(canonical)
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[match.end() : end].strip()
        if not body:
            raise ValueError(f"empty section: {url}")
        sections.append({"title": match.group(1), "url": url, "body": body})
    return sections


def build_snapshot(allow_index_only: bool = False) -> dict:
    pending = [(ROOT, 0)]
    visited, pages, indexes, total = set(), {}, [], 0
    while pending:
        url, depth = pending.pop(0)
        if url in visited:
            continue
        if depth > MAX_DEPTH or len(visited) >= MAX_INDEXES:
            raise ValueError("index depth/count limit exceeded")
        visited.add(url)
        text, final, modified = fetch(url, MAX_INDEX_BYTES)
        total += len(text.encode("utf-8"))
        if total > MAX_TOTAL_INDEX_BYTES:
            raise ValueError("total index size limit exceeded")
        links = list(LINK.finditer(text))
        if not text.lstrip().startswith("# ") or not links:
            raise ValueError(f"invalid index format: {url}")
        indexes.append(
            {"url": url, "final_url": final, "fetched_at": now(), "last_modified": modified}
        )
        headings = []
        for line in text.splitlines():
            heading = re.match(r"^(#{1,6}) (.+)$", line)
            if heading:
                level = len(heading.group(1))
                headings = headings[: level - 1] + [heading.group(2)]
                continue
            link = LINK.match(line)
            if not link:
                continue
            target = validate_url(urljoin(final, link.group(2)))
            path = urlsplit(target).path
            if path.startswith("/_llms/") and path.endswith(".txt"):
                pending.append((target, depth + 1))
            elif path.endswith(".md"):
                pages.setdefault(
                    target.removesuffix(".md"),
                    {
                        "title": link.group(1),
                        "url": target,
                        "hierarchy": " / ".join(headings),
                        "index": url,
                    },
                )
                if len(pages) > MAX_PAGES:
                    raise ValueError("page count limit exceeded")
            else:
                raise ValueError(f"unexpected index link: {target}")
    if not pages:
        raise ValueError("index contains no pages")
    try:
        full, final, modified = fetch(FULL, MAX_FULL_BYTES)
        sections = parse_sections(full, set(pages))
        full_data = {
            "url": final,
            "fetched_at": now(),
            "last_modified": modified,
            "language": "English",
            "sections": sections,
        }
    except (OSError, ValueError, http.client.HTTPException) as exc:
        if not allow_index_only:
            raise
        full_data = {
            "url": FULL,
            "fetched_at": None,
            "last_modified": None,
            "language": "English",
            "sections": [],
            "error": str(exc),
        }
    return {
        "version": 1,
        "fetched_at": now(),
        "indexes": indexes,
        "pages": list(pages.values()),
        "full": full_data,
    }


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def atomic_json(path: Path, value: dict) -> None:
    atomic_text(path, json.dumps(value, ensure_ascii=False))


def atomic_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    name = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as f:
            name = f.name
            f.write(value)
            f.flush()
            os.fsync(f.fileno())
        os.replace(name, path)
    finally:
        if name and os.path.exists(name):
            os.unlink(name)


def load(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def fresh(data: dict) -> bool:
    try:
        age = datetime.now(timezone.utc) - datetime.fromisoformat(data["fetched_at"])
        return timedelta(0) <= age < timedelta(hours=24)
    except (KeyError, TypeError, ValueError):
        return False


def page_url(raw: str) -> str:
    url = validate_url(urljoin(BASE, raw))
    path = urlsplit(url).path
    if path.startswith("/_llms/") or path in ("/", "/llms.txt", "/llms-full.txt"):
        raise ValueError("not a documentation page")
    return url if path.endswith(".md") else url + ".md"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    update = sub.add_parser(
        "update", help="refresh index and English full text; stale cache survives failure"
    )
    update.add_argument("--force", action="store_true")
    index = sub.add_parser("index", help="search hierarchical index across languages")
    index.add_argument("query", nargs="?", default="")
    search = sub.add_parser("search", help="search English full text, bounded results")
    search.add_argument("query")
    extract = sub.add_parser(
        "extract", help="extract a validated English section from the cached full text"
    )
    extract.add_argument("url")
    page = sub.add_parser("page", help="fetch an individual Markdown page")
    page.add_argument("url")
    args = parser.parse_args()
    snapshot = OUTPUT / "snapshot.json"
    try:
        if args.command == "page":
            url = page_url(args.url)
            path = OUTPUT / "pages" / (hashlib.sha256(url.encode()).hexdigest() + ".json")
            try:
                body, final, modified = fetch(url, MAX_PAGE_BYTES)
                data = {
                    "url": url,
                    "final_url": final,
                    "fetched_at": now(),
                    "last_modified": modified,
                    "body": body,
                }
                atomic_json(path, data)
            except (OSError, ValueError, http.client.HTTPException) as exc:
                if not path.is_file():
                    raise
                data = load(path)
                print(
                    f"WARNING: fetch failed ({exc}); stale cache, fetched_at: {data['fetched_at']}",
                    file=sys.stderr,
                )
            text_path = path.with_suffix(".md")
            atomic_text(
                text_path,
                f"Source: {data['final_url']}\nfetched_at: {data['fetched_at']}\nLast-Modified: {data['last_modified']}\n\n{data['body']}",
            )
            print(
                f"Source: {data['final_url']}\nfetched_at: {data['fetched_at']}\nFull text: {text_path}"
            )
            return 0
        if args.command == "update":
            if (
                not args.force
                and snapshot.is_file()
                and fresh(load(snapshot))
                and not load(snapshot)["full"].get("error")
            ):
                print(f"Fresh cache: {snapshot} (fetched_at: {load(snapshot)['fetched_at']})")
                return 0
            try:
                data = build_snapshot(allow_index_only=not snapshot.is_file())
                atomic_json(snapshot, data)
                print(
                    f"Updated {snapshot}; fetched_at: {data['fetched_at']}; {len(data['pages'])} pages, {len(data['full']['sections'])} English sections"
                )
                if data["full"].get("error"):
                    print(
                        f"WARNING: index only; full text unavailable: {data['full']['error']}. Use page for individual documents.",
                        file=sys.stderr,
                    )
            except (OSError, ValueError, http.client.HTTPException) as exc:
                if not snapshot.is_file():
                    raise
                data = load(snapshot)
                print(
                    f"WARNING: update failed ({exc}); stale cache: {snapshot}, fetched_at: {data['fetched_at']}",
                    file=sys.stderr,
                )
            return 0
        data = load(snapshot)
        print(f"Snapshot fetched_at: {data['fetched_at']} (index and full text fetched separately)")
        if args.command in ("search", "extract") and data["full"].get("error"):
            raise ValueError(f"full text unavailable: {data['full']['error']}; use index and page")
        if args.command == "extract":
            url = page_url(args.url).removesuffix(".md")
            section = next(
                (s for s in data["full"]["sections"] if s["url"].removesuffix(".md") == url), None
            )
            if section is None:
                raise ValueError(f"section not found: {url}; try index and page")
            path = OUTPUT / "sections" / (hashlib.sha256(url.encode()).hexdigest() + ".md")
            atomic_text(
                path,
                f"Source: {section['url']}\nfetched_at: {data['full']['fetched_at']}\nLast-Modified: {data['full']['last_modified']}\n\n# {section['title']}\n\n{section['body']}\n",
            )
            print(
                f"Source: {section['url']}\nEnglish full text fetched_at: {data['full']['fetched_at']}\nFull text: {path}"
            )
            return 0
        needle = args.query.casefold()
        if args.command == "index":
            found = [
                p
                for p in data["pages"]
                if needle in (p["title"] + " " + p["url"] + " " + p["hierarchy"]).casefold()
            ]
            for p in found[:100]:
                print(f"{p['hierarchy']} | {p['title']} | {p['url']} | index: {p['index']}")
        else:
            if not needle:
                raise ValueError("empty search query")
            found = [
                s
                for s in data["full"]["sections"]
                if needle in (s["title"] + "\n" + s["body"]).casefold()
            ]
            print(
                f"English full text fetched_at: {data['full']['fetched_at']}; search is not exhaustive across languages"
            )
            for section in found[:100]:
                lines = [
                    line.strip()[:300]
                    for line in section["body"].splitlines()
                    if needle in line.casefold()
                ][:3]
                print(f"{section['title']} | {section['url']}\n  " + "\n  ".join(lines))
        print(f"Matches: {len(found)} (showing at most 100); zero matches do not establish absence")
        return 0
    except (OSError, ValueError, KeyError, TypeError, http.client.HTTPException) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
