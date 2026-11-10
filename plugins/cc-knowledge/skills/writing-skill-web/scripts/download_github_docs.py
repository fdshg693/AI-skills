"""Copy-and-adapt template: mirror Markdown docs from a GitHub repository via `gh api`.

Use this when a product's docs live as Markdown in a GitHub repo (e.g.
`site/src/content/docs`, `docs/`) -- often more complete and more stable than
the rendered site, and fetchable without scraping HTML. Whether to use this,
an llms.txt snapshot (download_web_reference.py), or both is decided per skill
(see web-patterns-reference.md section 1.12); this script only covers the
GitHub side.

Copy into the new skill's directory, then edit DEFAULT_REPO / DEFAULT_DOCS_ROOT /
DEFAULT_REF (and PRESERVE_PREFIXES if other scripts also write into output/).

Enumeration (pick per repo):
  * default: Git Trees API (`git/trees/<ref>?recursive=1`) -- one request for the
    whole tree, filtered to DOCS_ROOT and DOC_EXTENSIONS. Falls back to walking
    the Contents API if GitHub reports the tree as truncated.
  * --toc <path relative to DOCS_ROOT>: only files linked from a table-of-contents
    Markdown file (e.g. `summary.md`, `SUMMARY.md`). Use when the docs root also
    holds drafts/partials you do not want.

Output (relative to this script):
  output/<path relative to DOCS_ROOT>   raw file bodies, unchanged
  output/summary.md                     generated index from each page's frontmatter
                                        title/description plus upstream blob URL
  output/_meta.json                     source_repo/ref/docs_root/fetched_at/files

Skips the whole snapshot when output/_meta.json is within FRESHNESS unless
--force is passed. Requires the `gh` CLI (authenticated for higher rate limits;
public reads work without auth).

Usage (via webref_cli.py):
    python webref_cli.py download-github
    python webref_cli.py download-github --force
    python webref_cli.py download-github --repo owner/name --docs-root docs --ref main
    python webref_cli.py download-github --toc summary.md
"""

from __future__ import annotations

import argparse
import json
import posixpath
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import unquote

# --- adapt these when copying ---------------------------------------------------
DEFAULT_REPO = "owner/repo"
DEFAULT_DOCS_ROOT = "docs"
DEFAULT_REF = "main"
# Output paths (relative to the output dir) owned by other scripts; never deleted
# as stale. temp/ is where extract_doc_section.py / fetch_selected_pages.py write.
# When the same skill also keeps an llms.txt snapshot, give this script its own
# --output-dir (e.g. output/github) instead of growing this list.
PRESERVE_PREFIXES: tuple[str, ...] = ("temp/",)
# ---------------------------------------------------------------------------------

SKILL_DIR = Path(__file__).resolve().parent
DEFAULT_OUTPUT_DIR = SKILL_DIR / "output"
META_NAME = "_meta.json"
SUMMARY_NAME = "summary.md"

DOC_EXTENSIONS = (".md", ".mdx")
# Docs repos change infrequently; a week is enough for usage/install guidance.
FRESHNESS = timedelta(days=7)
# Fail fast rather than hang on a stalled gh/network call.
GH_TIMEOUT_SECONDS = 60

REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
FRONTMATTER_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n", re.DOTALL)
# Markdown links: [title](path) -- absolute URLs and anchors are filtered later.
MD_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")


def run_gh(args: list[str], what: str) -> str:
    """Run `gh` and return stdout; raise RuntimeError on any failure."""
    try:
        result = subprocess.run(
            ["gh", *args],
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
        raise RuntimeError(f"gh api timed out after {GH_TIMEOUT_SECONDS}s for {what}") from exc
    if result.returncode != 0:
        err = (result.stderr or result.stdout or "").strip()
        raise RuntimeError(f"gh api failed for {what}: {err}")
    return result.stdout


def gh_json(endpoint: str) -> object:
    out = run_gh(["api", endpoint], endpoint)
    try:
        return json.loads(out)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"gh api returned non-JSON for {endpoint}") from exc


def gh_raw(repo: str, ref: str, repo_path: str) -> str:
    """Fetch one file's raw body (Contents API + raw Accept header)."""
    endpoint = f"repos/{repo}/contents/{repo_path}?ref={ref}"
    return run_gh(["api", endpoint, "-H", "Accept: application/vnd.github.raw"], repo_path)


def is_doc(path: str) -> bool:
    return path.lower().endswith(DOC_EXTENSIONS)


def safe_rel(path: str) -> str | None:
    """Normalize a docs-root-relative path; None if it escapes the root."""
    norm = posixpath.normpath(path).lstrip("/")
    if norm in ("", ".") or norm.startswith("../") or norm == "..":
        return None
    return norm


def list_via_tree(repo: str, ref: str, docs_root: str) -> list[str] | None:
    """Return doc paths relative to docs_root, or None if the tree was truncated."""
    data = gh_json(f"repos/{repo}/git/trees/{ref}?recursive=1")
    if not isinstance(data, dict) or not isinstance(data.get("tree"), list):
        raise RuntimeError(f"unexpected git/trees response for {repo}@{ref}")
    if data.get("truncated"):
        return None
    prefix = docs_root.strip("/") + "/" if docs_root.strip("/") else ""
    paths: list[str] = []
    for item in data["tree"]:
        if not isinstance(item, dict) or item.get("type") != "blob":
            continue
        full = item.get("path")
        if not isinstance(full, str) or not full.startswith(prefix) or not is_doc(full):
            continue
        rel = safe_rel(full[len(prefix) :])
        if rel:
            paths.append(rel)
    return paths


def list_via_contents(repo: str, ref: str, docs_root: str, rel_dir: str = "") -> list[str]:
    """Walk the Contents API recursively (fallback for truncated trees)."""
    repo_path = "/".join(p for p in (docs_root.strip("/"), rel_dir) if p)
    items = gh_json(f"repos/{repo}/contents/{repo_path}?ref={ref}")
    if not isinstance(items, list):
        raise RuntimeError(f"expected a directory listing for {repo_path}")
    paths: list[str] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        name, typ = item.get("name"), item.get("type")
        if not isinstance(name, str) or not isinstance(typ, str):
            continue
        child = safe_rel(f"{rel_dir}/{name}" if rel_dir else name)
        if child is None:
            continue
        if typ == "dir":
            paths.extend(list_via_contents(repo, ref, docs_root, child))
        elif typ == "file" and is_doc(name):
            paths.append(child)
    return paths


def links_from_toc(toc_rel: str, toc_body: str) -> list[str]:
    """Doc paths (relative to docs root) linked from a TOC file, in TOC order."""
    base = posixpath.dirname(toc_rel)
    seen: set[str] = set()
    paths: list[str] = []
    for target in MD_LINK_RE.findall(toc_body):
        if re.match(r"^[a-z][a-z0-9+.-]*:", target, re.IGNORECASE) or target.startswith("#"):
            continue
        target = unquote(target.split("#", 1)[0])
        if not is_doc(target):
            continue
        rel = safe_rel(posixpath.join(base, target))
        if rel and rel not in seen:
            seen.add(rel)
            paths.append(rel)
    return paths


def parse_frontmatter_fields(body: str) -> tuple[str, str]:
    """Return (title, description) from YAML frontmatter; empty strings if absent."""
    match = FRONTMATTER_RE.match(body)
    if not match:
        return "", ""
    title = description = ""
    for line in match.group(1).splitlines():
        key, sep, value = line.partition(":")
        if not sep:
            continue
        key, value = key.strip(), value.strip().strip("'\"")
        if key == "title" and not title:
            title = value
        elif key == "description" and not description:
            description = value
    return title, description


def blob_url(repo: str, ref: str, docs_root: str, rel: str) -> str:
    path = "/".join(p for p in (docs_root.strip("/"), rel) if p)
    return f"https://github.com/{repo}/blob/{ref}/{path}"


def build_summary(repo: str, ref: str, docs_root: str, pages: list[tuple[str, str, str]]) -> str:
    """Generated TOC grouped by first path segment (not an upstream file)."""
    groups: dict[str, list[tuple[str, str, str]]] = {}
    for rel, title, description in pages:
        group = rel.split("/", 1)[0] if "/" in rel else "(root)"
        groups.setdefault(group, []).append((rel, title, description))

    lines = [
        f"# {repo} docs index",
        "",
        f"Generated from `{repo}` `{docs_root}` (`{ref}`).",
        "This file is not upstream; it is built from each page's `title` / `description`.",
        f"Upstream: `{blob_url(repo, ref, docs_root, '<path>')}`",
        "",
    ]
    for group in sorted(groups, key=lambda g: (g != "(root)", g)):
        lines += [f"## {'root' if group == '(root)' else group}", ""]
        for rel, title, description in groups[group]:
            label = title or Path(rel).stem
            suffix = f" — {description}" if description else ""
            lines.append(f"- [{label}]({rel}){suffix}")
        lines.append("")
    return "\n".join(lines)


def read_fetched_at(meta_path: Path) -> datetime | None:
    if not meta_path.is_file():
        return None
    try:
        data = json.loads(meta_path.read_text(encoding="utf-8"))
        return datetime.fromisoformat(data["fetched_at"])
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError):
        return None


def remove_stale_outputs(output_dir: Path, keep: set[str]) -> None:
    for path in output_dir.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(output_dir).as_posix()
        if PRESERVE_PREFIXES and rel.startswith(PRESERVE_PREFIXES):
            continue
        if rel not in keep:
            path.unlink()
            print(f"  Removed stale {rel}")


def download_all(
    repo: str, ref: str, docs_root: str, output_dir: Path, toc: str | None
) -> list[str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    root = docs_root.strip("/")

    bodies: dict[str, str] = {}
    if toc:
        toc_rel = safe_rel(toc)
        if toc_rel is None:
            raise RuntimeError(f"--toc escapes the docs root: {toc}")
        print(f"Reading TOC {toc_rel} ...")
        bodies[toc_rel] = gh_raw(repo, ref, "/".join(p for p in (root, toc_rel) if p))
        rel_paths = [toc_rel, *links_from_toc(toc_rel, bodies[toc_rel])]
    else:
        print(f"Listing {repo}@{ref}:{root or '/'} ...")
        listed = list_via_tree(repo, ref, root)
        if listed is None:
            print("  git/trees response truncated; walking the Contents API instead")
            listed = list_via_contents(repo, ref, root)
        rel_paths = sorted(set(listed))
    rel_paths = [p for p in dict.fromkeys(rel_paths) if p != SUMMARY_NAME and p != META_NAME]
    if not rel_paths:
        raise RuntimeError(f"no doc files ({', '.join(DOC_EXTENSIONS)}) found under {root}")

    pages: list[tuple[str, str, str]] = []
    for rel in rel_paths:
        body = bodies.get(rel)
        if body is None:
            print(f"Fetching {rel} ...")
            body = gh_raw(repo, ref, "/".join(p for p in (root, rel) if p))
        out_path = output_dir / rel
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(body, encoding="utf-8", newline="\n")
        pages.append((rel, *parse_frontmatter_fields(body)))

    (output_dir / SUMMARY_NAME).write_text(
        build_summary(repo, ref, root, pages), encoding="utf-8", newline="\n"
    )
    indexed = [SUMMARY_NAME, *rel_paths]
    remove_stale_outputs(output_dir, set(indexed) | {META_NAME})
    meta = {
        "source_repo": repo,
        "ref": ref,
        "docs_root": root,
        "toc": toc,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "files": indexed,
    }
    (output_dir / META_NAME).write_text(
        json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"Wrote {len(indexed)} files to {output_dir}")
    return indexed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo", default=DEFAULT_REPO, help="owner/name")
    parser.add_argument("--docs-root", default=DEFAULT_DOCS_ROOT, help="docs directory in repo")
    parser.add_argument("--ref", default=DEFAULT_REF, help="branch, tag, or commit")
    parser.add_argument(
        "--toc", default=None, help="TOC file relative to --docs-root; fetch only its links"
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument(
        "--force", action="store_true", help="Re-download even if the snapshot is fresh."
    )
    args = parser.parse_args()

    if not REPO_RE.match(args.repo) or args.repo == "owner/repo":
        print(
            f"ERROR: set DEFAULT_REPO or pass --repo owner/name (got {args.repo!r})",
            file=sys.stderr,
        )
        return 2

    if not args.force:
        fetched_at = read_fetched_at(args.output_dir / META_NAME)
        if fetched_at is not None:
            age = datetime.now(timezone.utc) - fetched_at
            if age < FRESHNESS:
                print(
                    f"Snapshot already fresh (fetched_at={fetched_at.isoformat()}, "
                    f"age={age}). Use --force to refetch."
                )
                return 0

    try:
        download_all(args.repo, args.ref, args.docs_root, args.output_dir, args.toc)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
