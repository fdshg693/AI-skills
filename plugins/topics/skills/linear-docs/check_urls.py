"""Extract URLs from a file, or check explicitly given URLs, for reachability.

Bundled here (rather than a shared module one level up) so
writing-skill-web-derived skills can check whether candidate paths
(llms.txt / llms-full.txt / etc.) actually exist without depending on a
path outside the skill directory -- see web-patterns-reference.md section
1.1 for why this skill's templates are copy-and-adapt files instead of an
importable shared module.

Usage:
    python check_urls.py <path/to/file> [options]
    python check_urls.py --url <url> [--url <url> ...] [options]

file と --url は併用でき、その場合は両方から集めたURL(重複除去)をまとめて
1回のバッチでチェックする。候補パスが存在するかどうかを都度1件ずつ確認する
(例: llms.txt / llms-full.txt のような複数候補を1つずつWebFetchする)のは
往復回数分のレイテンシがそのまま積み上がるため、--url を複数指定してまとめて
並列チェックする方が効率的。

Design notes:
- Checks run in a bounded thread pool (global concurrency limit) plus a
  per-host semaphore and minimum delay, so a file with many links to the
  same domain does not hammer that host.
- Results are cached in a local SQLite database keyed by the raw URL
  (no hashing needed: SQLite's TEXT primary key handles arbitrary-length
  keys fine, and keeping the URL as the key keeps the cache directly
  inspectable with any SQLite client). Entries expire after --ttl seconds.
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CACHE_DB = Path(__file__).resolve().parent / ".cache" / "url_cache.sqlite3"

URL_RE = re.compile(r"https?://[^\s<>\)\]\"'`]+")
TRAILING_PUNCTUATION = ".,;:!?)]}>'\""
USER_AGENT = "url-checker/1.0 (+https://github.com/)"

FALLBACK_TO_GET_CODES = {400, 403, 405, 501}


def extract_urls(text: str) -> list[str]:
    seen: set[str] = set()
    urls: list[str] = []
    for match in URL_RE.finditer(text):
        url = match.group(0).rstrip(TRAILING_PUNCTUATION)
        if url and url not in seen:
            seen.add(url)
            urls.append(url)
    return urls


@dataclass
class CheckResult:
    url: str
    ok: bool
    status_code: int | None
    error: str | None
    checked_at: float
    from_cache: bool = False


class HostThrottle:
    """Bounds concurrency and request rate per host."""

    def __init__(self, per_host_concurrency: int, host_delay: float):
        self.per_host_concurrency = per_host_concurrency
        self.host_delay = host_delay
        self._semaphores: dict[str, threading.Semaphore] = {}
        self._last_request: dict[str, float] = {}
        self._lock = threading.Lock()

    def _semaphore_for(self, host: str) -> threading.Semaphore:
        with self._lock:
            sem = self._semaphores.get(host)
            if sem is None:
                sem = threading.Semaphore(self.per_host_concurrency)
                self._semaphores[host] = sem
            return sem

    def acquire(self, host: str) -> None:
        self._semaphore_for(host).acquire()
        with self._lock:
            last = self._last_request.get(host, 0.0)
        wait = self.host_delay - (time.monotonic() - last)
        if wait > 0:
            time.sleep(wait)
        with self._lock:
            self._last_request[host] = time.monotonic()

    def release(self, host: str) -> None:
        self._semaphore_for(host).release()


class UrlCache:
    SCHEMA = """
    CREATE TABLE IF NOT EXISTS url_cache (
        url TEXT PRIMARY KEY,
        status_code INTEGER,
        ok INTEGER NOT NULL,
        error TEXT,
        checked_at REAL NOT NULL,
        expires_at REAL NOT NULL
    )
    """

    def __init__(self, db_path: Path, ttl: float):
        self.ttl = ttl
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute(self.SCHEMA)
        self._conn.commit()
        self._lock = threading.Lock()

    def get(self, url: str, now: float) -> CheckResult | None:
        with self._lock:
            row = self._conn.execute(
                "SELECT status_code, ok, error, checked_at, expires_at "
                "FROM url_cache WHERE url = ?",
                (url,),
            ).fetchone()
        if row is None:
            return None
        status_code, ok, error, checked_at, expires_at = row
        if expires_at <= now:
            return None
        return CheckResult(url, bool(ok), status_code, error, checked_at, from_cache=True)

    def set(self, result: CheckResult) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT INTO url_cache (url, status_code, ok, error, checked_at, expires_at) "
                "VALUES (?, ?, ?, ?, ?, ?) "
                "ON CONFLICT(url) DO UPDATE SET "
                "status_code=excluded.status_code, ok=excluded.ok, error=excluded.error, "
                "checked_at=excluded.checked_at, expires_at=excluded.expires_at",
                (
                    result.url,
                    result.status_code,
                    int(result.ok),
                    result.error,
                    result.checked_at,
                    result.checked_at + self.ttl,
                ),
            )
            self._conn.commit()

    def close(self) -> None:
        self._conn.close()


def _request(url: str, method: str, timeout: float) -> tuple[int | None, str | None]:
    req = urllib.request.Request(url, method=method, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, None
    except urllib.error.HTTPError as e:
        return e.code, None
    except urllib.error.URLError as e:
        return None, str(e.reason)
    except (TimeoutError, OSError) as e:
        return None, str(e)


def check_url(url: str, timeout: float, retries: int) -> tuple[int | None, bool, str | None]:
    attempt = 0
    status_code: int | None = None
    error: str | None = None
    while attempt < max(1, retries):
        attempt += 1
        status_code, error = _request(url, "HEAD", timeout)
        if status_code in FALLBACK_TO_GET_CODES:
            status_code, error = _request(url, "GET", timeout)
        if status_code is not None:
            break
        # network-level failure (timeout/DNS/connection) -> retry
    ok = status_code is not None and 200 <= status_code < 400
    return status_code, ok, error


def worker(
    url: str,
    throttle: HostThrottle,
    timeout: float,
    retries: int,
) -> CheckResult:
    host = urlparse(url).netloc
    throttle.acquire(host)
    try:
        status_code, ok, error = check_url(url, timeout, retries)
    finally:
        throttle.release(host)
    return CheckResult(url, ok, status_code, error, time.time())


def run(
    urls: list[str],
    cache: UrlCache,
    concurrency: int,
    per_host_concurrency: int,
    host_delay: float,
    timeout: float,
    retries: int,
    use_cache: bool,
    quiet: bool,
) -> list[CheckResult]:
    from concurrent.futures import ThreadPoolExecutor, as_completed

    now = time.time()
    results: dict[str, CheckResult] = {}
    to_fetch: list[str] = []

    if use_cache:
        for url in urls:
            cached = cache.get(url, now)
            if cached is not None:
                results[url] = cached
            else:
                to_fetch.append(url)
    else:
        to_fetch = list(urls)

    throttle = HostThrottle(per_host_concurrency, host_delay)
    total = len(urls)
    done = len(results)

    if to_fetch:
        with ThreadPoolExecutor(max_workers=concurrency) as pool:
            futures = {
                pool.submit(worker, url, throttle, timeout, retries): url for url in to_fetch
            }
            for future in as_completed(futures):
                result = future.result()
                results[result.url] = result
                cache.set(result)
                done += 1
                if not quiet:
                    mark = "OK" if result.ok else "NG"
                    print(f"[{done}/{total}] {mark} {result.url}", file=sys.stderr)

    return [results[url] for url in urls]


def format_table(results: list[CheckResult]) -> str:
    lines = []
    for r in results:
        status = str(r.status_code) if r.status_code is not None else "----"
        mark = "OK" if r.ok else "NG"
        cache_flag = "cache" if r.from_cache else "live "
        detail = r.error or ""
        lines.append(
            f"{mark}  {status:>4}  {cache_flag}  {r.url}" + (f"  ({detail})" if detail else "")
        )
    return "\n".join(lines)


def format_markdown(results: list[CheckResult]) -> str:
    lines = ["| Status | Code | Cache | URL | Detail |", "| --- | --- | --- | --- | --- |"]
    for r in results:
        status = "OK" if r.ok else "NG"
        code = str(r.status_code) if r.status_code is not None else "-"
        cache_flag = "cache" if r.from_cache else "live"
        detail = (r.error or "").replace("|", "\\|")
        lines.append(f"| {status} | {code} | {cache_flag} | {r.url} | {detail} |")
    return "\n".join(lines)


def format_json(results: list[CheckResult]) -> str:
    return json.dumps(
        [
            {
                "url": r.url,
                "ok": r.ok,
                "status_code": r.status_code,
                "error": r.error,
                "from_cache": r.from_cache,
                "checked_at": r.checked_at,
            }
            for r in results
        ],
        ensure_ascii=False,
        indent=2,
    )


FORMATTERS = {"table": format_table, "markdown": format_markdown, "json": format_json}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "file",
        type=Path,
        nargs="?",
        default=None,
        help="URLを抽出する対象ファイル(省略可、--urlと併用可)",
    )
    parser.add_argument(
        "--url",
        action="append",
        dest="urls",
        metavar="URL",
        help="直接チェックするURL(複数回指定可。fileと併用した場合は両方から集めたURLをまとめてチェックする)",
    )
    parser.add_argument("--concurrency", type=int, default=8, help="全体の同時実行数 (既定: 8)")
    parser.add_argument(
        "--per-host-concurrency", type=int, default=2, help="同一ホストへの同時実行数 (既定: 2)"
    )
    parser.add_argument(
        "--host-delay",
        type=float,
        default=0.5,
        help="同一ホストへの最小リクエスト間隔・秒 (既定: 0.5)",
    )
    parser.add_argument(
        "--timeout", type=float, default=10.0, help="リクエストタイムアウト・秒 (既定: 10)"
    )
    parser.add_argument(
        "--retries", type=int, default=2, help="ネットワークエラー時の試行回数 (既定: 2)"
    )
    parser.add_argument(
        "--cache-db", type=Path, default=DEFAULT_CACHE_DB, help="SQLiteキャッシュのパス"
    )
    parser.add_argument(
        "--ttl", type=float, default=86400.0, help="キャッシュの有効期限・秒 (既定: 86400 = 24h)"
    )
    parser.add_argument(
        "--no-cache", action="store_true", help="キャッシュを使わず必ず再チェックする"
    )
    parser.add_argument(
        "--format", choices=sorted(FORMATTERS), default="table", help="出力形式 (既定: table)"
    )
    parser.add_argument("--output", type=Path, help="出力先ファイル (未指定なら標準出力)")
    parser.add_argument("--only-broken", action="store_true", help="失敗したURLのみ出力する")
    parser.add_argument("--quiet", action="store_true", help="進捗ログを抑制する")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if args.file is None and not args.urls:
        print("ファイル、または --url を少なくとも1つ指定してください。", file=sys.stderr)
        return 2

    urls: list[str] = []
    seen: set[str] = set()

    if args.file is not None:
        if not args.file.is_file():
            print(f"ファイルが見つかりません: {args.file}", file=sys.stderr)
            return 2
        text = args.file.read_text(encoding="utf-8", errors="replace")
        for url in extract_urls(text):
            if url not in seen:
                seen.add(url)
                urls.append(url)

    for raw_url in args.urls or []:
        url = raw_url.strip()
        if url and url not in seen:
            seen.add(url)
            urls.append(url)

    if not urls:
        print("URLが見つかりませんでした。", file=sys.stderr)
        return 0

    cache = UrlCache(args.cache_db, args.ttl)
    try:
        results = run(
            urls,
            cache,
            concurrency=args.concurrency,
            per_host_concurrency=args.per_host_concurrency,
            host_delay=args.host_delay,
            timeout=args.timeout,
            retries=args.retries,
            use_cache=not args.no_cache,
            quiet=args.quiet,
        )
    finally:
        cache.close()

    if args.only_broken:
        results = [r for r in results if not r.ok]

    output = FORMATTERS[args.format](results)
    if args.output:
        args.output.write_text(output + "\n", encoding="utf-8")
    else:
        print(output)

    broken = sum(1 for r in results if not r.ok)
    if not args.quiet:
        print(f"\n{len(results)} URL中 {broken} 件失敗", file=sys.stderr)

    return 1 if broken else 0


if __name__ == "__main__":
    raise SystemExit(main())
