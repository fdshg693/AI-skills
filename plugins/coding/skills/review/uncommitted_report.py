#!/usr/bin/env python3
"""現在の作業ツリーにある、コミットされていない変更の差分を出力する。

対象は staged（indexに追加済み）・unstaged（追加前）・untracked（未追跡）の
すべてのファイル。読み取り専用: git diff / status / show / ls-files / rev-parse
のみを使用し、add・commit・stash・checkout など状態を変更する操作は一切行わない。

使い方:
    python uncommitted_report.py [--repo REPO] [--output-dir DIR]

出力:
    - ファイル: temp/review/<timestamp>_uncommitted/ 配下に、
      ファイルパスのアルファベット順に並べた差分を、1ファイルあたり
      MAX_LINES_PER_CHUNK行を目安に分割した diff_XXXX.diff を生成する
      （1つの変更ファイルの差分が複数のdiff_XXXX.diffにまたがることはない）。
    - 分割ファイルが複数生成された場合は、各ファイルにどのパス〜どのパスの
      差分が含まれるかをまとめた INDEX.md を生成し、標準出力には
      その INDEX.md のパスのみを出力する（エージェントはまずINDEXを読み、
      必要な diff_XXXX.diff だけを個別に読む想定）。
    - 分割が1ファイルのみで済んだ場合は、INDEX.md は生成せず、
      従来どおり差分本文を標準出力にそのまま出力する。

依存関係:
    同梱の diff_common.py（チャンク分割・.diffignoreフィルタ等の共通処理）に依存する。
    本スクリプトと同階層の .diffignore ファイル（.gitignore と同じ書式の
    パターンを記載）に、パスがマッチした差分ファイルをレビュー対象から除外する。
    このマッチングには `pathspec` パッケージ（PyPI）を使用するため、事前に
    `pip install pathspec` でグローバルにインストールしておく必要がある。
    .diffignore が存在しない場合は何も除外せず、従来どおり全差分を対象とする。
"""

import argparse
import sys
import time
from pathlib import Path

from diff_common import (
    build_block_meta,
    build_chunks,
    build_index_md,
    count_lines,
    filter_ignored_entries,
    find_repo_root,
    load_diffignore_spec,
    run_git,
    write_chunk_files,
)


def ensure_head_exists(repo_root):
    result = run_git(repo_root, ["rev-parse", "--verify", "--quiet", "HEAD"], check=False)
    if result.returncode != 0:
        raise SystemExit(
            "エラー: HEAD が見つかりません（コミットが1つも無いリポジトリの可能性があります）。"
        )


def get_tracked_changes(repo_root):
    """HEADと作業ツリーの差分（staged+unstagedを合算したもの）を取得する。"""
    result = run_git(repo_root, ["diff", "HEAD", "-M", "--name-status"])
    entries = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        status = parts[0]
        if status.startswith("R") or status.startswith("C"):
            old_path, new_path = parts[1], parts[2]
        else:
            old_path = new_path = parts[1]
        entries.append((status, old_path, new_path))
    return entries


def get_untracked_files(repo_root):
    result = run_git(repo_root, ["ls-files", "--others", "--exclude-standard"])
    return [("A", path, path) for path in result.stdout.splitlines() if path.strip()]


def get_file_at_head(repo_root, path):
    result = run_git(repo_root, ["show", f"HEAD:{path}"], check=False)
    if result.returncode != 0:
        return None
    return result.stdout


def read_working_tree_file(repo_root, path):
    try:
        text = (repo_root / path).read_text(encoding="utf-8", errors="replace")
    except (FileNotFoundError, IsADirectoryError, PermissionError):
        return None
    return text


def is_binary_tracked(repo_root, old_path, new_path):
    result = run_git(
        repo_root, ["diff", "HEAD", "-M", "--numstat", "--", old_path, new_path], check=False
    )
    return result.stdout.strip().startswith("-\t-\t")


def is_binary_untracked(repo_root, path):
    result = run_git(
        repo_root, ["diff", "--no-index", "--numstat", "--", "/dev/null", path], check=False
    )
    return result.stdout.strip().startswith("-\t-\t")


def build_output_dir(repo_root, override):
    if override:
        return Path(override)
    return repo_root / "temp" / "review" / f"{int(time.time())}_uncommitted"


def build_entry_meta(repo_root, status, old_path, new_path, untracked):
    if untracked:
        if is_binary_untracked(repo_root, new_path):
            original_lines, new_lines = 0, "N/A (binary)"
            diff_body = "(バイナリファイルのため差分は省略)\n"
        else:
            original_lines = 0
            new_text = read_working_tree_file(repo_root, new_path)
            new_lines = count_lines(new_text) if new_text is not None else 0
            diff_body = run_git(
                repo_root, ["diff", "--no-index", "--", "/dev/null", new_path], check=False
            ).stdout
            if not diff_body.strip():
                diff_body = "(差分なし)\n"
    else:
        if is_binary_tracked(repo_root, old_path, new_path):
            original_lines = new_lines = "N/A (binary)"
            diff_body = "(バイナリファイルのため差分は省略)\n"
        else:
            original_text = None if status == "A" else get_file_at_head(repo_root, old_path)
            original_lines = count_lines(original_text) if original_text is not None else 0

            if status == "D":
                new_lines = 0
            else:
                new_text = read_working_tree_file(repo_root, new_path)
                new_lines = count_lines(new_text) if new_text is not None else 0

            diff_body = run_git(
                repo_root, ["diff", "HEAD", "-M", "--", old_path, new_path], check=False
            ).stdout
            if not diff_body.strip():
                diff_body = "(差分なし)\n"

    return build_block_meta(status, old_path, new_path, original_lines, new_lines, diff_body)


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--repo", default=".", help="対象リポジトリのパス。省略時はカレントディレクトリ"
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="差分ファイルの出力先。省略時は temp/review/<timestamp>_uncommitted/ 配下",
    )
    args = parser.parse_args()

    repo_root = find_repo_root(Path(args.repo))
    ensure_head_exists(repo_root)

    tracked_entries = get_tracked_changes(repo_root)
    untracked_entries = get_untracked_files(repo_root)

    raw_entries = [(status, old, new, False) for status, old, new in tracked_entries]
    raw_entries += [(status, old, new, True) for status, old, new in untracked_entries]

    if not raw_entries:
        print("コミットされていない変更はありません（staged/unstaged/untrackedいずれも無し）。")
        return

    # ファイルパスのアルファベット順に並べる
    raw_entries.sort(key=lambda e: e[2])

    script_dir = Path(__file__).resolve().parent
    diffignore_spec = load_diffignore_spec(script_dir)
    filterable_entries = [(status, old, new) for status, old, new, _untracked in raw_entries]
    kept, ignored_paths = filter_ignored_entries(filterable_entries, diffignore_spec)
    kept_set = set(kept)
    raw_entries = [e for e in raw_entries if (e[0], e[1], e[2]) in kept_set]

    if not raw_entries:
        print(
            "コミットされていない変更はありましたが、"
            f".diffignore によりすべて除外されました（{len(ignored_paths)}件）。"
        )
        return

    entries = [
        build_entry_meta(repo_root, status, old_path, new_path, untracked)
        for status, old_path, new_path, untracked in raw_entries
    ]

    output_dir = build_output_dir(repo_root, args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    chunks = build_chunks(entries)
    chunk_paths = write_chunk_files(output_dir, chunks)

    if len(chunks) > 1:
        index_content = build_index_md(
            chunk_paths,
            chunks,
            title="未コミット変更レビュー差分 INDEX",
            meta_lines=["対象: staged + unstaged + untracked（作業ツリーの現在の状態）"],
            output_dir=output_dir,
            total_entries=len(entries),
            ignored_paths=ignored_paths,
        )
        index_path = output_dir / "INDEX.md"
        index_path.write_text(index_content, encoding="utf-8")
        print(index_path)
        return

    # 分割が1ファイルのみの場合は、従来どおり差分本文をそのまま標準出力する
    print("# 未コミット変更レビュー差分（staged + unstaged + untracked）")
    print(f"# 出力先: {output_dir}")
    print(f"# 対象ファイル数: {len(entries)}")
    if ignored_paths:
        print(f"# .diffignoreにより除外: {len(ignored_paths)}件 ({', '.join(ignored_paths)})")
    print()

    for index, entry in enumerate(entries, start=1):
        print(f"## [{index}/{len(entries)}] {entry['display_path']}")
        print(
            f"status: {entry['status']} / original_lines: {entry['original_lines']} / "
            f"new_lines: {entry['new_lines']}"
        )
        print(entry["block_text"])

    print(f"# 出力ファイル: {chunk_paths[0]}")


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as e:
        print(f"エラー: {e}", file=sys.stderr)
        sys.exit(1)
