"""Tests for scripts/check_urls.py (batch URL reachability checker template)."""

from __future__ import annotations

import json

import check_urls as cu
import pytest


def test_extract_urls_dedupes_and_strips_trailing_punctuation():
    text = (
        "See https://example.com/a) and (https://example.com/b, also https://example.com/a again."
    )
    assert cu.extract_urls(text) == [
        "https://example.com/a",
        "https://example.com/b",
    ]


def test_check_url_ok_on_first_head_request(monkeypatch):
    monkeypatch.setattr(cu, "_request", lambda url, method, timeout: (200, None))
    status, ok, error = cu.check_url("https://example.com", timeout=1.0, retries=2)
    assert (status, ok, error) == (200, True, None)


def test_check_url_falls_back_to_get_on_405(monkeypatch):
    calls = []

    def fake_request(url, method, timeout):
        calls.append(method)
        if method == "HEAD":
            return 405, None
        return 200, None

    monkeypatch.setattr(cu, "_request", fake_request)
    status, ok, error = cu.check_url("https://example.com", timeout=1.0, retries=2)
    assert calls == ["HEAD", "GET"]
    assert (status, ok) == (200, True)


def test_check_url_retries_on_network_failure_then_succeeds(monkeypatch):
    attempts = {"n": 0}

    def fake_request(url, method, timeout):
        attempts["n"] += 1
        if attempts["n"] == 1:
            return None, "timed out"
        return 200, None

    monkeypatch.setattr(cu, "_request", fake_request)
    status, ok, error = cu.check_url("https://example.com", timeout=1.0, retries=2)
    assert attempts["n"] == 2
    assert (status, ok) == (200, True)


def test_check_url_reports_failure_when_all_retries_fail(monkeypatch):
    monkeypatch.setattr(cu, "_request", lambda url, method, timeout: (None, "connection refused"))
    status, ok, error = cu.check_url("https://example.com", timeout=1.0, retries=2)
    assert ok is False
    assert error == "connection refused"


def test_url_cache_round_trip(tmp_path):
    cache = cu.UrlCache(tmp_path / "cache.sqlite3", ttl=3600.0)
    try:
        assert cache.get("https://example.com", now=1000.0) is None
        result = cu.CheckResult("https://example.com", True, 200, None, checked_at=1000.0)
        cache.set(result)
        cached = cache.get("https://example.com", now=1000.0 + 10)
        assert cached is not None
        assert cached.ok is True
        assert cached.status_code == 200
        assert cached.from_cache is True
        assert cache.get("https://example.com", now=1000.0 + 3700) is None
    finally:
        cache.close()


def test_run_uses_cache_and_skips_recheck(tmp_path, monkeypatch):
    monkeypatch.setattr(cu, "_request", lambda url, method, timeout: (200, None))
    cache = cu.UrlCache(tmp_path / "cache.sqlite3", ttl=3600.0)
    try:
        urls = ["https://example.com/a", "https://example.com/b"]
        first = cu.run(
            urls,
            cache,
            concurrency=4,
            per_host_concurrency=2,
            host_delay=0.0,
            timeout=1.0,
            retries=1,
            use_cache=True,
            quiet=True,
        )
        assert all(r.ok for r in first)
        assert all(not r.from_cache for r in first)

        def fail_if_called(url, method, timeout):
            raise AssertionError("should not re-check cached URLs")

        monkeypatch.setattr(cu, "_request", fail_if_called)
        second = cu.run(
            urls,
            cache,
            concurrency=4,
            per_host_concurrency=2,
            host_delay=0.0,
            timeout=1.0,
            retries=1,
            use_cache=True,
            quiet=True,
        )
        assert all(r.from_cache for r in second)
    finally:
        cache.close()


def test_format_json_round_trips(monkeypatch):
    results = [cu.CheckResult("https://example.com", True, 200, None, checked_at=123.0)]
    parsed = json.loads(cu.format_json(results))
    assert parsed[0]["url"] == "https://example.com"
    assert parsed[0]["ok"] is True


def test_format_markdown_contains_header_and_row():
    results = [cu.CheckResult("https://example.com", False, 404, "not found", checked_at=1.0)]
    table = cu.format_markdown(results)
    assert "| Status | Code | Cache | URL | Detail |" in table
    assert "https://example.com" in table
    assert "404" in table


def test_main_end_to_end_with_url_args(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(cu, "_request", lambda url, method, timeout: (200, None))
    cache_db = tmp_path / "cache.sqlite3"
    exit_code = cu.main(
        [
            "--url",
            "https://example.com/llms.txt",
            "--cache-db",
            str(cache_db),
            "--quiet",
            "--format",
            "json",
        ]
    )
    assert exit_code == 0
    out = json.loads(capsys.readouterr().out)
    assert out[0]["url"] == "https://example.com/llms.txt"
    assert out[0]["ok"] is True


def test_main_only_broken_filters_ok_urls(tmp_path, monkeypatch, capsys):
    def fake_request(url, method, timeout):
        return (200, None) if url.endswith("/ok") else (None, "connection refused")

    monkeypatch.setattr(cu, "_request", fake_request)
    exit_code = cu.main(
        [
            "--url",
            "https://example.com/ok",
            "--url",
            "https://example.com/broken",
            "--cache-db",
            str(tmp_path / "cache.sqlite3"),
            "--quiet",
            "--only-broken",
            "--format",
            "json",
        ]
    )
    assert exit_code == 1
    out = json.loads(capsys.readouterr().out)
    assert len(out) == 1
    assert out[0]["url"] == "https://example.com/broken"


def test_main_requires_file_or_url(capsys):
    exit_code = cu.main([])
    assert exit_code == 2
