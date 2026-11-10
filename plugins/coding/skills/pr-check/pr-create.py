#!/usr/bin/env python3
"""現在のブランチからPRを作成する。

使い方:
  python pr-create.py [--draft] [--base <branch>] [--title <title>] [--body <body>|--body-file <path>]
省略時:
  base   : デフォルトブランチ（gh repo view から取得）
  title  : 直近コミットの件名
  body   : 空（gh がコミット履歴から生成）
事前チェック:
  - 未コミット変更がある場合は警告
  - 既に同ブランチからPRが開いている場合は中断
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pr_common import run, run_json, current_branch, default_branch, run_cli


def main() -> int:
    parser = argparse.ArgumentParser(prog="pr-create.py")
    parser.add_argument("--draft", action="store_true")
    parser.add_argument("--base")
    parser.add_argument("--title")
    parser.add_argument("--body")
    parser.add_argument("--body-file")
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

    verify = run(["git", "rev-parse", "--verify", "--quiet", f"origin/{branch}"], check=False)
    if verify.returncode != 0:
        print(f"リモートに {branch} が未push。push します...")
        subprocess.run(["git", "push", "-u", "origin", branch], check=True)

    gh_args = ["gh", "pr", "create", "--head", branch]
    if args.base:
        gh_args += ["--base", args.base]
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
