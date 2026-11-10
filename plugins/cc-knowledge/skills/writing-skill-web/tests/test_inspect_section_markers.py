"""Tests for scripts/inspect_section_markers.py (structure-sampling template)."""

from __future__ import annotations

import inspect_section_markers as ism


def test_scan_finds_all_heading_source_pairs(fixtures_dir):
    h1_hits, source_hits = ism.scan(
        fixtures_dir / "sample_llms_full.txt",
        ism.DEFAULT_H1_PATTERN,
        ism.DEFAULT_SOURCE_PATTERN,
        limit=10,
    )

    assert [text for _, text in h1_hits] == ["# Quickstart", "# Authentication", "# API Reference"]
    assert [text for _, text in source_hits] == [
        "Source: https://example.com/docs/quickstart",
        "Source: https://example.com/docs/guides/auth",
        "Source: https://example.com/docs/reference/api",
    ]


def test_scan_respects_limit(fixtures_dir):
    h1_hits, source_hits = ism.scan(
        fixtures_dir / "sample_llms_full.txt",
        ism.DEFAULT_H1_PATTERN,
        ism.DEFAULT_SOURCE_PATTERN,
        limit=1,
    )
    assert len(h1_hits) == 1
    assert len(source_hits) == 1


def test_main_reports_consistent_pattern(fixtures_dir, monkeypatch, capsys):
    monkeypatch.setattr(
        "sys.argv", ["inspect_section_markers.py", str(fixtures_dir / "sample_llms_full.txt")]
    )
    ism.main()
    out = capsys.readouterr().out
    assert "Looks consistent" in out


def test_main_reports_inconsistent_pattern_for_stray_heading(tmp_path, monkeypatch, capsys):
    broken = tmp_path / "broken.txt"
    broken.write_text(
        "# Real Section\nSource: https://example.com/a\n\nbody with a stray heading below\n"
        "# Using sed (macOS)\nnot a source line at all\n",
        encoding="utf-8",
    )
    monkeypatch.setattr("sys.argv", ["inspect_section_markers.py", str(broken)])
    ism.main()
    out = capsys.readouterr().out
    assert "Inconsistent pairing detected" in out


def test_main_raises_for_missing_file(tmp_path, monkeypatch):
    monkeypatch.setattr("sys.argv", ["inspect_section_markers.py", str(tmp_path / "missing.txt")])
    try:
        ism.main()
        assert False, "expected SystemExit"
    except SystemExit as exc:
        assert "File not found" in str(exc)
