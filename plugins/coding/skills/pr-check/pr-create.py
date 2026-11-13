#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""現在のブランチからPRを作成する。

使い方:
  uv run pr-create.py [--draft] [--base <branch>] [--title <title>] [--body <body>|--body-file <path>]
  （python でも可）
省略時:
  base   : デフォルトブランチ（gh repo view から取得）
  title  : base との差分が merge でない commit 1 件だけのとき、その件名。
           それ以外（複数 commit・最新がマージ commit）はエラーにして --title を求める
  body   : 空（gh --fill がコミット履歴から生成）
事前チェック:
  - 未コミット変更がある場合は警告
  - 既に同ブランチからPRが開いている場合は中断
  - ポインタが変わったサブモジュールの commit がそのリモートに無い場合は中断
    （--skip-submodule-check で飛ばせる）
  - リモートに未push、または upstream より先行していれば push する
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pr_common import (
    PrCheckError,
    ahead_behind,
    current_branch,
    default_branch,
    git_ok,
    run,
    run_cli,
    run_json,
)


def resolve_base_ref(base: str) -> str:
    """比較に使う base の ref。fetch 済みの origin/<base> を優先する。"""
    for ref in (f"origin/{base}", base):
        if git_ok(["rev-parse", "--verify", "--quiet", ref]):
            return ref
    raise PrCheckError(f"base ブランチ {base} が見つかりません（origin/{base} もありません）")


def decide_title(base_ref: str) -> str:
    """--title が無いときのタイトル。曖昧なら PrCheckError で止める。"""
    commits = run(["git", "log", "--no-merges", "--pretty=%s", f"{base_ref}..HEAD"]).stdout
    subjects = [s for s in commits.splitlines() if s.strip()]
    head_is_merge = git_ok(["rev-parse", "--verify", "--quiet", "HEAD^2"])
    if len(subjects) == 1 and not head_is_merge:
        return subjects[0]
    if not subjects:
        raise PrCheckError(f"{base_ref}..HEAD に merge 以外の commit がありません")
    reason = "最新の commit がマージ commit" if head_is_merge else f"commit が {len(subjects)} 件"
    raise PrCheckError(
        f"{reason} のため、タイトルを自動で決められません。--title で PR 全体を表すタイトルを指定してください。\n"
        f"  確認: git log --oneline {base_ref}..HEAD"
    )


def changed_submodules(base_ref: str) -> list[tuple[str, str]]:
    """base_ref...HEAD でポインタが変わったサブモジュールの (path, 新しいsha)。"""
    raw = run(["git", "diff", "--raw", "--no-abbrev", f"{base_ref}...HEAD"]).stdout
    result = []
    for line in raw.splitlines():
        meta, _, path = line.partition("\t")
        fields = meta.split()
        # :<old_mode> <new_mode> <old_sha> <new_sha> <status>
        if len(fields) >= 5 and fields[1] == "160000" and not fields[4].startswith("D"):
            result.append((path, fields[3]))
    return result


def unpushed_submodules(base_ref: str) -> list[str]:
    top = run(["git", "rev-parse", "--show-toplevel"]).stdout.strip()
    problems = []
    for path, sha in changed_submodules(base_ref):
        sub_dir = Path(top, path)
        sub = ["git", "-C", str(sub_dir)]
        if not (sub_dir / ".git").exists():
            problems.append(f"{path}: 未初期化のため確認できません（{sha[:7]}）")
            continue
        subprocess.run([*sub, "fetch", "--quiet", "origin"], check=False)
        contains = run([*sub, "branch", "-r", "--contains", sha], check=False)
        if contains.returncode != 0:
            problems.append(f"{path}: commit {sha[:7]} がサブモジュールにありません")
        elif not contains.stdout.strip():
            problems.append(
                f"{path}: commit {sha[:7]} がリモートのどのブランチにもありません（未push）"
            )
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(prog="pr-create.py")
    parser.add_argument("--draft", action="store_true")
    parser.add_argument("--base")
    parser.add_argument("--title")
    parser.add_argument("--body")
    parser.add_argument("--body-file")
    parser.add_argument(
        "--skip-submodule-check",
        action="store_true",
        help="サブモジュールのポインタ先がリモートにあるかの確認を飛ばす",
    )
    args = parser.parse_args()

    branch = current_branch()
    if not branch or branch == "HEAD":
        print("現在のブランチを特定できません（detached HEAD?）", file=sys.stderr)
        return 1

    default = default_branch()
    base = args.base or default
    if branch == base:
        print(f"base ブランチ({base})自身からはPRを作れません", file=sys.stderr)
        return 1

    status = run(["git", "status", "--porcelain"]).stdout
    if status.strip():
        print(
            "⚠ 未コミットの変更があります。続行前にコミット/スタッシュを検討してください。",
            file=sys.stderr,
        )

    existing = run_json(
        ["gh", "pr", "list", "--head", branch, "--state", "open", "--json", "number,url"]
    )
    if existing:
        print(f"既にオープンなPRが存在します: {json.dumps(existing[0])}", file=sys.stderr)
        return 1

    base_ref = resolve_base_ref(base)
    title = args.title or decide_title(base_ref)

    if not args.skip_submodule_check:
        problems = unpushed_submodules(base_ref)
        if problems:
            print(
                "サブモジュールのポインタ先がリモートにありません。先にサブモジュール側を push してください:",
                file=sys.stderr,
            )
            for p in problems:
                print(f"  - {p}", file=sys.stderr)
            return 1

    remote = f"origin/{branch}"
    if not git_ok(["rev-parse", "--verify", "--quiet", remote]):
        print(f"リモートに {branch} が未push。push します...", flush=True)
        subprocess.run(["git", "push", "-u", "origin", branch], check=True)
    else:
        counts = ahead_behind("HEAD", remote)
        if counts and counts[1] > 0:
            print(
                f"{remote} にローカルに無い commit が {counts[1]} 件あります。取り込んでから再実行してください",
                file=sys.stderr,
            )
            return 1
        if counts and counts[0] > 0:
            print(f"{remote} より {counts[0]} commit 先行。push します...", flush=True)
            subprocess.run(["git", "push", "origin", branch], check=True)

    gh_args = ["gh", "pr", "create", "--head", branch, "--base", base, "--title", title]
    if args.draft:
        gh_args.append("--draft")

    if args.body_file:
        gh_args += ["--body-file", args.body_file]
    elif args.body:
        gh_args += ["--body", args.body]
    else:
        # --fill は本文をコミット履歴から作る。--title を渡しているのでタイトルは上書きされない
        gh_args.append("--fill")

    print(f"### PR作成: {' '.join(gh_args)}", flush=True)
    return subprocess.run(gh_args).returncode


if __name__ == "__main__":
    raise SystemExit(run_cli(main))
