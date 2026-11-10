"""PPTX 抽出の単体テスト。フィクスチャは zip に最小の OOXML を詰めて作った。"""

from __future__ import annotations

from pathlib import Path

import pytest

from extract_pptx import (
    NoVisibleSlidesError,
    PptxExtractError,
    PptxNotZipError,
    PptxText,
    SlideText,
    extract_pptx,
)

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def test_deck_order_hidden_shapes_table_notes_and_choice() -> None:
    """deck.pptx は sldIdLst の順がファイル名順と違う最小 OOXML。非表示・図形・表・ノートを含む。"""
    assert extract_pptx(FIXTURES / "deck.pptx") == PptxText(
        slides=(
            SlideText(number=1, text="First\nFIELD", notes="Speaker"),
            SlideText(number=2, text="Second", notes=""),
            SlideText(
                number=5,
                text="Grouped\nCell1\nCell2\nLine1\nLine2\nFromChoice",
                notes="",
            ),
            SlideText(number=6, text="Trim", notes=""),
            SlideText(number=7, text="A  B", notes=""),
        ),
        hidden_count=2,
    )


def test_whitespace_only_slide_is_empty() -> None:
    """blank.pptx は空白だけの a:t を1枚の表示スライドに置いた最小 OOXML。"""
    document = extract_pptx(FIXTURES / "blank.pptx")
    assert document.hidden_count == 0
    assert document.slides == (SlideText(number=1, text="", notes=""),)


def test_all_hidden_slides_raise() -> None:
    """all-hidden.pptx は show=0 と show=false の2枚だけの最小 OOXML。"""
    with pytest.raises(NoVisibleSlidesError):
        extract_pptx(FIXTURES / "all-hidden.pptx")


def test_ole_container_is_not_zip() -> None:
    """not-zip.pptx は OLE 複合文書の先頭バイト。暗号化とは断定しない。"""
    with pytest.raises(PptxNotZipError):
        extract_pptx(FIXTURES / "not-zip.pptx")


def test_broken_xml_raises() -> None:
    """broken.pptx は presentation.xml が XML ではない zip。"""
    with pytest.raises(PptxExtractError, match="ParseError"):
        extract_pptx(FIXTURES / "broken.pptx")
