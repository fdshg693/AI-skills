# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""Fetch the Playwright docs sources (docs/src/**/*.md) into output/ and index them.

`docs/src` is the source of truth for the public API and for every guide on
playwright.dev, but it is ~3 MB across ~180 Markdown files -- far too much to read
wholesale. This script takes a snapshot so that answers are grounded in the actual
docs, and search_playwright_docs.py can grep/rank over a stable local copy:

  microsoft/playwright@main docs/src/**/*.md  ->  output/docs/**/*.md

The sources come from a shallow, blobless, sparse `git clone` into a temporary
directory (one network round trip; only the Markdown blobs are downloaded).
Non-Markdown assets (docs/src/images/**) are intentionally skipped.
`--repo-root` copies from an existing local checkout instead.

After copying, writes a generated output/index.md (one line per file: title,
language tag, size, member count for API classes) and output/_meta.json.

Skips the whole copy when output/_meta.json was written within the last 7 days
unless --force is passed. The snapshot is big, so the freshness window is
deliberately long; docs move with releases, not hourly.

Standard library only; needs `git` on PATH (unless --repo-root is given).
"""

from __future__ import annotations

import argparse
import json
import re
import os
import shutil
import stat
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = SKILL_DIR / "output"
DOCS_OUT = OUTPUT_DIR / "docs"
META_PATH = OUTPUT_DIR / "_meta.json"
INDEX_REL = "index.md"

# docs/src relative to the repository root.
DOCS_SRC_REL = "docs/src"
SUFFIXES = (".md",)
# Directories under docs/src that hold no Markdown worth mirroring.
SKIP_DIRS = {"images"}

# The snapshot is large and docs move per release; a week is plenty.
FRESHNESS = timedelta(days=7)

REPO_URL = "https://github.com/microsoft/playwright"
REF = "main"
UPSTREAM_BLOB = f"{REPO_URL}/blob/{REF}"
# A blobless sparse clone of docs/src is a few MB; fail rather than hang.
GIT_TIMEOUT_SECONDS = 300

FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
HEADING_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)
MEMBER_RE = re.compile(r"^##\s+(?:async\s+)?(method|property|event)\s*:\s*(\S+)", re.MULTILINE)
# Language variants are encoded in the file name: auth-js.md, test-runners-csharp.md,
# test-assertions-csharp-java-python.md ...
LANGS = ("js", "python", "java", "csharp")
LANG_SUFFIX_RE = re.compile(r"-((?:" + "|".join(LANGS) + r")(?:-(?:" + "|".join(LANGS) + r"))*)$")


def _git(args: list[str], cwd: Path | None = None) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True,
            timeout=GIT_TIMEOUT_SECONDS,
        )
    except FileNotFoundError as exc:
        raise RuntimeError("`git` was not found on PATH") from exc
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"git {args[0]} timed out after {GIT_TIMEOUT_SECONDS}s") from exc
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"git {args[0]} failed: {exc.stderr.strip()}") from exc
    return result.stdout.strip()


def clone_docs(dest: Path) -> str:
    """Sparse-clone only docs/src/**/*.md of upstream into dest. Returns the commit SHA."""
    _git(
        [
            "clone",
            "--depth",
            "1",
            "--filter=blob:none",
            "--sparse",
            "--branch",
            REF,
            REPO_URL,
            str(dest),
        ]
    )
    _git(["sparse-checkout", "set", "--no-cone", f"/{DOCS_SRC_REL}/**/*.md"], cwd=dest)
    return _git(["rev-parse", "HEAD"], cwd=dest)


def _force_remove(func, path, _exc) -> None:
    # git writes read-only object files; Windows refuses to delete them as-is.
    os.chmod(path, stat.S_IWRITE)
    func(path)


def remove_tree(path: Path) -> None:
    if sys.version_info >= (3, 12):
        shutil.rmtree(path, onexc=_force_remove)
    else:
        shutil.rmtree(path, onerror=_force_remove)


def parse_frontmatter(body: str) -> dict[str, str]:
    match = FRONTMATTER_RE.match(body)
    if not match:
        return {}
    fields: dict[str, str] = {}
    for line in match.group(1).splitlines():
        key, sep, value = line.partition(":")
        if sep:
            fields[key.strip()] = value.strip().strip("'\"")
    return fields


def detect_langs(rel: str) -> list[str]:
    """Language variants a file covers, from its `-js` / `-csharp-java` name suffix."""
    stem = Path(rel).stem
    match = LANG_SUFFIX_RE.search(stem)
    if not match:
        return []
    return match.group(1).split("-")


def describe(rel: str, body: str) -> tuple[str, int]:
    """Return (title, API member count) for one doc file."""
    fields = parse_frontmatter(body)
    title = fields.get("title") or fields.get("id") or ""
    if not title:
        heading = HEADING_RE.search(body)
        title = heading.group(1).strip() if heading else Path(rel).stem
    return title, len(MEMBER_RE.findall(body))


def list_doc_files(docs_src: Path) -> list[str]:
    paths: list[str] = []
    for path in docs_src.rglob("*"):
        if not path.is_file() or path.suffix not in SUFFIXES:
            continue
        rel = path.relative_to(docs_src).as_posix()
        if rel.split("/", 1)[0] in SKIP_DIRS:
            continue
        paths.append(rel)
    return sorted(paths)


def write_index(pages: list[tuple[str, str, list[str], int, int]], source: str) -> None:
    """Write a generated file-level index grouped by directory."""
    groups: dict[str, list[tuple[str, str, list[str], int, int]]] = {}
    for page in pages:
        rel = page[0]
        group = rel.split("/", 1)[0] if "/" in rel else "(root)"
        groups.setdefault(group, []).append(page)

    lines = [
        "# Playwright docs index",
        "",
        f"Generated from `{DOCS_SRC_REL}` of {source}.",
        "Not upstream: built from each file's frontmatter / first heading.",
        "Paths are relative to this file; sources live under `docs/`.",
        "",
        "`members` counts `## method:` / `## property:` / `## event:` entries,",
        "so a high count means an API reference page rather than a guide.",
        "",
    ]
    for group in sorted(groups):
        lines.append(f"## {group if group != '(root)' else 'guides (docs/src root)'}")
        lines.append("")
        lines.append("| file | title | langs | KB | members |")
        lines.append("|---|---|---|---|---|")
        for rel, title, langs, size, members in sorted(groups[group]):
            lang_cell = ", ".join(langs) if langs else "all"
            member_cell = str(members) if members else ""
            lines.append(
                f"| [{rel}](docs/{rel}) | {title} | {lang_cell} | "
                f"{size // 1024 or 1} | {member_cell} |"
            )
        lines.append("")

    (OUTPUT_DIR / INDEX_REL).write_text("\n".join(lines), encoding="utf-8", newline="\n")


def read_fetched_at(meta_path: Path) -> datetime | None:
    if not meta_path.is_file():
        return None
    try:
        data = json.loads(meta_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    raw = data.get("fetched_at")
    if not isinstance(raw, str):
        return None
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        return None


def write_meta(source: str, pages: list[tuple[str, str, list[str], int, int]]) -> None:
    payload = {
        "source": source,
        "source_dir": DOCS_SRC_REL,
        "upstream_blob": UPSTREAM_BLOB + "/" + DOCS_SRC_REL,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "file_count": len(pages),
        "files": [
            {
                "output": "docs/" + rel,
                "source": f"{DOCS_SRC_REL}/{rel}",
                "title": title,
                "langs": langs,
                "bytes": size,
                "members": members,
            }
            for rel, title, langs, size, members in pages
        ],
    }
    META_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def remove_stale_outputs(keep: set[str]) -> None:
    removed = 0
    for path in sorted(OUTPUT_DIR.rglob("*"), reverse=True):
        if path.is_file():
            rel = path.relative_to(OUTPUT_DIR).as_posix()
            if rel not in keep:
                path.unlink()
                removed += 1
        elif path.is_dir() and not any(path.iterdir()):
            path.rmdir()
    if removed:
        print(f"  Removed {removed} stale file(s)")


def copy_all(repo_root: Path, source: str) -> None:
    docs_src = repo_root / DOCS_SRC_REL
    rel_paths = list_doc_files(docs_src)
    if not rel_paths:
        raise RuntimeError(f"no Markdown files found under {docs_src}")

    DOCS_OUT.mkdir(parents=True, exist_ok=True)
    pages: list[tuple[str, str, list[str], int, int]] = []

    for rel in rel_paths:
        src = docs_src / rel
        dst = DOCS_OUT / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
        body = src.read_text(encoding="utf-8", errors="replace")
        title, members = describe(rel, body)
        pages.append((rel, title, detect_langs(rel), src.stat().st_size, members))

    print(f"Copied {len(pages)} Markdown file(s) from {docs_src}")

    write_index(pages, source)
    print(f"  Wrote {INDEX_REL}")

    keep = {"docs/" + rel for rel, *_ in pages} | {INDEX_REL, "_meta.json"}
    remove_stale_outputs(keep)
    write_meta(source, pages)
    print(f"Wrote {META_PATH.relative_to(SKILL_DIR)}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-fetch even if the snapshot is still within the 7-day freshness window.",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Copy from this local Playwright checkout instead of cloning upstream.",
    )
    args = parser.parse_args()

    if not args.force:
        fetched_at = read_fetched_at(META_PATH)
        if fetched_at is not None:
            age = datetime.now(timezone.utc) - fetched_at
            if age < FRESHNESS:
                print(
                    f"Snapshot already fresh (fetched_at={fetched_at.isoformat()}, "
                    f"age={age}). Use --force to re-copy."
                )
                return 0

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    try:
        if args.repo_root:
            repo_root = args.repo_root.resolve()
            copy_all(repo_root, f"the local checkout at `{repo_root}`")
        else:
            tmp = Path(tempfile.mkdtemp(prefix="playwright-docs-"))
            try:
                print(f"Cloning {DOCS_SRC_REL} of {REPO_URL}@{REF} (sparse, blobless) ...")
                sha = clone_docs(tmp / "playwright")
                copy_all(tmp / "playwright", f"`{REPO_URL}` at commit `{sha}` ({REF})")
            finally:
                remove_tree(tmp)
    except (RuntimeError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
