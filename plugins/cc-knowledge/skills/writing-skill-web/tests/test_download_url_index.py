"""Tests for the sitemap/llms.txt URL-index template."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import download_url_index as d
import pytest


def test_parse_namespaced_urlset_deduplicates_fragments(fixtures_dir):
    body = (fixtures_dir / "sample_sitemap.xml").read_text(encoding="utf-8")
    entries, children = d.parse_index(body, "https://docs.example.com/sitemap.xml")
    assert children == []
    assert [entry.url for entry in entries] == [
        "https://docs.example.com/docs/Router",
        "https://docs.example.com/docs/providers/openai",
    ]
    assert entries[0].lastmod == "2026-09-01"


def test_parse_nested_sitemap_index():
    body = """<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><sitemap><loc>child.xml</loc></sitemap></sitemapindex>"""
    kind, children = d.parse_sitemap_xml(body, "https://docs.example.com/root.xml")
    assert kind == "index"
    assert children == ["https://docs.example.com/child.xml"]


def test_parse_llms_text_retains_titles_and_descriptions(fixtures_dir):
    body = (fixtures_dir / "sample_llms_index.txt").read_text(encoding="utf-8")
    entries = d.parse_llms_text(body, "https://docs.example.com/llms.txt")
    assert [entry.url for entry in entries] == [
        "https://docs.example.com/docs/Router",
        "https://docs.example.com/docs/proxy",
        "https://docs.example.com/docs/observability",
    ]
    assert entries[0].description == "Configure routing."


def test_download_entries_follows_sitemap_children(monkeypatch, fixtures_dir):
    bodies = {
        "https://docs.example.com/sitemapindex.xml": (
            fixtures_dir / "sample_sitemapindex.xml"
        ).read_text(),
        "https://docs.example.com/sitemap-a.xml": (
            fixtures_dir / "sample_sitemap_a.xml"
        ).read_text(),
        "https://docs.example.com/sitemap-b.xml": (
            fixtures_dir / "sample_sitemap_b.xml"
        ).read_text(),
    }

    class Response:
        def __init__(self, url, text):
            self.url = url
            self.text = text
            self.content = text.encode()

        def raise_for_status(self):
            return None

    monkeypatch.setattr(
        d.requests, "get", lambda url, timeout, **kwargs: Response(url, bodies[url])
    )
    entries = d.download_entries("https://docs.example.com/sitemapindex.xml", {"docs.example.com"})
    assert [entry.url for entry in entries] == [
        "https://docs.example.com/docs/proxy",
        "https://docs.example.com/docs/routing",
    ]


def test_download_entries_rejects_outside_host(monkeypatch):
    monkeypatch.setattr(
        d.requests,
        "get",
        lambda url, timeout, **kwargs: type(
            "Response",
            (),
            {
                "url": url,
                "text": "https://evil.example/a",
                "content": b"https://evil.example/a",
                "raise_for_status": lambda self: None,
            },
        )(),
    )
    with pytest.raises(d.IndexError_, match="host"):
        d.download_entries("https://docs.example.com/llms.txt", {"docs.example.com"})


def test_dtd_is_rejected():
    with pytest.raises(d.IndexError_, match="DTD"):
        d.parse_sitemap_xml("<!DOCTYPE urlset><urlset />", "https://docs.example.com/sitemap.xml")


def test_private_ipv6_url_is_rejected():
    with pytest.raises(d.IndexError_, match="private"):
        d.validate_url("https://[::1]/sitemap.xml", {"::1"})


def test_tree_includes_counts_and_collapses():
    lines = d.build_url_tree(
        ["https://docs.example.com/docs/a", "https://docs.example.com/docs/b"], max_depth=1
    )
    rendered = "\n".join(lines)
    assert "docs/` (2)" in rendered
    assert "…" in rendered


def test_main_skips_fresh_output(tmp_path, monkeypatch):
    output = tmp_path / "urls.md"
    tree = tmp_path / "tree.md"
    fetched_at = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    output.write_text(f"---\nfetched_at: {fetched_at}\n---\n", encoding="utf-8")
    tree.write_text("# URL Tree\n", encoding="utf-8")
    monkeypatch.setattr(
        d, "download_entries", lambda *args, **kwargs: pytest.fail("must not fetch")
    )
    assert (
        d.main(
            [
                "--url",
                "https://docs.example.com/sitemap.xml",
                "--output",
                str(output),
                "--tree-output",
                str(tree),
            ]
        )
        == 0
    )
