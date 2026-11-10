"""Tests for URL-index selection manifests."""

from __future__ import annotations

import json

import select_url_index as s


def test_read_and_filter_entries(fixtures_dir):
    entries = s.read_entries(fixtures_dir / "sample_llms_index.txt")
    selected = s.select_entries(
        entries, include_prefixes=["https://docs.example.com/docs/"], keywords=["router"]
    )
    assert [entry["url"] for entry in selected] == ["https://docs.example.com/docs/Router"]


def test_exclude_filters_and_limit():
    entries = [
        {"url": "https://docs.example.com/docs/a", "title": "A", "description": "provider"},
        {"url": "https://docs.example.com/docs/b", "title": "B", "description": "proxy"},
    ]
    selected = s.select_entries(entries, exclude_keywords=["proxy"], limit=1)
    assert [entry["url"] for entry in selected] == ["https://docs.example.com/docs/a"]


def test_write_manifest_is_machine_readable(tmp_path):
    output = tmp_path / "selection.json"
    s.write_manifest(
        output,
        tmp_path / "urls.md",
        [{"url": "https://docs.example.com/docs/a"}],
        {"keyword": ["a"]},
    )
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["schema"] == "url-selection-manifest/v1"
    assert payload["entries"][0]["url"].endswith("/a")
