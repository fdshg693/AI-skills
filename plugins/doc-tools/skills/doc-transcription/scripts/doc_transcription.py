"""PDF / PPTX のテキストを `temp/doc-transcription/` の Markdown に書き出す。

標準出力には、書いたファイルの絶対パスを1行だけ出す。
"""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
from collections.abc import Sequence
from pathlib import Path

from extract_pdf import PasswordProtectedPdfError, PdfExtractError, extract_pdf
from extract_pptx import (
    NoVisibleSlidesError,
    PptxExtractError,
    PptxNotZipError,
    extract_pptx,
)

EXIT_OK = 0
EXIT_EXTRACT = 1
EXIT_USAGE = 2

# 空白だけの合成 PDF / PPTX は、空白を除くと 0 文字だった。
# 非空白が 1 文字でもあれば、テキストを取り出せたものとして書く。
MIN_NONSPACE_CHARS = 1

# 衝突を避け、同じ入力の再実行でファイルが増えないようにする（概要の決定）。
_HASH_HEX_DIGITS = 8

MSG_NO_TEXT = "テキストを取り出せませんでした（画像・スキャンの可能性）"
MSG_NO_SLIDES = "表示されるスライドがありません"
MSG_PASSWORD = "パスワード付きPDFです"
MSG_NOT_ZIP = "ZIPとして開けません（暗号化・旧形式・破損の可能性）"
MSG_TEMP_FILE = "Office の一時ファイル（~$ で始まる）は対象外です"
_DISCLAIMER = "テキスト抽出であり、レイアウトの再現ではない"


def main(argv: Sequence[str] | None = None) -> int:
    configure_stdio()
    parser = argparse.ArgumentParser(
        prog="doc-transcription",
        description="PDF または PPTX から選択可能なテキストを Markdown に書き出す。",
    )
    parser.add_argument("path", help="入力ファイル（.pdf / .pptx）")
    args = parser.parse_args(argv)

    source = Path(args.path)
    usage = _usage_error(source)
    if usage is not None:
        print(usage, file=sys.stderr)
        return EXIT_USAGE

    try:
        kind, pages, hidden = _extract(source)
        if _nonspace_length(pages) < MIN_NONSPACE_CHARS:
            print(MSG_NO_TEXT, file=sys.stderr)
            return EXIT_EXTRACT
        destination = _write_markdown(source, kind=kind, pages=pages, hidden=hidden)
    except NoVisibleSlidesError:
        print(MSG_NO_SLIDES, file=sys.stderr)
        return EXIT_EXTRACT
    except PasswordProtectedPdfError:
        print(MSG_PASSWORD, file=sys.stderr)
        return EXIT_EXTRACT
    except PptxNotZipError:
        print(MSG_NOT_ZIP, file=sys.stderr)
        return EXIT_EXTRACT
    except (PdfExtractError, PptxExtractError) as exc:
        print(str(exc), file=sys.stderr)
        return EXIT_EXTRACT
    except OSError as exc:
        print(f"書き込みに失敗しました: {exc}", file=sys.stderr)
        return EXIT_EXTRACT

    print(destination)
    return EXIT_OK


def configure_stdio() -> None:
    """標準出力・標準エラーを UTF-8 に固定する。

    Windows の既定（cp932）のままだと、日本語の本文やファイル名で落ちる。
    """
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8")
        except (OSError, ValueError):
            continue


def path_hash_key(path: str) -> str:
    """絶対パスを正規化し、OS が区別しない大文字小文字を normcase で吸収する。"""
    return os.path.normcase(os.path.normpath(os.path.abspath(path)))


def output_path_for(source: Path) -> Path:
    ascii_stem = "".join(char for char in source.stem if char.isascii() and char.isalnum())
    if not ascii_stem:
        ascii_stem = "document"
    digest = hashlib.sha256(path_hash_key(str(source)).encode("utf-8")).hexdigest()
    return Path("temp") / "doc-transcription" / f"{ascii_stem}-{digest[:_HASH_HEX_DIGITS]}.md"


def render_markdown(
    source_name: str,
    *,
    kind: str,
    pages: Sequence[tuple[int, str, str]],
    hidden: int,
) -> str:
    lines = [f"{source_name}（{_DISCLAIMER}）"]
    if kind == "pptx" and hidden > 0:
        lines.append(f"非表示スライド {hidden} 件を除外")
    lines.append("")
    label = "ページ" if kind == "pdf" else "スライド"
    for number, text, notes in pages:
        lines.append(f"## {label} {number}")
        lines.append("")
        if text:
            lines.append(text)
            lines.append("")
        if notes:
            lines.append("### ノート")
            lines.append("")
            lines.append(notes)
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _usage_error(source: Path) -> str | None:
    if source.name.startswith("~$"):
        return MSG_TEMP_FILE
    if not source.is_file():
        return f"ファイルが見つかりません: {source}"
    if source.suffix.lower() not in {".pdf", ".pptx"}:
        shown = source.suffix or "（拡張子なし）"
        return f"未対応の拡張子です: {shown}"
    return None


def _extract(source: Path) -> tuple[str, list[tuple[int, str, str]], int]:
    if source.suffix.lower() == ".pdf":
        pages = [(number, text, "") for number, text in enumerate(extract_pdf(source), start=1)]
        return "pdf", pages, 0
    document = extract_pptx(source)
    pages = [(slide.number, slide.text, slide.notes) for slide in document.slides]
    return "pptx", pages, document.hidden_count


def _nonspace_length(pages: Sequence[tuple[int, str, str]]) -> int:
    count = 0
    for _number, text, notes in pages:
        count += len("".join(text.split()))
        count += len("".join(notes.split()))
    return count


def _write_markdown(
    source: Path,
    *,
    kind: str,
    pages: Sequence[tuple[int, str, str]],
    hidden: int,
) -> Path:
    destination = output_path_for(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        render_markdown(source.name, kind=kind, pages=pages, hidden=hidden),
        encoding="utf-8",
        newline="\n",
    )
    return destination.resolve()


if __name__ == "__main__":
    sys.exit(main())
