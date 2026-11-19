#!/usr/bin/env python3
"""現在のブランチからPRを作成する。

使い方:
  python pr-create.py [--draft] [--base <branch>] [--title <title>] [--body <body>|--body-file <path>]
                      [--skip-submodule-check]
省略時:
  base   : デフォルトブランチ（gh repo view から取得）
  title  : base との差分が 1 コミットならその件名。2 コミット以上なら --title 必須
  body   : 空（gh がコミット履歴から生成）
事前チェック:
  - 未コミット変更がある場合は警告
  - 既に同ブランチからPRが開いている場合は中断
  - ポインタが変わったサブモジュールの commit がそのリモートに無い場合は中断
    （--skip-submodule-check で飛ばせる）
  - origin/<branch> にローカルに無い commit があれば中断する
  - リモート未作成、またはローカルが origin/<branch> より先行していれば push する
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pr_common import run, run_json, current_branch, default_branch, run_cli


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
    if branch == default:
        print(f"デフォルトブランチ({default})からはPRを作れません", file=sys.stderr)
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

    base = args.base or default
    run(["git", "fetch", "--quiet", "origin"], check=False)

    commits = run(
        ["git", "log", "--oneline", f"origin/{base}..HEAD"], check=False
    ).stdout.splitlines()
    if not commits:
        print(f"origin/{base} との差分コミットがありません", file=sys.stderr)
        return 1
    if len(commits) > 1 and not args.title:
        print(
            f"origin/{base} との差分が {len(commits)} コミットあります。"
            "全体を表す --title を指定してください:\n" + "\n".join(commits),
            file=sys.stderr,
        )
        return 1

    if not args.skip_submodule_check:
        problems = unpushed_submodules(f"origin/{base}")
        if problems:
            print(
                "サブモジュールのポインタ先がリモートにありません。先にサブモジュール側を push してください:\n"
                + "\n".join(f"  - {p}" for p in problems),
                file=sys.stderr,
            )
            return 1

    verify = run(["git", "rev-parse", "--verify", "--quiet", f"origin/{branch}"], check=False)
    if verify.returncode != 0:
        print(f"リモートに {branch} が未push。push します...")
        subprocess.run(["git", "push", "-u", "origin", branch], check=True)
    else:
        behind = run(["git", "rev-list", "--count", f"HEAD..origin/{branch}"]).stdout.strip()
        if behind != "0":
            print(
                f"origin/{branch} にローカルに無い commit が {behind} 件あります。取り込んでから再実行してください",
                file=sys.stderr,
            )
            return 1
        ahead = run(["git", "rev-list", "--count", f"origin/{branch}..HEAD"]).stdout.strip()
        if ahead != "0":
            print(f"ローカルが origin/{branch} より {ahead} コミット先行。push します...")
            subprocess.run(["git", "push", "origin", branch], check=True)

    gh_args = ["gh", "pr", "create", "--head", branch, "--base", base]
    if args.draft:
        gh_args.append("--draft")

    if args.title:
        gh_args += ["--title", args.title]
    else:
        title = run(["git", "log", "-1", "--pretty=%s"]).stdout.strip()
        gh_args += ["--title", title]

    if args.body_file:
        gh_args += ["--body-file", args.body_file]
    elif args.body:
        gh_args += ["--body", args.body]
    else:
        gh_args.append("--fill")
        # --fill はコミット履歴から自動生成。--title と併用時は title のみ上書き。

    print(f"### PR作成: {' '.join(gh_args)}")
    return subprocess.run(gh_args).returncode


if __name__ == "__main__":
    raise SystemExit(run_cli(main))
