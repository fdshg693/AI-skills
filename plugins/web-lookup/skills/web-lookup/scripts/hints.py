"""Gap hints shown after `(N chars)` in index.md. Pure functions, no I/O.

A hint only says "this file may be missing text"; it never changes the file.
Wording is short English so it reads next to `(N chars)`; page.md / tav.md
explain what each hint means and what to do about it.

- `excerpt gaps: N` / `possible gaps: N` -- count of `[...]` markers. Search
  results and query-focused extracts are excerpts by design (`excerpt`);
  elsewhere the marker only suggests something was dropped (`possible`).
- `cut off` -- the last non-empty line does not end like a finished sentence,
  table, code block, list item or heading.
- `body from line N` -- the first heading after the `# {title}` line starts at
  line N >= BODY_START_LINE_THRESHOLD (navigation before the body).
"""

from __future__ import annotations

import re

GAP_MARKER = "[...]"
BODY_START_LINE_THRESHOLD = 30

# Japanese and English sentence ends, closing brackets and quotes.
_TERMINAL_CHARS = frozenset("。．！？」』）】.!?)\"'”’|")
_CODE_FENCE = ("```", "~~~")
_STRUCTURAL_LINE = re.compile(r"^\s*(?:[-*+]\s|\d+[.)]\s|#{1,6}\s)")
_HEADING = re.compile(r"^#{1,6}\s+\S")


def count_gap_markers(text: str) -> int:
    return text.count(GAP_MARKER)


def is_cut_off(text: str) -> bool:
    lines = [line.rstrip() for line in text.splitlines() if line.strip()]
    if not lines:
        return False
    last = lines[-1]
    if last.lstrip().startswith(_CODE_FENCE):
        return False
    if _STRUCTURAL_LINE.match(last):
        return False
    return last[-1] not in _TERMINAL_CHARS


def body_start_line(text: str) -> int | None:
    """1-based line of the first heading after the leading `# {title}`, or None."""
    lines = text.splitlines()
    start = 0
    for index, line in enumerate(lines):
        if line.strip():
            if line.startswith("# "):
                start = index + 1
            break
    for index in range(start, len(lines)):
        if _HEADING.match(lines[index]):
            return index + 1
    return None


def gap_hints(text: str, *, excerpt: bool) -> str:
    """Comma-separated hints for one file, or "" when nothing looks missing."""
    hints: list[str] = []
    gaps = count_gap_markers(text)
    if gaps:
        hints.append(f"{'excerpt' if excerpt else 'possible'} gaps: {gaps}")
    if is_cut_off(text):
        hints.append("cut off")
    line = body_start_line(text)
    if line is not None and line >= BODY_START_LINE_THRESHOLD:
        hints.append(f"body from line {line}")
    return ", ".join(hints)
