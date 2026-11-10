"""Fetch a narrow slice of a GitHub repository via the REST API, without git clone.

Subcommands are meant to be used in this order to progressively narrow scope,
then pull only what's needed:

    readme    -> read the repo's README to understand its layout
    list      -> list the immediate children of a path (start with "" = root)
    tree      -> recursively list every file under a (now-narrow) path
    get       -> download a single file
    get-tree  -> download every file under a (now-narrow) path

Auth (optional; raises rate limit 60/hour -> 5000/hour, enables private repos):
    1. --token CLI flag
    2. GITHUB_TOKEN or GH_TOKEN environment variable
    3. .env next to this script (GITHUB_TOKEN=... or GH_TOKEN=...)
Anonymous access still works for public repos at low volume.
"""

from __future__ import annotations

import argparse
import base64
import fnmatch
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path, PurePosixPath

API_ROOT = "https://api.github.com"
USER_AGENT = "github-fetch-skill"
SCRIPT_DIR = Path(__file__).resolve().parent
TOKEN_ENV_KEYS = ("GITHUB_TOKEN", "GH_TOKEN")
AUTH_HINT = (
    "Pass --token, set GITHUB_TOKEN/GH_TOKEN, or put GITHUB_TOKEN=... "
    f"in {SCRIPT_DIR / '.env'} to raise the limit from 60/hour to 5000/hour."
)


class GhFetchError(RuntimeError):
    pass


def load_dotenv(path: Path) -> None:
    """Load KEY=VALUE pairs from a .env file into os.environ (stdlib only).

    Does not overwrite keys already present in the environment.
    Lines starting with # and blank lines are ignored. Values may be
    optionally quoted with single or double quotes.
    """
    if not path.is_file():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        if not key or key in os.environ:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        os.environ[key] = value


def resolve_token(cli_token: str | None) -> str | None:
    """Resolve GitHub token: --token > env > .env next to this script."""
    if cli_token:
        return cli_token
    load_dotenv(SCRIPT_DIR / ".env")
    for key in TOKEN_ENV_KEYS:
        value = os.environ.get(key)
        if value:
            return value
    return None


def api_request(url: str, token: str | None, raw: bool = False) -> tuple[bytes, dict]:
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/vnd.github+json" if not raw else "*/*",
    }
    if not raw:
        headers["X-GitHub-Api-Version"] = "2022-11-28"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.read(), dict(resp.headers)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        if e.code == 403 and e.headers.get("X-RateLimit-Remaining") == "0":
            reset = e.headers.get("X-RateLimit-Reset", "?")
            raise GhFetchError(
                f"GitHub API rate limit exceeded (resets at unix time {reset}). {AUTH_HINT}"
            ) from e
        if e.code == 404:
            raise GhFetchError(
                f"404 Not Found for {url}\n"
                "Check the owner/repo, --ref (branch/tag/sha), and path spelling."
            ) from e
        raise GhFetchError(f"GitHub API error {e.code} for {url}: {body}") from e
    except urllib.error.URLError as e:
        raise GhFetchError(f"Network error requesting {url}: {e}") from e


def api_get_json(url: str, token: str | None):
    body, _ = api_request(url, token)
    return json.loads(body)


def split_repo(repo: str) -> tuple[str, str]:
    if "/" not in repo:
        raise GhFetchError(f"repo must be 'owner/repo', got: {repo}")
    owner, name = repo.split("/", 1)
    return owner, name


def resolve_default_branch(owner: str, repo: str, token: str | None) -> str:
    data = api_get_json(f"{API_ROOT}/repos/{owner}/{repo}", token)
    return data["default_branch"]


def resolve_root_tree_sha(owner: str, repo: str, ref: str | None, token: str | None) -> str:
    ref = ref or resolve_default_branch(owner, repo, token)
    data = api_get_json(f"{API_ROOT}/repos/{owner}/{repo}/commits/{ref}", token)
    return data["commit"]["tree"]["sha"]


def get_tree(owner: str, repo: str, sha: str, token: str, recursive: bool) -> dict:
    url = f"{API_ROOT}/repos/{owner}/{repo}/git/trees/{sha}"
    if recursive:
        url += "?recursive=1"
    return api_get_json(url, token)


def resolve_path_tree_sha(
    owner: str, repo: str, path: str, root_tree_sha: str, token: str | None
) -> str:
    path = path.strip("/")
    if not path:
        return root_tree_sha
    current_sha = root_tree_sha
    parts = path.split("/")
    for i, part in enumerate(parts):
        tree = get_tree(owner, repo, current_sha, token, recursive=False)
        match = next((e for e in tree["tree"] if e["path"] == part), None)
        if match is None:
            raise GhFetchError(f"path segment '{part}' not found (looking for '{path}')")
        if match["type"] == "blob":
            if i != len(parts) - 1:
                raise GhFetchError(f"'{part}' is a file, not a directory, partway through '{path}'")
            raise GhFetchError(f"'{path}' is a file, not a directory. Use 'get' instead of 'tree'.")
        current_sha = match["sha"]
    return current_sha


def cmd_readme(args, token: str | None) -> None:
    owner, repo = split_repo(args.repo)
    ref_qs = f"?ref={args.ref}" if args.ref else ""
    data = api_get_json(f"{API_ROOT}/repos/{owner}/{repo}/readme{ref_qs}", token)
    content = decode_content(data)
    sys.stdout.write(content.decode("utf-8", errors="replace"))


def cmd_list(args, token: str | None) -> None:
    owner, repo = split_repo(args.repo)
    path = args.path.strip("/")
    ref_qs = f"?ref={args.ref}" if args.ref else ""
    data = api_get_json(f"{API_ROOT}/repos/{owner}/{repo}/contents/{path}{ref_qs}", token)
    if isinstance(data, dict):
        raise GhFetchError(f"'{path}' is a file, not a directory. Use 'get' to download it.")
    entries = sorted(data, key=lambda e: (e["type"] != "dir", e["name"]))
    for e in entries:
        kind = "DIR " if e["type"] == "dir" else "FILE"
        size = "-" if e["type"] == "dir" else str(e["size"])
        print(f"{kind}  {size:>10}  {e['path']}")
    print(f"\n{len(entries)} entries under '{path or '(root)'}'")


def cmd_tree(args, token: str | None) -> None:
    owner, repo = split_repo(args.repo)
    root_sha = resolve_root_tree_sha(owner, repo, args.ref, token)
    path = args.path.strip("/")
    target_sha = resolve_path_tree_sha(owner, repo, path, root_sha, token)
    data = get_tree(owner, repo, target_sha, token, recursive=True)
    files = [e for e in data["tree"] if e["type"] == "blob"]
    total_size = sum(e.get("size", 0) for e in files)
    for e in files:
        full_path = f"{path}/{e['path']}" if path else e["path"]
        print(f"{e.get('size', 0):>10}  {full_path}")
    print(f"\n{len(files)} files, {total_size} bytes total under '{path or '(root)'}'")
    if data.get("truncated"):
        print(
            "WARNING: GitHub truncated this listing (too many entries). "
            "Narrow to a deeper subfolder and re-run 'tree' on that instead.",
            file=sys.stderr,
        )


def decode_content(data: dict) -> bytes:
    encoding = data.get("encoding")
    if data.get("content") is not None and encoding in ("base64", None):
        return base64.b64decode(data["content"])
    if data.get("content") is not None and encoding == "utf-8":
        return data["content"].encode("utf-8")
    raise GhFetchError(f"unexpected content encoding: {encoding}")


def fetch_file_bytes(owner: str, repo: str, path: str, ref: str | None, token: str | None) -> bytes:
    ref_qs = f"?ref={ref}" if ref else ""
    encoded_path = urllib.parse.quote(path, safe="/")
    data = api_get_json(f"{API_ROOT}/repos/{owner}/{repo}/contents/{encoded_path}{ref_qs}", token)
    if isinstance(data, list):
        raise GhFetchError(f"'{path}' is a directory, not a file. Use 'list' or 'tree' instead.")
    if data.get("type") != "file":
        raise GhFetchError(f"'{path}' is a {data.get('type')}, not a plain file.")
    # GitHub returns encoding "none" and empty content for files >1MB; use download_url.
    encoding = data.get("encoding")
    content = data.get("content")
    if content and encoding in ("base64", "utf-8", None):
        return decode_content(data)
    download_url = data.get("download_url")
    if not download_url:
        raise GhFetchError(f"'{path}' has no inline content and no download_url (file too large?)")
    body, _ = api_request(download_url, token, raw=True)
    return body


def cmd_get(args, token: str | None) -> None:
    owner, repo = split_repo(args.repo)
    path = args.path.strip("/")
    content = fetch_file_bytes(owner, repo, path, args.ref, token)
    dest = Path(args.dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(content)
    print(f"wrote {len(content)} bytes -> {dest}")


def cmd_get_tree(args, token: str | None) -> None:
    owner, repo = split_repo(args.repo)
    root_sha = resolve_root_tree_sha(owner, repo, args.ref, token)
    path = args.path.strip("/")
    target_sha = resolve_path_tree_sha(owner, repo, path, root_sha, token)
    data = get_tree(owner, repo, target_sha, token, recursive=True)
    if data.get("truncated"):
        raise GhFetchError(
            f"'{path}' is too large for a single tree listing (GitHub truncated it). "
            "Narrow to a deeper subfolder first."
        )
    files = [e for e in data["tree"] if e["type"] == "blob"]

    if args.include:
        files = [e for e in files if any(fnmatch.fnmatch(e["path"], pat) for pat in args.include)]
    if args.exclude:
        files = [
            e for e in files if not any(fnmatch.fnmatch(e["path"], pat) for pat in args.exclude)
        ]

    if len(files) > args.max_files:
        raise GhFetchError(
            f"{len(files)} files match under '{path}', which exceeds --max-files={args.max_files}. "
            "Narrow the path further, add --include/--exclude filters, or raise --max-files explicitly."
        )

    dest_dir = Path(args.dest)
    written = []
    for e in files:
        repo_path = f"{path}/{e['path']}" if path else e["path"]
        content = fetch_file_bytes(owner, repo, repo_path, args.ref, token)
        local_path = dest_dir / PurePosixPath(e["path"])
        local_path.parent.mkdir(parents=True, exist_ok=True)
        local_path.write_bytes(content)
        written.append((local_path, len(content)))

    for local_path, size in written:
        print(f"wrote {size:>10} bytes -> {local_path}")
    print(f"\n{len(written)} files written under {dest_dir}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gh_fetch.py",
        description="Fetch a narrow slice of a GitHub repo via the REST API (no git clone).",
    )
    parser.add_argument(
        "--token",
        help="GitHub token (else GITHUB_TOKEN/GH_TOKEN env, else .env next to this script, else anonymous)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_readme = sub.add_parser("readme", help="print the repo's README")
    p_readme.add_argument("repo", help="owner/repo")
    p_readme.add_argument(
        "--ref", help="branch, tag, or commit sha (default: repo's default branch)"
    )
    p_readme.set_defaults(func=cmd_readme)

    p_list = sub.add_parser("list", help="list immediate children of a path (one directory level)")
    p_list.add_argument("repo", help="owner/repo")
    p_list.add_argument("path", nargs="?", default="", help='directory path, "" for repo root')
    p_list.add_argument("--ref", help="branch, tag, or commit sha")
    p_list.set_defaults(func=cmd_list)

    p_tree = sub.add_parser("tree", help="recursively list every file under a path")
    p_tree.add_argument("repo", help="owner/repo")
    p_tree.add_argument("path", nargs="?", default="", help='directory path, "" for repo root')
    p_tree.add_argument("--ref", help="branch, tag, or commit sha")
    p_tree.set_defaults(func=cmd_tree)

    p_get = sub.add_parser("get", help="download a single file")
    p_get.add_argument("repo", help="owner/repo")
    p_get.add_argument("path", help="file path in the repo")
    p_get.add_argument("dest", help="local destination file path")
    p_get.add_argument("--ref", help="branch, tag, or commit sha")
    p_get.set_defaults(func=cmd_get)

    p_get_tree = sub.add_parser(
        "get-tree", help="download every file under a path, preserving structure"
    )
    p_get_tree.add_argument("repo", help="owner/repo")
    p_get_tree.add_argument("path", help="directory path in the repo")
    p_get_tree.add_argument(
        "dest", help="local destination directory (path is stripped from the layout)"
    )
    p_get_tree.add_argument("--ref", help="branch, tag, or commit sha")
    p_get_tree.add_argument(
        "--include", action="append", help="fnmatch pattern, relative to path; repeatable"
    )
    p_get_tree.add_argument(
        "--exclude", action="append", help="fnmatch pattern, relative to path; repeatable"
    )
    p_get_tree.add_argument(
        "--max-files",
        type=int,
        default=200,
        help="safety cap on number of files to download in one call (default: 200)",
    )
    p_get_tree.set_defaults(func=cmd_get_tree)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    token = resolve_token(args.token)
    try:
        args.func(args, token)
    except GhFetchError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
