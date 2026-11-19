#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pathspec"]
# ///
"""現在のブランチから指定したマージ先ブランチへPRを作ると仮定し、その差分を出力する。

読み取り専用: git diff / show / merge-base / rev-parse のみを使用し、
checkout・merge・commit・push など状態を変更する操作は一切行わない。

使い方:
    uv run diff_report.py <target-branch> [--source SOURCE] [--repo REPO] [--output-dir DIR]
                          [--local-target]

マージ先の解決:
    ブランチ名だけを渡すと、リモート追跡ブランチ origin/<target> があればそちらを使う
    （PR のマージ先は GitHub 上の <target> なので、古いローカルの <target> と比べない）。
    ローカルの <target> と origin/<target> がずれていれば stderr に件数を出す。
    ローカルの <target> を使いたいときは --local-target。fetch はしないので、
    origin/<target> 自体が古いときは事前に `git fetch` するようユーザーに伝える。

サブモジュール:
    ポインタが変わったサブモジュールは、差分ブロックにサブモジュール内のコミット一覧と、
    新しい commit がリモートのどこかのブランチに含まれるか（未push の検出）を出す。
    INDEX.md / 標準出力の冒頭にも要約を出す。

出力:
    - ファイル: temp/review/<timestamp>_<hash(target,source)>/ 配下に、
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
    このマッチングには `pathspec` パッケージ（PyPI）を使用する。`uv run` で実行すれば
    PEP 723 のメタデータから自動で入る（uv を使わない場合は `pip install pathspec`）。
    .diffignore が存在しない場合は何も除外せず、従来どおり全差分を対象とする。
"""

import argparse
import hashlib
import sys
import time
from pathlib import Path

from diff_common import (
    build_block_meta,
    describe_submodule_change,
    parse_raw_gitlinks,
    build_chunks,
    build_index_md,
    count_lines,
    filter_ignored_entries,
    find_repo_root,
    load_diffignore_spec,
    run_git,
    write_chunk_files,
)


def resolve_target(repo_root, name, use_local):
    """マージ先は origin/<name> を優先する。ローカルとずれていれば stderr に出す。"""
    if use_local or ("/" in name and name.split("/", 1)[0] in remotes(repo_root)):
        return resolve_branch(repo_root, name, "マージ先ブランチ")
    remote_name = f"origin/{name}"
    if not exact_ref(repo_root, f"refs/remotes/{remote_name}"):
        # ブランチ名でない(HEAD~3 や sha 等)、または origin に無い
        return resolve_branch(repo_root, name, "マージ先ブランチ")
    if exact_ref(repo_root, f"refs/heads/{name}"):
        counts = run_git(
            repo_root, ["rev-list", "--left-right", "--count", f"{name}...{remote_name}"]
        ).stdout.split()
        local_only, remote_only = int(counts[0]), int(counts[1])
        if local_only or remote_only:
            print(
                f"注意: ローカルの {name} は {remote_name} と {remote_only} commit 遅れ・"
                f"{local_only} commit 先行。PR のマージ先に合わせて {remote_name} と比較する"
                "（ローカルと比べるなら --local-target）。",
                file=sys.stderr,
            )
    return remote_name


def remotes(repo_root):
    return run_git(repo_root, ["remote"], check=False).stdout.split()


def exact_ref(repo_root, full_ref):
    return (
        run_git(repo_root, ["show-ref", "--verify", "--quiet", full_ref], check=False).returncode
        == 0
    )


def resolve_branch(repo_root, name, label):
    result = run_git(repo_root, ["rev-parse", "--verify", "--quiet", name], check=False)
    if result.returncode == 0:
        return name
    remote_name = f"origin/{name}"
    result = run_git(repo_root, ["rev-parse", "--verify", "--quiet", remote_name], check=False)
    if result.returncode == 0:
        return remote_name
    raise SystemExit(
        f"エラー: {label} '{name}' が見つかりません（ローカル・origin/{name} のどちらにも存在しません）。"
    )


def get_file_at_ref(repo_root, ref, path):
    result = run_git(repo_root, ["show", f"{ref}:{path}"], check=False)
    if result.returncode != 0:
        return None
    return result.stdout


def parse_name_status(output):
    entries = []
    for line in output.splitlines():
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


def is_binary(repo_root, diff_range, old_path, new_path):
    result = run_git(
        repo_root, ["diff", "-M", "--numstat", diff_range, "--", old_path, new_path], check=False
    )
    line = result.stdout.strip()
    return line.startswith("-\t-\t")


def build_output_dir(repo_root, target_ref, source_ref, override):
    if override:
        return Path(override)
    digest = hashlib.sha1(f"{target_ref}|{source_ref}".encode("utf-8")).hexdigest()[:8]
    folder_name = f"{int(time.time())}_{digest}"
    return repo_root / "temp" / "review" / folder_name


def build_entry_meta(
    repo_root, diff_range, merge_base_sha, source_ref, status, old_path, new_path, gitlinks
):
    if new_path in gitlinks:
        old_sha, new_sha = gitlinks[new_path]
        diff_body, _ = describe_submodule_change(repo_root, new_path, old_sha, new_sha)
        return build_block_meta(
            status, old_path, new_path, "N/A (submodule)", "N/A (submodule)", diff_body
        )

    binary = is_binary(repo_root, diff_range, old_path, new_path)

    if binary:
        original_lines = new_lines = "N/A (binary)"
        diff_body = "(バイナリファイルのため差分は省略)\n"
    else:
        original_text = (
            None if status == "A" else get_file_at_ref(repo_root, merge_base_sha, old_path)
        )
        original_lines = count_lines(original_text) if original_text is not None else 0

        new_text = None if status == "D" else get_file_at_ref(repo_root, source_ref, new_path)
        new_lines = count_lines(new_text) if new_text is not None else 0

        diff_body = run_git(
            repo_root, ["diff", "-M", diff_range, "--", old_path, new_path], check=False
        ).stdout
        if not diff_body.strip():
            diff_body = "(差分なし)\n"

    return build_block_meta(status, old_path, new_path, original_lines, new_lines, diff_body)


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("target", help="マージ先ブランチ名 (例: main)")
    parser.add_argument("--source", default=None, help="マージ元ブランチ名。省略時は現在のブランチ")
    parser.add_argument(
        "--repo", default=".", help="対象リポジトリのパス。省略時はカレントディレクトリ"
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="差分ファイルの出力先。省略時は temp/review/<timestamp>_<hash>/ 配下",
    )
    parser.add_argument(
        "--local-target",
        action="store_true",
        help="マージ先に origin/<target> ではなくローカルの <target> を使う",
    )
    args = parser.parse_args()

    repo_root = find_repo_root(Path(args.repo))

    source = args.source
    if source is None:
        head = run_git(repo_root, ["rev-parse", "--abbrev-ref", "HEAD"]).stdout.strip()
        if head == "HEAD":
            raise SystemExit(
                "エラー: 現在detached HEAD状態のため現在のブランチを特定できません。--source でブランチ名を指定してください。"
            )
        source = head

    target_ref = resolve_target(repo_root, args.target, args.local_target)
    source_ref = resolve_branch(repo_root, source, "マージ元ブランチ")

    if target_ref == source_ref:
        print(f"マージ先とマージ元が同一です ({target_ref})。差分はありません。")
        return

    merge_base = run_git(repo_root, ["merge-base", target_ref, source_ref], check=False)
    if merge_base.returncode != 0:
        raise SystemExit(
            f"エラー: {target_ref} と {source_ref} の共通の祖先が見つかりません（履歴が無関係な可能性があります）。"
        )
    merge_base_sha = merge_base.stdout.strip()

    diff_range = f"{target_ref}...{source_ref}"
    name_status = run_git(repo_root, ["diff", "-M", "--name-status", diff_range])
    raw_entries = parse_name_status(name_status.stdout)

    if not raw_entries:
        print(f"{source_ref} -> {target_ref} の間に差分ファイルはありません。")
        return

    # ファイルパスのアルファベット順に並べる
    raw_entries.sort(key=lambda e: e[2])

    script_dir = Path(__file__).resolve().parent
    diffignore_spec = load_diffignore_spec(script_dir)
    raw_entries, ignored_paths = filter_ignored_entries(raw_entries, diffignore_spec)

    if not raw_entries:
        print(
            f"{source_ref} -> {target_ref} の間に差分ファイルはありましたが、"
            f".diffignore によりすべて除外されました（{len(ignored_paths)}件）。"
        )
        return

    gitlinks = parse_raw_gitlinks(
        run_git(repo_root, ["diff", "--raw", "--no-abbrev", diff_range]).stdout
    )
    submodule_summaries = [
        describe_submodule_change(repo_root, path, old_sha, new_sha)[1]
        for path, (old_sha, new_sha) in sorted(gitlinks.items())
        if any(path == e[2] for e in raw_entries)
    ]

    entries = [
        build_entry_meta(
            repo_root, diff_range, merge_base_sha, source_ref, status, old_path, new_path, gitlinks
        )
        for status, old_path, new_path in raw_entries
    ]

    output_dir = build_output_dir(repo_root, target_ref, source_ref, args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    chunks = build_chunks(entries)
    chunk_paths = write_chunk_files(output_dir, chunks)

    if len(chunks) > 1:
        index_content = build_index_md(
            chunk_paths,
            chunks,
            title=f"PRレビュー差分 INDEX（想定PR）: {source_ref} -> {target_ref}",
            meta_lines=[f"merge-base: {merge_base_sha}"],
            output_dir=output_dir,
            total_entries=len(entries),
            ignored_paths=ignored_paths,
            extra_sections=(
                [("サブモジュールの変更", "".join(f"- {line}\n" for line in submodule_summaries))]
                if submodule_summaries
                else []
            ),
        )
        index_path = output_dir / "INDEX.md"
        index_path.write_text(index_content, encoding="utf-8")
        print(index_path)
        return

    # 分割が1ファイルのみの場合は、従来どおり差分本文をそのまま標準出力する
    print(f"# PRレビュー差分（想定PR）: {source_ref} -> {target_ref}")
    print(f"# merge-base: {merge_base_sha}")
    print(f"# 出力先: {output_dir}")
    print(f"# 対象ファイル数: {len(entries)}")
    if ignored_paths:
        print(f"# .diffignoreにより除外: {len(ignored_paths)}件 ({', '.join(ignored_paths)})")
    for line in submodule_summaries:
        print(f"# サブモジュール: {line}")
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
