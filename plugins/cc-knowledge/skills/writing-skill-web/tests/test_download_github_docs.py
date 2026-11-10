"""Tests for scripts/download_github_docs.py (GitHub docs mirror via `gh api`)."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone

import download_github_docs as dgd
import pytest

REPO = "acme/widgets"

PAGES = {
    "docs/index.md": "---\ntitle: Welcome\ndescription: Start here\n---\n\nhello\n",
    "docs/guides/setup.mdx": "---\ntitle: 'Setup'\n---\nbody\n",
    "docs/guides/notes.txt": "not a doc",
    "docs/summary.md": "- [Home](index.md)\n- [Setup](guides/setup.mdx#top)\n"
    "- [Ext](https://example.com/x.md)\n- [Up](../README.md)\n- [Home again](./index.md)\n",
    "README.md": "outside docs root",
}


def make_fake_gh(truncated: bool = False, calls: list | None = None):
    def fake_run_gh(args, what):
        if calls is not None:
            calls.append(args)
        endpoint = args[1]
        path, _, _query = endpoint.partition("?")
        if path == f"repos/{REPO}/git/trees/main":
            tree = [{"path": p, "type": "blob"} for p in PAGES]
            tree.append({"path": "docs/guides", "type": "tree"})
            return json.dumps({"tree": tree, "truncated": truncated})
        prefix = f"repos/{REPO}/contents/"
        assert path.startswith(prefix)
        repo_path = path[len(prefix) :]
        if "-H" in args:
            return PAGES[repo_path]
        # Contents API directory listing.
        children = {}
        for p in PAGES:
            if p.startswith(repo_path + "/"):
                head = p[len(repo_path) + 1 :].split("/", 1)
                children[head[0]] = "dir" if len(head) > 1 else "file"
        return json.dumps([{"name": n, "type": t} for n, t in children.items()])

    return fake_run_gh


def test_links_from_toc_resolves_relative_and_skips_external_and_escapes():
    body = PAGES["docs/summary.md"]
    assert dgd.links_from_toc("summary.md", body) == ["index.md", "guides/setup.mdx"]
    assert dgd.links_from_toc("sub/toc.md", "[a](../b.md) [c](d.md)") == ["b.md", "sub/d.md"]


def test_parse_frontmatter_fields():
    assert dgd.parse_frontmatter_fields(PAGES["docs/index.md"]) == ("Welcome", "Start here")
    assert dgd.parse_frontmatter_fields("no frontmatter") == ("", "")


def test_download_via_tree(monkeypatch, tmp_path):
    monkeypatch.setattr(dgd, "run_gh", make_fake_gh())
    (tmp_path / "old.md").write_text("stale", encoding="utf-8")
    (tmp_path / "temp").mkdir()
    (tmp_path / "temp" / "keep.txt").write_text("x", encoding="utf-8")

    files = dgd.download_all(REPO, "main", "docs", tmp_path, toc=None)

    assert files == ["summary.md", "guides/setup.mdx", "index.md"]
    assert (tmp_path / "index.md").read_text(encoding="utf-8") == PAGES["docs/index.md"]
    assert not (tmp_path / "old.md").exists()
    assert (tmp_path / "temp" / "keep.txt").exists()
    summary = (tmp_path / "summary.md").read_text(encoding="utf-8")
    assert "- [Welcome](index.md) — Start here" in summary
    assert "- [Setup](guides/setup.mdx)" in summary
    assert f"https://github.com/{REPO}/blob/main/docs/<path>" in summary
    meta = json.loads((tmp_path / "_meta.json").read_text(encoding="utf-8"))
    assert meta["source_repo"] == REPO and meta["files"] == files


def test_truncated_tree_falls_back_to_contents_walk(monkeypatch, tmp_path):
    monkeypatch.setattr(dgd, "run_gh", make_fake_gh(truncated=True))
    files = dgd.download_all(REPO, "main", "docs", tmp_path, toc=None)
    assert sorted(files) == ["guides/setup.mdx", "index.md", "summary.md"]


def test_download_via_toc_fetches_only_linked_pages(monkeypatch, tmp_path):
    calls: list = []
    monkeypatch.setattr(dgd, "run_gh", make_fake_gh(calls=calls))
    files = dgd.download_all(REPO, "main", "docs", tmp_path, toc="summary.md")
    # The upstream TOC named summary.md collides with the generated index; the
    # generated one wins and the TOC is not double-listed.
    assert files == ["summary.md", "index.md", "guides/setup.mdx"]
    assert not any("git/trees" in c[1] for c in calls)


def test_main_skips_when_fresh(monkeypatch, tmp_path, capsys):
    meta = {"fetched_at": datetime.now(timezone.utc).isoformat()}
    (tmp_path / "_meta.json").write_text(json.dumps(meta), encoding="utf-8")
    monkeypatch.setattr(dgd, "run_gh", lambda *a: pytest.fail("should not fetch"))
    monkeypatch.setattr(sys, "argv", ["x", "--repo", REPO, "--output-dir", str(tmp_path)])
    assert dgd.main() == 0
    assert "already fresh" in capsys.readouterr().out


def test_main_refetches_when_stale(monkeypatch, tmp_path):
    old = datetime.now(timezone.utc) - dgd.FRESHNESS - timedelta(minutes=1)
    (tmp_path / "_meta.json").write_text(json.dumps({"fetched_at": old.isoformat()}))
    monkeypatch.setattr(dgd, "run_gh", make_fake_gh())
    monkeypatch.setattr(sys, "argv", ["x", "--repo", REPO, "--output-dir", str(tmp_path)])
    assert dgd.main() == 0
    assert (tmp_path / "index.md").exists()


def test_main_rejects_placeholder_repo(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "argv", ["x", "--output-dir", str(tmp_path)])
    assert dgd.main() == 2


def test_main_reports_gh_errors(monkeypatch, tmp_path, capsys):
    def boom(args, what):
        raise RuntimeError("gh api failed for x: 404")

    monkeypatch.setattr(dgd, "run_gh", boom)
    monkeypatch.setattr(sys, "argv", ["x", "--repo", REPO, "--output-dir", str(tmp_path)])
    assert dgd.main() == 1
    assert "404" in capsys.readouterr().err
