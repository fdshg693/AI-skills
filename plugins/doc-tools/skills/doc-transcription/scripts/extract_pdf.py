"""pypdf で PDF の選択可能なテキストをページ順に取り出す。"""

from __future__ import annotations

from pathlib import Path

from pypdf import PasswordType, PdfReader
from pypdf.errors import DependencyError, PyPdfError


class PdfExtractError(Exception):
    """PDF を読めなかった。呼び出し側が終了コード 1 にする。"""


class PasswordProtectedPdfError(PdfExtractError):
    """空のユーザーパスワードでは復号できない。"""


def extract_pdf(path: Path) -> list[str]:
    """文書順の本文を返す。各要素は前後の空白だけを除いた文字列で、空ページは空文字。

    `password=""` は暗号化されていない PDF でも PdfReadError になるため渡さない。
    暗号化されているときだけ `decrypt("")` を呼び、戻り値で成否を見る。
    `decrypt` は失敗しても例外を出さない。
    """
    try:
        # strict は既定の False。壊れていても警告だけで読み進む場合がある。
        reader = PdfReader(path)
        if reader.is_encrypted:
            decrypted = reader.decrypt("")
            if decrypted == PasswordType.NOT_DECRYPTED:
                raise PasswordProtectedPdfError
        pages: list[str] = []
        for page in reader.pages:
            pages.append((page.extract_text() or "").strip())
        return pages
    except PdfExtractError:
        raise
    except (PyPdfError, DependencyError, NotImplementedError, OSError) as exc:
        raise PdfExtractError(f"{type(exc).__name__}: {exc}") from exc
