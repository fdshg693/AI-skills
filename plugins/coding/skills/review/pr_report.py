#!/usr/bin/env python3
"""GitHub上の既存PRの差分とコメントを gh CLI で取得して出力する。

読み取り専用: gh pr view / gh pr diff / gh api (GET) のみを使用し、
コメント投稿・approve・merge・checkout など状態を変更する操作は一切行わない。
ローカルの作業ツリー・ブランチには触れないため、PRのブランチをcheckoutしていなくてよい。

使い方:
    python pr_report.py [PR] [--gh-repo OWNER/REPO] [--repo REPO] [--output-dir DIR]
                        [--max-body-chars N]

    PR には PR番号(`123` / `#123`)またはPRのURLを指定する。省略時は
    現在のブランチに紐づくPRを gh で検出する。

出力:
    - ファイル: temp/review/<timestamp>_pr<番号>/ 配下に、
      ファイルパスのアルファベット順に並べた差分を、1ファイルあたり
      MAX_LINES_PER_CHUNK行を目安に分割した diff_XXXX.diff を生成する
      （1つの変更ファイルの差分が複数のdiff_XXXX.diffにまたがることはない）。
      各ブロックの数値列は additions / deletions（PRの差分から数えた追加・削除行数）。
    - 同じディレクトリに COMMENTS.md（PR本文・会話コメント・レビュー本文・
      インラインレビューコメント）を必ず生成する。
    - 分割ファイルが複数生成された場合は INDEX.md を生成し、標準出力には
      INDEX.md と COMMENTS.md のパスのみを出力する。
    - 分割が1ファイルのみで済んだ場合は、INDEX.md は生成せず、
      差分本文を標準出力にそのまま出力する（COMMENTS.md のパスも併記する）。

依存関係:
    gh CLI (https://cli.github.com/) がインストール・認証済みであること。
    見つからない・未認証の場合はエラーで終了する（git へのフォールバックはしない）。
    同梱の diff_common.py に依存し、同階層の .diffignore による除外も
    diff_report.py と同じく適用する（パターンがあれば pathspec が必要）。
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

from diff_common import (
    build_block_meta,
    build_chunks,
    build_index_md,
    filter_ignored_entries,
    load_diffignore_spec,
    write_chunk_files,
)

PR_URL_PATTERN = re.compile(r"github\.com/([^/]+)/([^/]+)/pull/(\d+)")
PR_LINE_LABELS = ("additions", "deletions")


def run_gh(args, cwd):
    result = subprocess.run(
        ["gh", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"gh {' '.join(args)} failed:\n{result.stderr.strip()}\n"
            "（未認証の場合は `gh auth login`、リポジトリ外の場合は --gh-repo OWNER/REPO を指定する）"
        )
    return result.stdout


def ensure_gh_available():
    if shutil.which("gh") is None:
        raise SystemExit(
            "エラー: gh CLI が見つかりません。PRレビューには gh が必須です"
            "（https://cli.github.com/ からインストールし、`gh auth login` で認証してください）。"
        )


def find_base_dir(start):
    """出力先の基準ディレクトリ。Gitリポジトリ内ならそのルート、外ならカレントディレクトリ。"""
    result = subprocess.run(
        ["git", "-C", str(start), "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode == 0:
        return Path(result.stdout.strip())
    return Path(start).resolve()


def parse_pr_arg(pr_arg, gh_repo):
    """(PRセレクタ, OWNER/REPO or None) を返す。URL指定時はURLのリポジトリを優先する。"""
    if pr_arg is None:
        return None, gh_repo
    match = PR_URL_PATTERN.search(pr_arg)
    if match:
        owner, repo, number = match.groups()
        return number, f"{owner}/{repo}"
    number = pr_arg.lstrip("#")
    if not number.isdigit() or int(number) <= 0:
        raise SystemExit(f"エラー: PR には正の整数またはPRのURLを指定してください: {pr_arg}")
    return number, gh_repo


def repo_flag(gh_repo):
    return ["-R", gh_repo] if gh_repo else []


def fetch_pr_meta(pr_number, gh_repo, cwd):
    fields = (
        "number,title,url,author,state,isDraft,baseRefName,headRefName,"
        "baseRefOid,headRefOid,additions,deletions,changedFiles,body,comments,reviews"
    )
    selector = [pr_number] if pr_number else []
    raw = run_gh(["pr", "view", *selector, *repo_flag(gh_repo), "--json", fields], cwd)
    return json.loads(raw)


def fetch_inline_comments(pr_number, gh_repo, cwd):
    repo_path = gh_repo if gh_repo else "{owner}/{repo}"
    raw = run_gh(
        ["api", f"repos/{repo_path}/pulls/{pr_number}/comments", "--paginate", "--jq", ".[]"],
        cwd,
    )
    return [json.loads(line) for line in raw.splitlines() if line.strip()]


def _strip_prefix(path, prefix):
    return path[len(prefix) :] if path.startswith(prefix) else path


def parse_diff_blocks(diff_text):
    """gh pr diff の生テキストを 'diff --git' ごとに分割し、
    (status, old_path, new_path, additions, deletions, binary, block_text) を返す。

    ファイル一覧は `gh pr view --json files`（100件で打ち切られる）ではなく
    生差分から求める。
    """
    lines = diff_text.splitlines()
    starts = [i for i, line in enumerate(lines) if line.startswith("diff --git ")]
    blocks = []
    for idx, start in enumerate(starts):
        end = starts[idx + 1] if idx + 1 < len(starts) else len(lines)
        block = lines[start:end]

        header_paths = block[0][len("diff --git ") :].split(" b/", 1)
        old_path = _strip_prefix(header_paths[0], "a/")
        new_path = header_paths[1] if len(header_paths) == 2 else old_path
        status = "M"
        move_kind = None  # "R"(rename) / "C"(copy)
        similarity = ""
        binary = False
        additions = deletions = 0
        in_hunk = False

        for line in block[1:]:
            if in_hunk:
                if line.startswith("+"):
                    additions += 1
                elif line.startswith("-"):
                    deletions += 1
                continue
            if line.startswith("@@"):
                in_hunk = True
            elif line.startswith("new file mode"):
                status = "A"
            elif line.startswith("deleted file mode"):
                status = "D"
            elif line.startswith("similarity index"):
                similarity = line.split()[-1].rstrip("%")
            elif line.startswith(("rename from ", "copy from ")):
                move_kind = "R" if line.startswith("rename") else "C"
                old_path = line.split(" from ", 1)[1]
            elif line.startswith(("rename to ", "copy to ")):
                new_path = line.split(" to ", 1)[1]
            elif line.startswith("--- ") and not line.startswith("--- /dev/null"):
                old_path = _strip_prefix(line[4:], "a/")
            elif line.startswith("+++ ") and not line.startswith("+++ /dev/null"):
                new_path = _strip_prefix(line[4:], "b/")
            elif line.startswith("Binary files ") or line.startswith("GIT binary patch"):
                binary = True

        if move_kind:
            status = move_kind + similarity
        elif status == "A":
            old_path = new_path
        elif status == "D":
            new_path = old_path

        blocks.append(
            (status, old_path, new_path, additions, deletions, binary, "\n".join(block) + "\n")
        )
    return blocks


def truncate(body, max_chars):
    body = (body or "").strip()
    if not body:
        return None
    if len(body) > max_chars:
        return body[:max_chars] + f"\n\n…（{len(body) - max_chars}文字省略）"
    return body


def build_comments_md(meta, inline_comments, max_chars):
    issue_comments = [c for c in meta.get("comments") or [] if truncate(c.get("body"), max_chars)]
    reviews = [r for r in meta.get("reviews") or [] if truncate(r.get("body"), max_chars)]
    inline = [c for c in inline_comments if truncate(c.get("body"), max_chars)]
    inline.sort(key=lambda c: (c.get("path") or "", c.get("line") or c.get("original_line") or 0))

    lines = [
        f"# PR #{meta['number']} コメント",
        "",
        f"- タイトル: {meta['title']}",
        f"- URL: {meta['url']}",
        "",
        "## PR本文",
        "",
        truncate(meta.get("body"), max_chars) or "（本文なし）",
        "",
        f"## 会話コメント (issue comments)（{len(issue_comments)}件）",
        "",
    ]
    if not issue_comments:
        lines += ["（本文のあるコメントなし）", ""]
    for c in issue_comments:
        author = (c.get("author") or {}).get("login", "不明")
        lines += [
            f"### {author} - {c.get('createdAt', '')}",
            "",
            truncate(c["body"], max_chars),
            "",
        ]

    lines += [f"## レビュー本文 (reviews)（{len(reviews)}件）", ""]
    if not reviews:
        lines += ["（本文のあるレビューなし）", ""]
    for r in reviews:
        author = (r.get("author") or {}).get("login", "不明")
        lines += [
            f"### {author} - {r.get('state', '')} - {r.get('submittedAt', '')}",
            "",
            truncate(r["body"], max_chars),
            "",
        ]

    lines += [f"## インラインレビューコメント (diff内コメント)（{len(inline)}件）", ""]
    if not inline:
        lines += ["（本文のあるインラインコメントなし）", ""]
    for c in inline:
        author = (c.get("user") or {}).get("login", "不明")
        line_no = c.get("line") or c.get("original_line") or "?"
        notes = []
        if c.get("in_reply_to_id"):
            notes.append("返信")
        if c.get("line") is None:
            notes.append("outdated")
        note = f"（{'・'.join(notes)}）" if notes else ""
        lines += [
            f"### `{c.get('path', '(パス不明)')}:{line_no}` - {author}{note} - {c.get('created_at', '')}",
            "",
            truncate(c["body"], max_chars),
            "",
        ]

    counts = {
        "issue_comments": len(issue_comments),
        "reviews": len(reviews),
        "inline_comments": len(inline),
    }
    return "\n".join(lines), counts


def build_output_dir(base_dir, pr_number, override):
    if override:
        return Path(override)
    return base_dir / "temp" / "review" / f"{int(time.time())}_pr{pr_number}"


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "pr",
        nargs="?",
        default=None,
        help="PR番号(123 / #123)またはPRのURL。省略時は現在のブランチのPR",
    )
    parser.add_argument(
        "--gh-repo",
        default=None,
        help="PRのあるGitHubリポジトリ(OWNER/REPO)。省略時はカレントのリポジトリ",
    )
    parser.add_argument(
        "--repo",
        default=".",
        help="gh を実行するディレクトリ(出力先の基準)。省略時はカレントディレクトリ",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="出力先。省略時は temp/review/<timestamp>_pr<番号>/ 配下",
    )
    parser.add_argument(
        "--max-body-chars",
        type=int,
        default=4000,
        help="COMMENTS.md のコメント本文1件あたりの最大文字数(デフォルト4000)",
    )
    args = parser.parse_args()

    ensure_gh_available()
    base_dir = find_base_dir(Path(args.repo))
    pr_selector, gh_repo = parse_pr_arg(args.pr, args.gh_repo)

    meta = fetch_pr_meta(pr_selector, gh_repo, base_dir)
    pr_number = str(meta["number"])

    diff_text = run_gh(["pr", "diff", pr_number, *repo_flag(gh_repo)], base_dir)
    inline_comments = fetch_inline_comments(pr_number, gh_repo, base_dir)

    output_dir = build_output_dir(base_dir, pr_number, args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    comments_md, comment_counts = build_comments_md(meta, inline_comments, args.max_body_chars)
    comments_path = output_dir / "COMMENTS.md"
    comments_path.write_text(comments_md, encoding="utf-8")
    comments_summary = (
        f"会話 {comment_counts['issue_comments']}件 / レビュー {comment_counts['reviews']}件 / "
        f"インライン {comment_counts['inline_comments']}件"
    )

    blocks = parse_diff_blocks(diff_text)
    title = f"PR #{pr_number}: {meta['title']}"
    pr_meta_lines = [
        f"URL: {meta['url']}",
        f"作成者: {(meta.get('author') or {}).get('login', '不明')}",
        f"ブランチ: {meta['headRefName']} -> {meta['baseRefName']}",
        f"状態: {meta['state']}{'（Draft）' if meta.get('isDraft') else ''}",
        f"head: {meta['headRefOid']} / base: {meta['baseRefOid']}",
        f"変更規模: {meta['changedFiles']}ファイル (+{meta['additions']} -{meta['deletions']})",
        f"コメント: {comments_path}（{comments_summary}）",
    ]

    if not blocks:
        print(f"{title} に差分ファイルはありません。")
        print(f"# コメント: {comments_path}（{comments_summary}）")
        return

    if len(blocks) != meta["changedFiles"]:
        print(
            f"警告: PRの changedFiles({meta['changedFiles']}) と差分から検出したファイル数"
            f"({len(blocks)})が一致しません。INDEX/差分の内容を確認してください。",
            file=sys.stderr,
        )

    blocks.sort(key=lambda b: b[2])
    by_key = {(b[0], b[1], b[2]): b for b in blocks}

    script_dir = Path(__file__).resolve().parent
    diffignore_spec = load_diffignore_spec(script_dir)
    kept, ignored_paths = filter_ignored_entries(list(by_key), diffignore_spec)

    if not kept:
        print(
            f"{title} に差分ファイルはありましたが、"
            f".diffignore によりすべて除外されました（{len(ignored_paths)}件）。"
        )
        print(f"# コメント: {comments_path}（{comments_summary}）")
        return

    entries = []
    for key in kept:
        status, old_path, new_path, additions, deletions, binary, block_text = by_key[key]
        if binary:
            additions = deletions = "N/A (binary)"
            block_text = "(バイナリファイルのため差分は省略)\n"
        entries.append(
            build_block_meta(
                status, old_path, new_path, additions, deletions, block_text, PR_LINE_LABELS
            )
        )

    chunks = build_chunks(entries)
    chunk_paths = write_chunk_files(output_dir, chunks)

    if len(chunks) > 1:
        index_content = build_index_md(
            chunk_paths,
            chunks,
            title=f"PRレビュー差分 INDEX: {title}",
            meta_lines=pr_meta_lines,
            output_dir=output_dir,
            total_entries=len(entries),
            ignored_paths=ignored_paths,
        )
        index_path = output_dir / "INDEX.md"
        index_path.write_text(index_content, encoding="utf-8")
        print(index_path)
        print(comments_path)
        return

    # 分割が1ファイルのみの場合は、差分本文をそのまま標準出力する
    print(f"# PRレビュー差分: {title}")
    for line in pr_meta_lines:
        print(f"# {line}")
    print(f"# 出力先: {output_dir}")
    print(f"# 対象ファイル数: {len(entries)}")
    if ignored_paths:
        print(f"# .diffignoreにより除外: {len(ignored_paths)}件 ({', '.join(ignored_paths)})")
    print()

    for index, entry in enumerate(entries, start=1):
        print(f"## [{index}/{len(entries)}] {entry['display_path']}")
        print(
            f"status: {entry['status']} / additions: {entry['original_lines']} / "
            f"deletions: {entry['new_lines']}"
        )
        print(entry["block_text"])

    print(f"# 出力ファイル: {chunk_paths[0]}")


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as e:
        print(f"エラー: {e}", file=sys.stderr)
        sys.exit(1)
