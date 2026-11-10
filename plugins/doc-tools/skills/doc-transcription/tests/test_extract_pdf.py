"""PDF 抽出の単体テスト。フィクスチャは手書きの最小 PDF と、pypdf で AES-128 にしたもの。"""

from __future__ import annotations

from pathlib import Path

import pytest
from pypdf.errors import DependencyError, PyPdfError

from extract_pdf import PasswordProtectedPdfError, PdfExtractError, extract_pdf

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def test_pages_keep_order_blank_page_and_internal_spaces() -> None:
    """pages.pdf は Helvetica の Tj で「  Alpha  」「   」「A  B」の3ページを手書きした。"""
    assert extract_pdf(FIXTURES / "pages.pdf") == ["Alpha", "", "A  B"]


def test_whitespace_only_page_is_empty() -> None:
    """blank.pdf は空白だけの Tj を1ページに置いた手書き PDF。"""
    assert extract_pdf(FIXTURES / "blank.pdf") == [""]


def test_empty_user_password_opens_aes_pdf() -> None:
    """empty-password-aes.pdf は Opened の手書き PDF を、ユーザーパスワード空の AES-128 で暗号化した。"""
    assert extract_pdf(FIXTURES / "empty-password-aes.pdf") == ["Opened"]


def test_user_password_is_rejected() -> None:
    """password-aes.pdf は Secret の手書き PDF を、ユーザーパスワード secret の AES-128 で暗号化した。"""
    with pytest.raises(PasswordProtectedPdfError):
        extract_pdf(FIXTURES / "password-aes.pdf")


def test_corrupt_pdf_raises() -> None:
    """corrupt.pdf は PDF ではない短いバイト列。"""
    with pytest.raises(PdfExtractError, match="PdfStreamError"):
        extract_pdf(FIXTURES / "corrupt.pdf")


def test_empty_file_raises() -> None:
    """empty.pdf は 0 バイト。"""
    with pytest.raises(PdfExtractError, match="EmptyFileError"):
        extract_pdf(FIXTURES / "empty.pdf")


@pytest.mark.parametrize(
    "exc_type",
    [PyPdfError, DependencyError, NotImplementedError, OSError],
)
def test_reader_errors_are_wrapped(
    monkeypatch: pytest.MonkeyPatch, exc_type: type[Exception]
) -> None:
    """暗号化方式の未対応などは、ファイルを作らず PdfReader を差し替えて包む。"""

    class Boom:
        def __init__(self, _path: Path) -> None:
            raise exc_type("boom")

    monkeypatch.setattr("extract_pdf.PdfReader", Boom)
    with pytest.raises(PdfExtractError, match="boom"):
        extract_pdf(Path("unused.pdf"))
