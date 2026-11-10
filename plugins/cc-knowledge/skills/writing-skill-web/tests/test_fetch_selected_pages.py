"""Tests for constrained page retrieval."""

from __future__ import annotations

import json

import fetch_selected_pages as f


class FakeResponse:
    def __init__(self, url: str, text: str):
        self.url = url
        self.text = text
        self.content = text.encode()

    def raise_for_status(self):
        return None


def test_manifest_reading(tmp_path):
    manifest = tmp_path / "selection.json"
    manifest.write_text(
        json.dumps({"entries": [{"url": "https://docs.example.com/docs/a"}]}), encoding="utf-8"
    )
    assert f.read_manifest(manifest) == ["https://docs.example.com/docs/a"]


def test_fetch_and_write_selected_page(tmp_path, monkeypatch):
    monkeypatch.setattr(
        f.requests, "get", lambda url, timeout, **kwargs: FakeResponse(url, "PAGE BODY")
    )
    final_url, body = f.fetch_page(
        "https://docs.example.com/docs/a#fragment",
        {"docs.example.com"},
        ("https://docs.example.com/docs/",),
    )
    path = f.write_page(tmp_path, final_url, body)
    assert path.is_file()
    assert "source: https://docs.example.com/docs/a" in path.read_text(encoding="utf-8")
    assert "PAGE BODY" in path.read_text(encoding="utf-8")


def test_fetch_rejects_prefix_escape(monkeypatch):
    monkeypatch.setattr(
        f.requests, "get", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("network"))
    )
    try:
        f.fetch_page(
            "https://docs.example.com/blog/a",
            {"docs.example.com"},
            ("https://docs.example.com/docs/",),
        )
    except f.index.IndexError_ as exc:
        assert "prefix" in str(exc)
    else:
        raise AssertionError("expected prefix rejection")


def test_fetch_validates_redirect_before_following(monkeypatch):
    class RedirectResponse:
        status_code = 302
        headers = {"Location": "https://evil.example/docs/a"}
        url = "https://docs.example.com/docs/a"
        text = ""
        content = b""

        def raise_for_status(self):
            return None

    calls = []

    def fake_get(url, timeout, **kwargs):
        calls.append(url)
        return RedirectResponse()

    monkeypatch.setattr(f.requests, "get", fake_get)
    try:
        f.fetch_page(
            "https://docs.example.com/docs/a",
            {"docs.example.com"},
            ("https://docs.example.com/docs/",),
        )
    except f.index.IndexError_ as exc:
        assert "host" in str(exc)
    else:
        raise AssertionError("expected redirect rejection")
    assert calls == ["https://docs.example.com/docs/a"]


def test_main_enforces_page_limit(tmp_path):
    manifest = tmp_path / "selection.json"
    manifest.write_text(
        json.dumps(
            {
                "entries": [
                    {"url": "https://docs.example.com/docs/a"},
                    {"url": "https://docs.example.com/docs/b"},
                ]
            }
        ),
        encoding="utf-8",
    )
    assert f.main(["--manifest", str(manifest), "--max-pages", "1"]) == 2
