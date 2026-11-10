"""CLI の終了コード、出力先、ファイル名、UTF-8。フィクスチャの作り方は抽出テストと同じ。"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

from doc_transcription import (
    MIN_NONSPACE_CHARS,
    MSG_NO_SLIDES,
    MSG_NO_TEXT,
    MSG_NOT_ZIP,
    MSG_PASSWORD,
    MSG_TEMP_FILE,
    main,
    output_path_for,
    path_hash_key,
)
from extract_pdf import extract_pdf
from extract_pptx import extract_pptx

FIXTURES = Path(__file__).resolve().parent / "fixtures"
SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "doc_transcription.py"
_NAME = re.compile(r"^[A-Za-z0-9]+-[0-9a-f]{8}\.md$")


def test_threshold_is_one_nonspace_character() -> None:
    """blank.pdf と blank.pptx は空白だけ。非空白 0 文字なので閾値 1 未満になる。"""
    assert MIN_NONSPACE_CHARS == 1
    assert extract_pdf(FIXTURES / "blank.pdf") == [""]
    assert extract_pptx(FIXTURES / "blank.pptx").slides[0].text == ""


def test_writes_markdown_and_prints_absolute_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """pages.pdf は Helvetica の Tj で3ページを手書きした PDF。"""
    monkeypatch.chdir(tmp_path)
    source = tmp_path / "pages.pdf"
    source.write_bytes((FIXTURES / "pages.pdf").read_bytes())

    assert main([str(source)]) == 0

    captured = capsys.readouterr()
    assert captured.err == ""
    assert captured.out.count("\n") == 1
    written = Path(captured.out.strip())
    assert written.is_file()
    assert written.parent == (tmp_path / "temp" / "doc-transcription").resolve()
    assert _NAME.fullmatch(written.name)
    assert written.name.startswith("pages-")
    assert written.read_text(encoding="utf-8") == (
        "pages.pdf（テキスト抽出であり、レイアウトの再現ではない）\n"
        "\n"
        "## ページ 1\n"
        "\n"
        "Alpha\n"
        "\n"
        "## ページ 2\n"
        "\n"
        "## ページ 3\n"
        "\n"
        "A  B\n"
    )
    assert list(source.parent.glob("*.md")) == []


def test_pptx_markdown_skips_hidden_slides(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """deck.pptx は非表示2枚を含む最小 OOXML。番号はデッキ内の位置のまま。"""
    monkeypatch.chdir(tmp_path)
    source = tmp_path / "deck.pptx"
    source.write_bytes((FIXTURES / "deck.pptx").read_bytes())

    assert main([str(source)]) == 0

    text = Path(capsys.readouterr().out.strip()).read_text(encoding="utf-8")
    assert text.startswith("deck.pptx（テキスト抽出であり、レイアウトの再現ではない）\n")
    assert "非表示スライド 2 件を除外\n" in text
    assert "## スライド 1\n" in text
    assert "## スライド 2\n" in text
    assert "## スライド 5\n" in text
    assert "## スライド 3\n" not in text
    assert "### ノート\n" in text
    assert "Speaker" in text
    assert "FromFallback" not in text
    assert "Hidden0" not in text
    assert "NUM" not in text


def test_same_input_overwrites(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """pages.pdf は手書きの3ページ PDF。同じパスの再実行はファイルを増やさない。"""
    monkeypatch.chdir(tmp_path)
    source = tmp_path / "pages.pdf"
    source.write_bytes((FIXTURES / "pages.pdf").read_bytes())
    assert main([str(source)]) == 0
    written = Path(capsys.readouterr().out.strip())
    written.write_text("junk", encoding="utf-8")

    assert main([str(source)]) == 0

    assert capsys.readouterr().out.strip() == str(written)
    assert written.read_text(encoding="utf-8") != "junk"
    assert list(written.parent.glob("*.md")) == [written]


def test_japanese_filename_becomes_document(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """pages.pdf の中身を、英数字の無いファイル名でコピーした。"""
    monkeypatch.chdir(tmp_path)
    source = tmp_path / "議事録.pdf"
    source.write_bytes((FIXTURES / "pages.pdf").read_bytes())

    assert main([str(source)]) == 0

    written = Path(capsys.readouterr().out.strip())
    assert written.name.startswith("document-")
    assert written.read_text(encoding="utf-8").startswith("議事録.pdf（")


def test_extension_case_is_ignored(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """pages.pdf の中身を拡張子 .PDF で置いた。"""
    monkeypatch.chdir(tmp_path)
    source = tmp_path / "Pages.PDF"
    source.write_bytes((FIXTURES / "pages.pdf").read_bytes())
    assert main([str(source)]) == 0
    written = Path(capsys.readouterr().out.strip())
    assert "## ページ 1\n" in written.read_text(encoding="utf-8")


def test_output_name_drops_non_ascii_alnum(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """ファイル名の英数字以外は捨てる。中身は読まない。"""
    monkeypatch.chdir(tmp_path)
    path = output_path_for(Path("会議-notes 1.pdf"))
    assert path.name.startswith("notes1-")
    assert _NAME.fullmatch(path.name)


def test_hash_absorbs_path_case() -> None:
    """ハッシュの入力は normcase した絶対パス。Windows では c:\\ と C:\\ を同じにする。"""
    sample = r"c:\C\ai\File.PDF"
    assert path_hash_key(sample) == path_hash_key(os.path.normcase(os.path.normpath(sample)))
    if os.name == "nt":
        assert path_hash_key(r"c:\C\ai\File.PDF") == path_hash_key(r"C:\C\ai\file.pdf")
        assert path_hash_key(r"c:\C\ai\File.PDF") == path_hash_key("c:/C/ai/File.PDF")


def test_missing_argument_exits_2() -> None:
    """引数が無いときは argparse の使い方エラー。"""
    with pytest.raises(SystemExit) as caught:
        main([])
    assert caught.value.code == 2


def test_missing_file_exits_2(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """存在しないパスは使い方エラー。"""
    assert main([str(tmp_path / "missing.pdf")]) == 2
    assert "ファイルが見つかりません" in capsys.readouterr().err


def test_unsupported_extension_exits_2(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """未対応の拡張子は使い方エラー。"""
    source = tmp_path / "notes.txt"
    source.write_text("hello", encoding="utf-8")
    assert main([str(source)]) == 2
    assert "未対応の拡張子です" in capsys.readouterr().err


def test_office_temp_file_exits_2(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """~$ で始まるファイルは、中身が PPTX でも使い方エラー。暗号化とは区別する。"""
    source = tmp_path / "~$deck.pptx"
    source.write_bytes((FIXTURES / "deck.pptx").read_bytes())
    assert main([str(source)]) == 2
    assert capsys.readouterr().err.strip() == MSG_TEMP_FILE


@pytest.mark.parametrize(
    ("name", "message"),
    [
        ("blank.pdf", MSG_NO_TEXT),
        ("blank.pptx", MSG_NO_TEXT),
        ("all-hidden.pptx", MSG_NO_SLIDES),
        ("password-aes.pdf", MSG_PASSWORD),
        ("not-zip.pptx", MSG_NOT_ZIP),
        ("corrupt.pdf", "PdfStreamError"),
        ("empty.pdf", "EmptyFileError"),
        ("broken.pptx", "ParseError"),
    ],
)
def test_extract_failures_exit_1(
    name: str,
    message: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """失敗時は Markdown を書かず、理由を標準エラーに出して終了コード 1。"""
    monkeypatch.chdir(tmp_path)
    source = tmp_path / name
    source.write_bytes((FIXTURES / name).read_bytes())
    assert main([str(source)]) == 1
    assert message in capsys.readouterr().err
    assert list((tmp_path / "temp").rglob("*.md")) == []


def test_write_error_exits_1(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """pages.pdf は手書き PDF。書き込みの OSError は終了コード 1。"""
    monkeypatch.chdir(tmp_path)
    source = tmp_path / "pages.pdf"
    source.write_bytes((FIXTURES / "pages.pdf").read_bytes())
    original = Path.write_text

    def fail_markdown(self: Path, *args: object, **kwargs: object) -> int:
        if self.suffix == ".md":
            raise OSError("disk full")
        return original(self, *args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(Path, "write_text", fail_markdown)
    assert main([str(source)]) == 1
    assert "書き込みに失敗しました" in capsys.readouterr().err


def test_stdio_is_utf8_for_japanese_path_and_error(tmp_path: Path) -> None:
    """blank.pdf は空白だけの手書き PDF。コンソールが cp932 でも UTF-8 で出す。"""
    work = tmp_path / "出力"
    work.mkdir()
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "cp932"
    failure = subprocess.run(
        [sys.executable, str(SCRIPT), str(FIXTURES / "blank.pdf")],
        cwd=work,
        capture_output=True,
        env=env,
        check=False,
    )
    assert failure.returncode == 1
    assert MSG_NO_TEXT in failure.stderr.decode("utf-8")

    success = subprocess.run(
        [sys.executable, str(SCRIPT), str(FIXTURES / "pages.pdf")],
        cwd=work,
        capture_output=True,
        env=env,
        check=False,
    )
    assert success.returncode == 0
    stdout = success.stdout.decode("utf-8")
    assert "出力" in stdout
    assert stdout.count("\n") == 1
