"""Tests for scripts/check_llms_excerpt.py (excerpt validation/drift-detection template)."""

from __future__ import annotations

import check_llms_excerpt as cle


def test_strip_frontmatter_removes_yaml_block():
    text = "---\nsource: x\n---\n\nbody line"
    assert cle.strip_frontmatter(text) == "\nbody line"


def test_strip_frontmatter_returns_text_unchanged_without_frontmatter():
    text = "no frontmatter here"
    assert cle.strip_frontmatter(text) == text


def test_parse_entries_separates_malformed_lines():
    text = "- [Title](https://example.com/a): desc\n- not a real entry\n"
    entries, malformed = cle.parse_entries(text)
    assert entries == [{"title": "Title", "url": "https://example.com/a", "desc": "desc"}]
    assert malformed == ["- not a real entry"]


def test_looks_candidate_matches_any_keyword():
    entry = {"title": "Webhooks", "url": "https://example.com/x", "desc": "event callbacks"}
    original = cle.CANDIDATE_KEYWORDS
    try:
        cle.CANDIDATE_KEYWORDS = ("webhook",)
        assert cle.looks_candidate(entry) is True
        cle.CANDIDATE_KEYWORDS = ("nomatch",)
        assert cle.looks_candidate(entry) is False
    finally:
        cle.CANDIDATE_KEYWORDS = original


def test_main_ok_excerpt_passes_clean(fixtures_dir, monkeypatch, capsys):
    monkeypatch.setattr(
        "sys.argv",
        [
            "check_llms_excerpt.py",
            "--excerpt",
            str(fixtures_dir / "sample_excerpt_ok.md"),
            "--source",
            str(fixtures_dir / "sample_llms.txt"),
        ],
    )
    exit_code = cle.main()
    out = capsys.readouterr().out

    assert exit_code == 0
    assert "MALFORMED" not in out
    assert "MISSING" not in out
    assert "TITLE MISMATCH" not in out
    assert "OK: excerpt format is valid" in out


def test_main_broken_excerpt_reports_every_problem_category(fixtures_dir, monkeypatch, capsys):
    monkeypatch.setattr(
        "sys.argv",
        [
            "check_llms_excerpt.py",
            "--excerpt",
            str(fixtures_dir / "sample_excerpt_broken.md"),
            "--source",
            str(fixtures_dir / "sample_llms.txt"),
        ],
    )
    exit_code = cle.main()
    out = capsys.readouterr().out

    assert exit_code == 1
    assert "MALFORMED (1)" in out
    assert "this line has no markdown link syntax" in out
    assert "MISSING (1)" in out
    assert "Removed Page" in out
    assert "TITLE MISMATCH (1)" in out
    assert "Auth Setup" in out
    assert "DESCRIPTION DRIFT (1" in out
    assert "STALE" in out


def test_main_errors_when_source_missing(tmp_path, fixtures_dir, monkeypatch):
    monkeypatch.setattr(
        "sys.argv",
        [
            "check_llms_excerpt.py",
            "--excerpt",
            str(fixtures_dir / "sample_excerpt_ok.md"),
            "--source",
            str(tmp_path / "missing.txt"),
        ],
    )
    assert cle.main() == 2


def test_main_errors_when_excerpt_missing(tmp_path, fixtures_dir, monkeypatch):
    monkeypatch.setattr(
        "sys.argv",
        [
            "check_llms_excerpt.py",
            "--excerpt",
            str(tmp_path / "missing.md"),
            "--source",
            str(fixtures_dir / "sample_llms.txt"),
        ],
    )
    assert cle.main() == 2
