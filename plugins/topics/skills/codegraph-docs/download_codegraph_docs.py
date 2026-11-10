"""Download CodeGraph docs (site/src/content/docs/**/*.md) into output/ via `gh api`.

Enumerates every Markdown file under the docs root recursively (the upstream
tree has no TOC). After fetch, writes a generated output/summary.md index
from each page's title/description frontmatter.

Skips the whole snapshot when output/_meta.json was written within the last
7 days unless --force is passed. Requires the `gh` CLI (authenticated for
higher rate limits; public reads work without auth).

Does not touch output/cli/ (owned by generate_codegraph_help_yaml.py).
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = SKILL_DIR / "output"
META_PATH = OUTPUT_DIR / "_meta.json"
SUMMARY_REL = "summary.md"

REPO = "colbymchenry/codegraph"
DOCS_ROOT = "site/src/content/docs"
REF = "main"

# Docs change infrequently; a week is enough for usage/install guidance.
FRESHNESS = timedelta(days=7)
# Fail fast rather than hang on a stalled gh/network call.
GH_TIMEOUT_SECONDS = 60

FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)


def run_gh(args: list[str], repo_file_path: str) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            args,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=GH_TIMEOUT_SECONDS,
        )
    except FileNotFoundError as exc:
        raise RuntimeError(
            "gh CLI not found on PATH. Install GitHub CLI and ensure `gh` is available."
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(
            f"gh api timed out after {GH_TIMEOUT_SECONDS}s for {repo_file_path}"
        ) from exc


def check_gh(result: subprocess.CompletedProcess[str], repo_file_path: str) -> None:
    if result.returncode != 0:
        err = (result.stderr or result.stdout or "").strip()
        raise RuntimeError(f"gh api failed for {repo_file_path}: {err}")


def gh_raw(repo_file_path: str) -> str:
    """Fetch a single file's raw contents via `gh api` (Contents API + raw Accept)."""
    endpoint = f"repos/{REPO}/contents/{repo_file_path}?ref={REF}"
    result = run_gh(
        [
            "gh",
            "api",
            endpoint,
            "-H",
            "Accept: application/vnd.github.raw",
        ],
        repo_file_path,
    )
    check_gh(result, repo_file_path)
    return result.stdout


def gh_json(repo_file_path: str) -> object:
    """Fetch Contents API JSON (directory listing or a single file object)."""
    endpoint = f"repos/{REPO}/contents/{repo_file_path}?ref={REF}"
    result = run_gh(["gh", "api", endpoint], repo_file_path)
    check_gh(result, repo_file_path)
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"gh api returned non-JSON for {repo_file_path}") from exc


def list_md_rel_paths(rel_dir: str = "") -> list[str]:
    """Walk the Contents API and return unique .md paths relative to DOCS_ROOT."""
    repo_path = f"{DOCS_ROOT}/{rel_dir}".rstrip("/") if rel_dir else DOCS_ROOT
    items = gh_json(repo_path)
    if not isinstance(items, list):
        raise RuntimeError(f"expected a directory listing for {repo_path}")

    paths: list[str] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        typ = item.get("type")
        if not isinstance(name, str) or not isinstance(typ, str):
            continue
        child_rel = f"{rel_dir}/{name}".lstrip("/") if rel_dir else name
        if ".." in Path(child_rel).parts:
            continue
        if typ == "dir":
            paths.extend(list_md_rel_paths(child_rel))
        elif typ == "file" and name.endswith(".md"):
            paths.append(child_rel)
    return paths


def parse_frontmatter_fields(body: str) -> tuple[str, str]:
    """Return (title, description) from YAML frontmatter; empty strings if absent."""
    match = FRONTMATTER_RE.match(body)
    if not match:
        return "", ""
    title = ""
    description = ""
    for line in match.group(1).splitlines():
        key, sep, value = line.partition(":")
        if not sep:
            continue
        key = key.strip()
        value = value.strip().strip("'\"")
        if key == "title" and not title:
            title = value
        elif key == "description" and not description:
            description = value
    return title, description


def write_summary(pages: list[tuple[str, str, str]]) -> None:
    """Write a generated TOC grouped by first path segment."""
    groups: dict[str, list[tuple[str, str, str]]] = {}
    for rel, title, description in pages:
        group = rel.split("/", 1)[0] if "/" in rel else "(root)"
        groups.setdefault(group, []).append((rel, title, description))

    lines = [
        "# CodeGraph docs index",
        "",
        f"Generated from `{REPO}` `{DOCS_ROOT}` (`{REF}`).",
        "This file is not upstream; it is built from each page's `title` / `description`.",
        "",
    ]
    for group in sorted(groups):
        heading = group if group != "(root)" else "root"
        lines.append(f"## {heading}")
        lines.append("")
        for rel, title, description in groups[group]:
            label = title or Path(rel).stem
            if description:
                lines.append(f"- [{label}]({rel}) — {description}")
            else:
                lines.append(f"- [{label}]({rel})")
        lines.append("")

    (OUTPUT_DIR / SUMMARY_REL).write_text("\n".join(lines), encoding="utf-8", newline="\n")


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


def write_meta(paths: list[str]) -> None:
    fetched_at = datetime.now(timezone.utc).isoformat()
    payload = {
        "source_repo": REPO,
        "ref": REF,
        "docs_root": DOCS_ROOT,
        "fetched_at": fetched_at,
        "files": paths,
    }
    META_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def remove_stale_outputs(keep: set[str]) -> None:
    for path in OUTPUT_DIR.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(OUTPUT_DIR).as_posix()
        # CLI --help YAML は generate_codegraph_help_yaml.py の生成物。docs 再取得で消さない。
        if rel.startswith("cli/"):
            continue
        if rel not in keep:
            path.unlink()
            print(f"  Removed stale {rel}")


def download_all() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Listing {DOCS_ROOT} ...")
    relative_paths = sorted(set(list_md_rel_paths()))
    if not relative_paths:
        raise RuntimeError(f"no Markdown files found under {DOCS_ROOT}")

    pages: list[tuple[str, str, str]] = []
    for rel in relative_paths:
        out_path = OUTPUT_DIR / rel
        out_path.parent.mkdir(parents=True, exist_ok=True)
        repo_path = f"{DOCS_ROOT}/{rel}"
        print(f"Fetching {repo_path} ...")
        body = gh_raw(repo_path)
        out_path.write_text(body, encoding="utf-8", newline="\n")
        print(f"  Wrote {out_path.relative_to(SKILL_DIR)}")
        title, description = parse_frontmatter_fields(body)
        pages.append((rel, title, description))

    write_summary(pages)
    print(f"  Wrote {SUMMARY_REL}")

    indexed = [SUMMARY_REL] + relative_paths
    remove_stale_outputs(set(indexed) | {"_meta.json"})
    write_meta(indexed)
    print(f"Wrote {META_PATH.relative_to(SKILL_DIR)} ({len(indexed)} files)")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-download even if the snapshot is still within the freshness window.",
    )
    args = parser.parse_args()

    if not args.force:
        fetched_at = read_fetched_at(META_PATH)
        if fetched_at is not None:
            age = datetime.now(timezone.utc) - fetched_at
            if age < FRESHNESS:
                print(
                    f"Snapshot already fresh (fetched_at={fetched_at.isoformat()}, "
                    f"age={age}). Use --force to refetch."
                )
                return 0

    try:
        download_all()
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
