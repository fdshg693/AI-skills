"""PPTX（OOXML）を zip と XML で読み、スライドごとのテキストとノートを返す。"""

from __future__ import annotations

import posixpath
import zipfile
from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree

P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
MC_NS = "http://schemas.openxmlformats.org/markup-compatibility/2006"
PKG_NS = "http://schemas.openxmlformats.org/package/2006/relationships"

SLIDE_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide"
NOTES_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/notesSlide"

# スライド番号・日付・フッター。会社名などのフッター文字は本文から落ちる。
_SKIP_PLACEHOLDERS = frozenset({"sldNum", "dt", "ftr"})


class PptxExtractError(Exception):
    """PPTX を読めなかった。呼び出し側が終了コード 1 にする。"""


class NoVisibleSlidesError(PptxExtractError):
    """表示されるスライドが無い。"""


class PptxNotZipError(PptxExtractError):
    """zip として開けない。暗号化された OOXML とは断定しない。"""


@dataclass(frozen=True)
class SlideText:
    """デッキ内の元の位置（1 始まり）。非表示を詰めた番号ではない。"""

    number: int
    text: str
    notes: str


@dataclass(frozen=True)
class PptxText:
    slides: tuple[SlideText, ...]
    hidden_count: int


def extract_pptx(path: Path) -> PptxText:
    """表示順に、表示中のスライドだけを返す。非表示は件数だけ数える。"""
    try:
        with zipfile.ZipFile(path) as archive:
            return _read_archive(archive)
    except zipfile.BadZipFile as exc:
        raise PptxNotZipError from exc
    except NoVisibleSlidesError:
        raise
    except PptxExtractError:
        raise
    except (ElementTree.ParseError, OSError, KeyError) as exc:
        raise PptxExtractError(f"{type(exc).__name__}: {exc}") from exc


def _read_archive(archive: zipfile.ZipFile) -> PptxText:
    presentation = _parse(archive, "ppt/presentation.xml")
    relationships = _relationships(archive, "ppt/_rels/presentation.xml.rels")
    slide_list = presentation.find(_q(P_NS, "sldIdLst"))
    parts: list[str] = []
    if slide_list is not None:
        for slide_id in slide_list.findall(_q(P_NS, "sldId")):
            rel_id = slide_id.get(_q(R_NS, "id"))
            if rel_id is None or rel_id not in relationships:
                raise PptxExtractError("スライドの relationship がありません")
            rel_type, target, mode = relationships[rel_id]
            if rel_type != SLIDE_REL or mode == "External":
                raise PptxExtractError("スライドの relationship が不正です")
            parts.append(_resolve_part("ppt/presentation.xml", target))

    slides: list[SlideText] = []
    hidden_count = 0
    for number, part in enumerate(parts, start=1):
        root = _parse(archive, part)
        if _is_hidden(root):
            hidden_count += 1
            continue
        slides.append(
            SlideText(
                number=number,
                text=_slide_text(root),
                notes=_notes_text(archive, part),
            )
        )
    if not slides:
        raise NoVisibleSlidesError
    return PptxText(slides=tuple(slides), hidden_count=hidden_count)


def _is_hidden(slide: ElementTree.Element) -> bool:
    # XSD の boolean は `0` と `false`。省略時は表示。
    return slide.get("show") in {"0", "false"}


def _slide_text(root: ElementTree.Element) -> str:
    tree = _first(root, _q(P_NS, "spTree"))
    if tree is None:
        return ""
    return _join(_paragraphs(tree))


def _notes_text(archive: zipfile.ZipFile, slide_part: str) -> str:
    rels_name = _rels_name(slide_part)
    if rels_name not in archive.namelist():
        return ""
    for rel_type, target, mode in _relationships(archive, rels_name).values():
        if rel_type != NOTES_REL or mode == "External":
            continue
        notes_root = _parse(archive, _resolve_part(slide_part, target))
        tree = _first(notes_root, _q(P_NS, "spTree"))
        if tree is None:
            return ""
        paragraphs: list[str] = []
        for shape in _shapes(tree):
            # type を省略したプレースホルダは obj であり、body ではない。
            if _placeholder_type(shape) != "body":
                continue
            paragraphs.extend(_tx_body_paragraphs(_child(shape, P_NS, "txBody")))
        return _join(paragraphs)
    return ""


def _paragraphs(container: ElementTree.Element) -> list[str]:
    paragraphs: list[str] = []
    for child in _choice_children(container):
        tag = child.tag
        if tag in {_q(P_NS, "sp"), _q(P_NS, "cxnSp")}:
            if _placeholder_type(child) in _SKIP_PLACEHOLDERS:
                continue
            paragraphs.extend(_tx_body_paragraphs(_child(child, P_NS, "txBody")))
        elif tag == _q(P_NS, "grpSp"):
            paragraphs.extend(_paragraphs(child))
        elif tag == _q(P_NS, "graphicFrame"):
            paragraphs.extend(_table_paragraphs(child))
    return paragraphs


def _shapes(container: ElementTree.Element) -> list[ElementTree.Element]:
    found: list[ElementTree.Element] = []
    for child in _choice_children(container):
        tag = child.tag
        if tag in {_q(P_NS, "sp"), _q(P_NS, "cxnSp")}:
            found.append(child)
        elif tag == _q(P_NS, "grpSp"):
            found.extend(_shapes(child))
    return found


def _table_paragraphs(frame: ElementTree.Element) -> list[str]:
    paragraphs: list[str] = []
    for table in _find(frame, _q(A_NS, "tbl")):
        for row in _choice_children(table):
            if row.tag != _q(A_NS, "tr"):
                continue
            for cell in _choice_children(row):
                if cell.tag != _q(A_NS, "tc"):
                    continue
                paragraphs.extend(_tx_body_paragraphs(_child(cell, A_NS, "txBody")))
    return paragraphs


def _tx_body_paragraphs(tx_body: ElementTree.Element | None) -> list[str]:
    if tx_body is None:
        return []
    return [
        _paragraph_text(paragraph)
        for paragraph in _choice_children(tx_body)
        if paragraph.tag == _q(A_NS, "p")
    ]


def _paragraph_text(paragraph: ElementTree.Element) -> str:
    parts: list[str] = []
    for child in _choice_children(paragraph):
        if child.tag in {_q(A_NS, "r"), _q(A_NS, "fld")}:
            parts.append(_run_text(child))
        elif child.tag == _q(A_NS, "br"):
            parts.append("\n")
    return "".join(parts)


def _run_text(run: ElementTree.Element) -> str:
    return "".join(
        child.text or "" for child in _choice_children(run) if child.tag == _q(A_NS, "t")
    )


def _placeholder_type(shape: ElementTree.Element) -> str | None:
    nv_pr = shape.find(f"{_q(P_NS, 'nvSpPr')}/{_q(P_NS, 'nvPr')}")
    if nv_pr is None:
        return None
    placeholder = nv_pr.find(_q(P_NS, "ph"))
    if placeholder is None:
        return None
    return placeholder.get("type")


def _first(element: ElementTree.Element, tag: str) -> ElementTree.Element | None:
    found = _find(element, tag)
    if not found:
        return None
    return found[0]


def _find(element: ElementTree.Element, tag: str) -> list[ElementTree.Element]:
    found: list[ElementTree.Element] = []

    def walk(node: ElementTree.Element) -> None:
        for child in _choice_children(node):
            if child.tag == tag:
                found.append(child)
                continue
            walk(child)

    walk(element)
    return found


def _choice_children(element: ElementTree.Element):
    """`mc:Choice` だけを辿り、`mc:Fallback` は読まない。"""
    for child in list(element):
        if child.tag != _q(MC_NS, "AlternateContent"):
            yield child
            continue
        choice = _child(child, MC_NS, "Choice")
        if choice is not None:
            yield from _choice_children(choice)


def _child(element: ElementTree.Element, namespace: str, name: str) -> ElementTree.Element | None:
    for child in _choice_children(element):
        if child.tag == _q(namespace, name):
            return child
    return None


def _join(paragraphs: list[str]) -> str:
    return "\n".join(paragraphs).strip()


def _parse(archive: zipfile.ZipFile, name: str) -> ElementTree.Element:
    try:
        payload = archive.read(name)
    except KeyError as exc:
        raise PptxExtractError(f"必要なパートがありません: {name}") from exc
    return ElementTree.fromstring(payload)


def _relationships(archive: zipfile.ZipFile, name: str) -> dict[str, tuple[str, str, str | None]]:
    root = _parse(archive, name)
    relationships: dict[str, tuple[str, str, str | None]] = {}
    for child in root.findall(_q(PKG_NS, "Relationship")):
        rel_id = child.get("Id")
        rel_type = child.get("Type")
        target = child.get("Target")
        if rel_id and rel_type and target:
            relationships[rel_id] = (rel_type, target, child.get("TargetMode"))
    return relationships


def _rels_name(part: str) -> str:
    directory, filename = posixpath.split(part)
    return posixpath.join(directory, "_rels", filename + ".rels")


def _resolve_part(base_part: str, target: str) -> str:
    if target.startswith("/"):
        resolved = posixpath.normpath(target.lstrip("/"))
    else:
        resolved = posixpath.normpath(posixpath.join(posixpath.dirname(base_part), target))
    if resolved.startswith("..") or resolved in {"", "."}:
        raise PptxExtractError("パートのパスが不正です")
    return resolved


def _q(namespace: str, name: str) -> str:
    return f"{{{namespace}}}{name}"
