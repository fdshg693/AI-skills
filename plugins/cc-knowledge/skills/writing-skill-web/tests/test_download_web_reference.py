"""Tests for scripts/download_web_reference.py (freshness-checked download template)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import download_web_reference as dwr
import pytest


class FakeResponse:
    def __init__(self, text: str, status: int = 200):
        self.text = text
        self._status = status

    def raise_for_status(self) -> None:
        if self._status >= 400:
            import requests

            raise requests.HTTPError(f"HTTP {self._status}")


def test_read_fetched_at_missing_file(tmp_path):
    assert dwr.read_fetched_at(tmp_path / "does-not-exist.md") is None


def test_read_fetched_at_no_frontmatter(tmp_path):
    path = tmp_path / "reference.md"
    path.write_text("just some body text, no frontmatter", encoding="utf-8")
    assert dwr.read_fetched_at(path) is None


def test_write_output_then_read_fetched_at_round_trip(tmp_path):
    path = tmp_path / "reference.md"
    dwr.write_output(path, "https://example.com/llms.txt", "BODY CONTENT")

    text = path.read_text(encoding="utf-8")
    assert "source: https://example.com/llms.txt" in text
    assert "BODY CONTENT" in text

    fetched_at = dwr.read_fetched_at(path)
    assert fetched_at is not None
    assert (datetime.now(timezone.utc) - fetched_at) < timedelta(seconds=30)


def test_read_fetched_at_malformed_timestamp(tmp_path):
    path = tmp_path / "reference.md"
    path.write_text(
        "---\nsource: https://example.com\nfetched_at: not-a-date\n---\n\nbody", encoding="utf-8"
    )
    assert dwr.read_fetched_at(path) is None


def test_fetch_success(monkeypatch):
    monkeypatch.setattr(dwr.requests, "get", lambda url, timeout: FakeResponse("hello"))
    assert dwr.fetch("https://example.com/llms.txt") == "hello"


def test_fetch_http_error_raises_system_exit(monkeypatch):
    monkeypatch.setattr(dwr.requests, "get", lambda url, timeout: FakeResponse("", status=500))
    with pytest.raises(SystemExit):
        dwr.fetch("https://example.com/llms.txt")


def test_main_skips_refetch_when_fresh(tmp_path, monkeypatch):
    output = tmp_path / "reference.md"
    dwr.write_output(output, "https://example.com/llms.txt", "OLD BODY")

    called = {"fetch": False}

    def fake_fetch(url: str) -> str:
        called["fetch"] = True
        return "NEW BODY"

    monkeypatch.setattr(dwr, "fetch", fake_fetch)
    monkeypatch.setattr(
        "sys.argv",
        [
            "download_web_reference.py",
            "--url",
            "https://example.com/llms.txt",
            "--output",
            str(output),
        ],
    )
    dwr.main()

    assert called["fetch"] is False
    assert "OLD BODY" in output.read_text(encoding="utf-8")


def test_main_force_refetches_even_when_fresh(tmp_path, monkeypatch):
    output = tmp_path / "reference.md"
    dwr.write_output(output, "https://example.com/llms.txt", "OLD BODY")

    monkeypatch.setattr(dwr, "fetch", lambda url: "NEW BODY")
    monkeypatch.setattr(
        "sys.argv",
        [
            "download_web_reference.py",
            "--url",
            "https://example.com/llms.txt",
            "--output",
            str(output),
            "--force",
        ],
    )
    dwr.main()

    assert "NEW BODY" in output.read_text(encoding="utf-8")


def test_main_refetches_when_stale(tmp_path, monkeypatch):
    output = tmp_path / "reference.md"
    stale_time = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
    output.write_text(
        f"---\nsource: https://example.com/llms.txt\nfetched_at: {stale_time}\n---\n\nOLD BODY",
        encoding="utf-8",
    )

    monkeypatch.setattr(dwr, "fetch", lambda url: "NEW BODY")
    monkeypatch.setattr(
        "sys.argv",
        [
            "download_web_reference.py",
            "--url",
            "https://example.com/llms.txt",
            "--output",
            str(output),
        ],
    )
    dwr.main()

    assert "NEW BODY" in output.read_text(encoding="utf-8")
