"""Download PR-Agent docs (docs/docs/*.md) into output/ via `gh api`.

Enumeration comes from docs/docs/summary.md (table of contents). Only Markdown
paths linked from that file are fetched — not the full docs/docs tree.

Skips the whole snapshot when output/_meta.json was written within the last
7 days unless --force is passed. Requires the `gh` CLI (authenticated for
higher rate limits; public reads work without auth).
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

REPO = "The-PR-Agent/pr-agent"
DOCS_ROOT = "docs/docs"
REF = "main"

# Docs change infrequently; a week is enough for usage/install guidance.
FRESHNESS = timedelta(days=7)
# Fail fast rather than hang on a stalled gh/network call.
GH_TIMEOUT_SECONDS = 60

# Markdown links: [title](path.md) — ignore absolute URLs and bare anchors.
MD_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")


def gh_raw(repo_file_path: str) -> str:
    """Fetch a single file's raw contents via `gh api` (Contents API + raw Accept)."""
    endpoint = f"repos/{REPO}/contents/{repo_file_path}?ref={REF}"
    try:
        result = subprocess.run(
            [
                "gh",
                "api",
                endpoint,
                "-H",
                "Accept: application/vnd.github.raw",
            ],
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

    if result.returncode != 0:
        err = (result.stderr or result.stdout or "").strip()
        raise RuntimeError(f"gh api failed for {repo_file_path}: {err}")
    return result.stdout


def parse_summary_md_paths(summary_body: str) -> list[str]:
    """Return unique relative .md paths linked from summary.md (order preserved)."""
    paths: list[str] = []
    seen: set[str] = set()
    for match in MD_LINK_RE.finditer(summary_body):
        href = match.group(1).strip()
        if href.startswith(("http://", "https://", "mailto:", "#")):
            continue
        href = href.split("#", 1)[0].strip()
        if not href or not href.endswith(".md"):
            continue
        # Keep paths relative to docs/docs; reject traversal.
        norm = href.replace("\\", "/").lstrip("./")
        if not norm or ".." in Path(norm).parts:
            continue
        if norm in seen:
            continue
        seen.add(norm)
        paths.append(norm)
    return paths


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


def download_all() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    summary_rel = "summary.md"
    summary_repo_path = f"{DOCS_ROOT}/{summary_rel}"
    print(f"Fetching {summary_repo_path} ...")
    summary_body = gh_raw(summary_repo_path)
    summary_out = OUTPUT_DIR / summary_rel
    summary_out.write_text(summary_body, encoding="utf-8", newline="\n")
    print(f"  Wrote {summary_out.relative_to(SKILL_DIR)}")

    linked = parse_summary_md_paths(summary_body)
    # TOC first, then every linked page (deduped; summary itself already written).
    relative_paths = [summary_rel] + [p for p in linked if p != summary_rel]

    for rel in relative_paths[1:]:
        out_path = OUTPUT_DIR / rel
        out_path.parent.mkdir(parents=True, exist_ok=True)
        repo_path = f"{DOCS_ROOT}/{rel}"
        print(f"Fetching {repo_path} ...")
        body = gh_raw(repo_path)
        out_path.write_text(body, encoding="utf-8", newline="\n")
        print(f"  Wrote {out_path.relative_to(SKILL_DIR)}")

    write_meta(relative_paths)
    print(f"Wrote {META_PATH.relative_to(SKILL_DIR)} ({len(relative_paths)} files)")


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
