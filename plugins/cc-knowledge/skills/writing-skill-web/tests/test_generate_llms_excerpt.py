"""Tests for scripts/generate_llms_excerpt.py (AI-curated excerpt draft template)."""

from __future__ import annotations

import shutil

import generate_llms_excerpt as gle
import pytest


def test_parse_entries_with_section(fixtures_dir):
    text = (fixtures_dir / "sample_llms.txt").read_text(encoding="utf-8")
    entries = gle.parse_entries_with_section(text)

    assert len(entries) == 7
    assert entries[0] == {
        "title": "Quickstart",
        "url": "https://example.com/docs/quickstart",
        "desc": "Install and run your first example.",
        "section": "Getting Started",
    }
    assert entries[2]["section"] == "Guides"
    assert entries[2]["title"] == "Authentication"


def test_extract_urls_ignores_surrounding_punctuation():
    ai_output = "https://example.com/a\nhttps://example.com/b).\nhttps://example.com/a\n"
    assert gle.extract_urls(ai_output) == {"https://example.com/a", "https://example.com/b"}


def test_build_excerpt_preserves_source_order_and_grouping(fixtures_dir):
    text = (fixtures_dir / "sample_llms.txt").read_text(encoding="utf-8")
    entries = gle.parse_entries_with_section(text)
    included = {"https://example.com/docs/quickstart", "https://example.com/docs/reference/api"}

    excerpt_text, count = gle.build_excerpt(
        entries, included, "sample_llms.txt", "2026-01-01T00:00:00+00:00", "test-model"
    )

    assert count == 2
    assert "## Getting Started" in excerpt_text
    assert "## Reference" in excerpt_text
    assert "## Guides" not in excerpt_text
    assert excerpt_text.index("Quickstart") < excerpt_text.index("API Reference")


def test_main_generates_excerpt_from_fixtures(tmp_path, fixtures_dir, monkeypatch):
    source = tmp_path / "llms.txt"
    prompt = tmp_path / "prompt.md"
    out = tmp_path / "excerpt.md"
    shutil.copy(fixtures_dir / "sample_llms.txt", source)
    shutil.copy(fixtures_dir / "sample_prompt_generate_excerpt.md", prompt)

    monkeypatch.setattr(
        gle,
        "call_aim",
        lambda model, prompt_text, source_text: (
            "https://example.com/docs/quickstart\nhttps://example.com/docs/guides/auth\n"
        ),
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "generate_llms_excerpt.py",
            "--source",
            str(source),
            "--prompt",
            str(prompt),
            "--out",
            str(out),
        ],
    )

    exit_code = gle.main()

    assert exit_code == 0
    excerpt_text = out.read_text(encoding="utf-8")
    assert "Quickstart" in excerpt_text
    assert "Authentication" in excerpt_text
    assert "Rate Limits" not in excerpt_text
    assert "extracted_from_fetched_at: 2026-01-01T00:00:00+00:00" in excerpt_text


def test_main_drops_hallucinated_urls_not_in_source(tmp_path, fixtures_dir, monkeypatch, capsys):
    source = tmp_path / "llms.txt"
    prompt = tmp_path / "prompt.md"
    out = tmp_path / "excerpt.md"
    shutil.copy(fixtures_dir / "sample_llms.txt", source)
    shutil.copy(fixtures_dir / "sample_prompt_generate_excerpt.md", prompt)

    monkeypatch.setattr(
        gle,
        "call_aim",
        lambda model, prompt_text, source_text: (
            "https://example.com/docs/quickstart\nhttps://not-in-source.example/made-up\n"
        ),
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "generate_llms_excerpt.py",
            "--source",
            str(source),
            "--prompt",
            str(prompt),
            "--out",
            str(out),
        ],
    )

    exit_code = gle.main()

    assert exit_code == 0
    stderr = capsys.readouterr().err
    assert "not-in-source.example" in stderr
    assert "not-in-source.example" not in out.read_text(encoding="utf-8")


def test_main_rejects_prompt_with_unfilled_placeholders(tmp_path, fixtures_dir, monkeypatch):
    source = tmp_path / "llms.txt"
    prompt = tmp_path / "prompt.md"
    out = tmp_path / "excerpt.md"
    shutil.copy(fixtures_dir / "sample_llms.txt", source)
    prompt.write_text("Include entries about <<the skill's topic>>.", encoding="utf-8")

    monkeypatch.setattr(
        "sys.argv",
        [
            "generate_llms_excerpt.py",
            "--source",
            str(source),
            "--prompt",
            str(prompt),
            "--out",
            str(out),
        ],
    )
    exit_code = gle.main()

    assert exit_code == 2
    assert not out.exists()


def test_main_refuses_to_overwrite_existing_out_without_force(tmp_path, fixtures_dir, monkeypatch):
    source = tmp_path / "llms.txt"
    prompt = tmp_path / "prompt.md"
    out = tmp_path / "excerpt.md"
    shutil.copy(fixtures_dir / "sample_llms.txt", source)
    shutil.copy(fixtures_dir / "sample_prompt_generate_excerpt.md", prompt)
    out.write_text("existing draft", encoding="utf-8")

    monkeypatch.setattr(
        "sys.argv",
        [
            "generate_llms_excerpt.py",
            "--source",
            str(source),
            "--prompt",
            str(prompt),
            "--out",
            str(out),
        ],
    )
    exit_code = gle.main()

    assert exit_code == 2
    assert out.read_text(encoding="utf-8") == "existing draft"


def test_main_errors_when_source_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "sys.argv",
        [
            "generate_llms_excerpt.py",
            "--source",
            str(tmp_path / "missing.txt"),
            "--prompt",
            str(tmp_path / "prompt.md"),
            "--out",
            str(tmp_path / "excerpt.md"),
        ],
    )
    assert gle.main() == 2
