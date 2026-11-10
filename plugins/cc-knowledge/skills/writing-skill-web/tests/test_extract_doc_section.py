"""Tests for scripts/extract_doc_section.py (per-URL section extraction template)."""

from __future__ import annotations

import extract_doc_section as eds

BASE_URL = "https://example.com/docs/"


def test_parse_sections_splits_on_heading_source_pairs(fixtures_dir):
    text = (fixtures_dir / "sample_llms_full.txt").read_text(encoding="utf-8")
    sections = eds.parse_sections(text)

    assert set(sections) == {
        "https://example.com/docs/quickstart",
        "https://example.com/docs/guides/auth",
        "https://example.com/docs/reference/api",
    }
    title, source, body = sections["https://example.com/docs/guides/auth"]
    assert title == "Authentication"
    assert "ERROR_CODE_401" in body


def test_resolve_url_from_slug_and_full_url_and_strips_md_suffix():
    assert eds.resolve_url("quickstart", BASE_URL) == "https://example.com/docs/quickstart"
    assert eds.resolve_url("guides/auth.md", BASE_URL) == "https://example.com/docs/guides/auth"
    assert eds.resolve_url("https://other.example.com/x", BASE_URL) == "https://other.example.com/x"


def test_slug_from_url_keeps_full_path_to_avoid_collisions():
    slug_a = eds.slug_from_url("https://example.com/docs/client-sdks/go/README", BASE_URL)
    slug_b = eds.slug_from_url("https://example.com/docs/client-sdks/python/README", BASE_URL)
    assert slug_a != slug_b
    assert slug_a == "client-sdks__go__README"
    assert slug_b == "client-sdks__python__README"


def test_main_extracts_known_pages_and_writes_full_text(
    fixtures_dir, tmp_path, monkeypatch, capsys
):
    output_dir = tmp_path / "temp"
    monkeypatch.setattr(
        "sys.argv",
        [
            "extract_doc_section.py",
            "quickstart",
            "--input",
            str(fixtures_dir / "sample_llms_full.txt"),
            "--base-url",
            BASE_URL,
            "--output-dir",
            str(output_dir),
            "--no-summarize",
        ],
    )
    eds.main()

    out_file = output_dir / "quickstart.txt"
    assert out_file.is_file()
    text = out_file.read_text(encoding="utf-8")
    assert "# Quickstart" in text
    assert "ERROR_CODE_100" in text
    assert f"Wrote {out_file}" in capsys.readouterr().out


def test_main_reports_unknown_url(fixtures_dir, tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(
        "sys.argv",
        [
            "extract_doc_section.py",
            "no-such-page",
            "--input",
            str(fixtures_dir / "sample_llms_full.txt"),
            "--base-url",
            BASE_URL,
            "--output-dir",
            str(tmp_path / "temp"),
        ],
    )
    eds.main()
    assert "Not found: https://example.com/docs/no-such-page" in capsys.readouterr().out


def test_main_summarizes_when_body_exceeds_threshold(fixtures_dir, tmp_path, monkeypatch, capsys):
    output_dir = tmp_path / "temp"
    monkeypatch.setattr(
        eds, "summarize_via_aim", lambda model, title, source, body: "SHORT SUMMARY TEXT"
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "extract_doc_section.py",
            "guides/auth",
            "--input",
            str(fixtures_dir / "sample_llms_full.txt"),
            "--base-url",
            BASE_URL,
            "--output-dir",
            str(output_dir),
            "--summarize-threshold",
            "10",
        ],
    )
    eds.main()

    full_text_path = output_dir / "guides__auth.txt"
    summary_path = output_dir / "guides__auth.summary.md"
    assert full_text_path.is_file()
    assert summary_path.is_file()

    summary_text = summary_path.read_text(encoding="utf-8")
    assert "SHORT SUMMARY TEXT" in summary_text
    assert f"full_text: {full_text_path.name}" in summary_text

    out = capsys.readouterr().out
    assert "calling aim --model" in out
    assert str(full_text_path) in out


def test_main_falls_back_to_full_text_when_summarization_fails(
    fixtures_dir, tmp_path, monkeypatch, capsys
):
    output_dir = tmp_path / "temp"

    def failing_summarize(model, title, source, body):
        raise RuntimeError("`aim` CLI not found on PATH")

    monkeypatch.setattr(eds, "summarize_via_aim", failing_summarize)
    monkeypatch.setattr(
        "sys.argv",
        [
            "extract_doc_section.py",
            "reference/api",
            "--input",
            str(fixtures_dir / "sample_llms_full.txt"),
            "--base-url",
            BASE_URL,
            "--output-dir",
            str(output_dir),
            "--summarize-threshold",
            "10",
        ],
    )
    eds.main()

    assert (output_dir / "reference__api.txt").is_file()
    assert not (output_dir / "reference__api.summary.md").exists()
    assert "WARNING: summarization failed" in capsys.readouterr().err
