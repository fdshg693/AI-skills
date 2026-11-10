"""Tests for scripts/grep_doc_sections.py (grep-with-URL-attribution template)."""

from __future__ import annotations

import re

import grep_doc_sections as gds

H1_RE = re.compile(gds.DEFAULT_H1_PATTERN)
SOURCE_RE = re.compile(gds.DEFAULT_SOURCE_PATTERN)


def test_scan_attributes_each_match_to_its_source_url(fixtures_dir):
    pattern = re.compile(r"ERROR_CODE_\d+")
    matches, total = gds.scan(
        fixtures_dir / "sample_llms_full.txt", pattern, H1_RE, SOURCE_RE, max_matches=200
    )

    assert total == 3
    urls = [url for _lineno, _text, _title, url in matches]
    assert urls == [
        "https://example.com/docs/quickstart",
        "https://example.com/docs/guides/auth",
        "https://example.com/docs/reference/api",
    ]


def test_scan_respects_max_matches_truncation(fixtures_dir):
    pattern = re.compile(r"ERROR_CODE_\d+")
    matches, total = gds.scan(
        fixtures_dir / "sample_llms_full.txt", pattern, H1_RE, SOURCE_RE, max_matches=1
    )
    assert len(matches) == 1
    assert total == 3


def test_find_current_section_ignores_stray_heading_without_source():
    lines = ["# Stray heading with no source line nearby", "some unrelated body text"]
    assert gds.find_current_section(lines, 0, H1_RE, SOURCE_RE) is None


def test_main_groups_output_by_url(fixtures_dir, monkeypatch, capsys):
    monkeypatch.setattr(
        "sys.argv",
        [
            "grep_doc_sections.py",
            "ERROR_CODE_401",
            "--input",
            str(fixtures_dir / "sample_llms_full.txt"),
        ],
    )
    exit_code = gds.main()
    out = capsys.readouterr().out

    assert exit_code == 0
    assert "== https://example.com/docs/guides/auth (Authentication) ==" in out
    assert "ERROR_CODE_401" in out
    assert "1 match(es) shown" in out


def test_main_reports_no_matches(fixtures_dir, monkeypatch, capsys):
    monkeypatch.setattr(
        "sys.argv",
        [
            "grep_doc_sections.py",
            "NO_SUCH_PATTERN",
            "--input",
            str(fixtures_dir / "sample_llms_full.txt"),
        ],
    )
    exit_code = gds.main()
    assert exit_code == 1
    assert "No matches for" in capsys.readouterr().out


def test_main_fixed_strings_mode_treats_pattern_as_literal(fixtures_dir, monkeypatch, capsys):
    monkeypatch.setattr(
        "sys.argv",
        [
            "grep_doc_sections.py",
            "ERROR_CODE_\\d+",
            "--input",
            str(fixtures_dir / "sample_llms_full.txt"),
            "--fixed-strings",
        ],
    )
    exit_code = gds.main()
    assert exit_code == 1
    assert "No matches for" in capsys.readouterr().out
