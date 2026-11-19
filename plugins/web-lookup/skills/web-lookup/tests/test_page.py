"""`page` の取得・本文抽出・失敗判定・CLI 配線。ネットワークには出ない（合成 HTML と偽セッション）。"""

from __future__ import annotations

from pathlib import Path

import pytest
import requests

import page
import web_lookup
from page import MIN_CHARS, PageResult, extract, fetch_page, normalize_whitespace

PARAGRAPH = (
    "This synthetic company builds measuring instruments for laboratories and has "
    "worked with research institutes for many years, shipping devices worldwide. "
)
SJIS_META = '<meta http-equiv="Content-Type" content="text/html; charset=Shift_JIS">'


def _article_html(body: str, *, title: str = "Synthetic Co.", head: str = "") -> str:
    return f"""<!doctype html>
<html><head>{head}<title>{title}</title></head>
<body>
<header><nav><ul><li><a href="/">Home</a></li><li><a href="/news">News</a></li></ul></nav></header>
<main><article>
<h1>{title}</h1>
{body}
</article></main>
<footer><p>Footer copyright notice repeated on every page.</p></footer>
</body></html>"""


def _paragraphs(count: int = 4) -> str:
    return "\n".join(f"<p>{PARAGRAPH * 2}</p>" for _ in range(count))


# --- extract -----------------------------------------------------------------


def test_extract_keeps_body_and_drops_navigation() -> None:
    html = _article_html(_paragraphs()).encode("utf-8")
    title, markdown = extract(html, "https://example.com/about")
    assert title == "Synthetic Co."
    assert "measuring instruments" in markdown
    assert "Footer copyright" not in markdown
    assert "News" not in markdown


def test_extract_flattens_list_inside_table_cell() -> None:
    table = """
<table>
<tr><th>Company</th><td>Synthetic Co.</td></tr>
<tr><th>Phone</th><td><ul><li>03-0000-0001</li><li>03-0000-0002</li></ul></td></tr>
<tr><th>Founded</th><td>1999</td></tr>
</table>"""
    html = _article_html(_paragraphs(3) + table).encode("utf-8")
    _title, markdown = extract(html, "https://example.com/about")
    assert "03-0000-0001 / 03-0000-0002" in markdown


def test_extract_reads_shift_jis_bytes_with_meta_charset() -> None:
    sentence = "これは合成した日本語の本文です。研究機関向けの計測機器を作っています。"
    body = f"<p>{sentence * 6}</p>" * 3
    html = _article_html(body, title="合成株式会社", head=SJIS_META).encode("shift_jis")
    title, markdown = extract(html, "https://example.jp/")
    assert title == "合成株式会社"
    assert "計測機器" in markdown


def test_extract_uses_header_charset_without_meta() -> None:
    sentence = "ヘッダーだけに文字コードがある合成ページの本文です。"
    body = f"<p>{sentence * 8}</p>" * 3
    html = _article_html(body, title="ヘッダー判定").encode("shift_jis")
    _title, markdown = extract(html, "https://example.jp/", charset="Shift_JIS")
    assert "文字コード" in markdown


def test_title_is_never_empty() -> None:
    html = b"<html><body><article>" + _paragraphs().encode() + b"</article></body></html>"
    title, _markdown = extract(html, "https://example.com/x")
    assert title


def test_normalize_whitespace_joins_bullet_breaks_and_blank_runs() -> None:
    raw = "- \n      Tokyo\n-\n   Osaka   \n\n\n\n\nNext paragraph."
    assert normalize_whitespace(raw) == "- Tokyo\n- Osaka\n\nNext paragraph."


# --- fetch_page with a fake session ------------------------------------------


class _FakeResponse:
    def __init__(self, status: int, body: bytes, content_type: str, url: str) -> None:
        self.status_code = status
        self._body = body
        self.headers = {"Content-Type": content_type}
        self.url = url

    def __enter__(self) -> _FakeResponse:
        return self

    def __exit__(self, *_exc: object) -> None:
        return None

    def iter_content(self, chunk_size: int):
        for start in range(0, len(self._body), chunk_size):
            yield self._body[start : start + chunk_size]


class _FakeSession:
    def __init__(self, response: _FakeResponse | None = None, exc: Exception | None = None):
        self.response = response
        self.exc = exc
        self.calls: list[dict] = []

    def get(self, url: str, **kwargs):
        self.calls.append({"url": url, **kwargs})
        if self.exc:
            raise self.exc
        return self.response


def _session(
    status: int = 200,
    body: bytes = b"",
    content_type: str = "text/html; charset=utf-8",
    url: str = "https://example.com/final",
) -> _FakeSession:
    return _FakeSession(_FakeResponse(status, body, content_type, url))


def test_fetch_page_success_writes_title_and_final_url() -> None:
    session = _session(body=_article_html(_paragraphs()).encode())
    result = fetch_page("https://example.com/start", session=session)
    assert result.ok
    assert result.content.startswith("# Synthetic Co.\n\nURL: https://example.com/final\n\n")
    call = session.calls[0]
    assert call["stream"] is True
    assert call["timeout"] == (page.CONNECT_TIMEOUT, page.READ_TIMEOUT)
    assert call["headers"]["User-Agent"].startswith("web-lookup")
    assert "text/html" in call["headers"]["Accept"]
    assert call["headers"]["Accept-Language"]


def test_fetch_page_reports_http_status() -> None:
    result = fetch_page("https://example.com/", session=_session(status=403, body=b"Forbidden"))
    assert result.failure == "failed (HTTP 403)"


def test_fetch_page_rejects_non_html() -> None:
    session = _session(content_type="application/pdf")
    result = fetch_page("https://example.com/a.pdf", session=session)
    assert result.failure == "failed (content-type application/pdf)"


def test_fetch_page_rejects_too_large(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(page, "MAX_BYTES", 1000)
    result = fetch_page("https://example.com/", session=_session(body=b"x" * 2000))
    assert result.failure == "failed (too large)"


def test_fetch_page_reports_timeout() -> None:
    session = _FakeSession(exc=requests.ReadTimeout("slow"))
    assert fetch_page("https://example.com/", session=session).failure == "failed (timeout)"


def test_fetch_page_short_body_is_too_short() -> None:
    html = (
        b"<html><head><title>Login</title></head>"
        b"<body><p>Please log in to continue.</p></body></html>"
    )
    result = fetch_page("https://example.com/", session=_session(body=html))
    assert result.failure.startswith("too short (")
    assert int(result.failure.split("(")[1].split()[0]) < MIN_CHARS


def test_fetch_page_empty_document_does_not_raise() -> None:
    result = fetch_page("https://example.com/", session=_session(body=b""))
    assert not result.ok


# --- CLI wiring --------------------------------------------------------------


def _ok(url: str, body: str) -> PageResult:
    return PageResult(url=url, title="Ok page", content=f"# Ok page\n\nURL: {url}\n\n{body}\n")


def test_cli_page_writes_index_with_hints_and_failures(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("WEB_LOOKUP_OUTPUT_DIR", str(tmp_path))
    results = [
        _ok("https://example.com/a", "Body text that stops in the middle of"),
        PageResult(url="https://example.com/b", failure="failed (HTTP 403)"),
    ]
    monkeypatch.setattr(web_lookup, "fetch_pages", lambda urls: results)

    assert web_lookup.main(["page", "https://example.com/a", "https://example.com/b"]) == 0
    index = Path(capsys.readouterr().out.strip())
    text = index.read_text(encoding="utf-8")
    assert "- [Ok page](0001.md) (" in text
    assert "chars) — cut off" in text
    assert "- https://example.com/b — failed (HTTP 403); try `tav extract`" in text
    assert (index.parent / "0001.md").is_file()
    assert not (index.parent / "0002.md").exists()


def test_cli_page_all_failed_exits_nonzero(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("WEB_LOOKUP_OUTPUT_DIR", str(tmp_path))
    results = [PageResult(url="https://example.com/b", failure="too short (26 chars)")]
    monkeypatch.setattr(web_lookup, "fetch_pages", lambda urls: results)

    assert web_lookup.main(["page", "https://example.com/b"]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "too short (26 chars)" in captured.err
    assert not any(tmp_path.iterdir())


def test_available_lists_page_first(capsys: pytest.CaptureFixture[str]) -> None:
    assert web_lookup.main(["available"]) == 0
    rows = capsys.readouterr().out.splitlines()
    assert rows[1].split()[:2] == ["page", "available"]


def test_tav_search_index_marks_excerpts(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("WEB_LOOKUP_OUTPUT_DIR", str(tmp_path))
    monkeypatch.setenv("TAVILY_API_KEY", "dummy")
    body = "[...] chunk one. [...] chunk two."
    items = [("Hit", f"# Hit\n\nURL: https://example.com/\nScore: 0.9\n\n{body}")]
    monkeypatch.setattr(web_lookup, "tav_search", lambda *a, **k: items)

    assert web_lookup.main(["tav", "search", "synthetic query"]) == 0
    text = Path(capsys.readouterr().out.strip()).read_text(encoding="utf-8")
    assert "chars) — excerpt gaps: 2" in text
