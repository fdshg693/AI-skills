"""欠落の目安（純関数）。入力は合成 Markdown。"""

from __future__ import annotations

from hints import BODY_START_LINE_THRESHOLD, body_start_line, gap_hints, is_cut_off


def test_no_hints_for_complete_text() -> None:
    text = "# Title\n\nURL: https://example.com/\n\n## Section\n\nA finished sentence.\n"
    assert gap_hints(text, excerpt=False) == ""


def test_excerpt_and_possible_gap_wording() -> None:
    text = "# T\n\n[...] first part. [...] second part.\n"
    assert gap_hints(text, excerpt=True) == "excerpt gaps: 2"
    assert gap_hints(text, excerpt=False) == "possible gaps: 2"


def test_cut_off_mid_sentence() -> None:
    assert is_cut_off("# T\n\nThe company was founded in")
    assert is_cut_off("# T\n\n会社は東京に本社を置き")
    assert gap_hints("# T\n\nThe company was founded in", excerpt=False) == "cut off"


def test_finished_endings_are_not_cut_off() -> None:
    for ending in [
        "文末です。",
        "「引用」",
        "Done.",
        "Really?",
        "(see note)",
        '"quoted"',
        "| a | b |",
        "```",
        "- list item without period",
        "1. numbered item",
        "## Heading",
    ]:
        assert not is_cut_off(f"# T\n\n{ending}\n\n"), ending


def test_empty_text_is_not_cut_off() -> None:
    assert not is_cut_off("")


def test_body_start_line_skips_leading_title() -> None:
    nav = "\n".join(f"- nav {i}" for i in range(40))
    text = f"# Page\n\nURL: x\n\n{nav}\n\n## About us\n\nBody.\n"
    line = body_start_line(text)
    assert line is not None and line >= BODY_START_LINE_THRESHOLD
    assert text.splitlines()[line - 1] == "## About us"
    assert f"body from line {line}" in gap_hints(text, excerpt=False)


def test_early_heading_gives_no_body_hint() -> None:
    text = "# Page\n\n## Intro\n\nBody.\n"
    assert body_start_line(text) == 3
    assert gap_hints(text, excerpt=False) == ""


def test_combined_hints_order() -> None:
    nav = "\n".join(f"- nav {i}" for i in range(40))
    text = f"# Page\n\n{nav}\n\n## Body\n\n[...] and then it stops at"
    hint = gap_hints(text, excerpt=False)
    assert hint.startswith("possible gaps: 1, cut off, body from line ")
