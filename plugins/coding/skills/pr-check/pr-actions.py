#!/usr/bin/env python3
"""GitHub Actions（ワークフロー実行）の一覧・詳細・失敗ログ・手動実行を扱う。

使い方:
  python pr-actions.py list [branch]            # 直近のrun一覧（既定: 現在のブランチ、最大20件）
  python pr-actions.py pr <PR番号>              # 対象PRのHEADコミットに紐づくrun一覧
  python pr-actions.py view <run_id>            # run詳細（ジョブ毎の成否）
  python pr-actions.py failed <run_id>          # 失敗したstepのログのみ
  python pr-actions.py run <workflow> [ref]     # ワークフロー手動実行（workflow_dispatch必須）
  python pr-actions.py watch <run_id>           # 完了まで追跡
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pr_common import run_json, current_branch, run_cli


def cmd_list(args) -> int:
    branch = args.branch or current_branch()
    print(f"### ワークフロー実行一覧（branch: {branch}）")
    runs = run_json(
        [
            "gh",
            "run",
            "list",
            "--branch",
            branch,
            "--limit",
            "20",
            "--json",
            "databaseId,displayTitle,workflowName,status,conclusion,event,headBranch,createdAt,url",
        ]
    )
    for r in runs:
        print(
            f"[{r['databaseId']}] {r['workflowName']} | {r['status']}/{r.get('conclusion') or '-'} | {r['event']} | {r['displayTitle']}"
        )
        print(f"  {r['createdAt']} {r['url']}")
    return 0


def cmd_pr(args) -> int:
    sha = run_json(["gh", "pr", "view", args.pr_number, "--json", "headRefOid"])["headRefOid"]
    print(f"### PR #{args.pr_number} HEAD ({sha[:7]}) の実行")
    runs = run_json(
        [
            "gh",
            "run",
            "list",
            "--commit",
            sha,
            "--limit",
            "20",
            "--json",
            "databaseId,displayTitle,workflowName,status,conclusion,url",
        ]
    )
    for r in runs:
        print(
            f"[{r['databaseId']}] {r['workflowName']} | {r['status']}/{r.get('conclusion') or '-'}"
        )
        print(f"  {r['url']}")
    return 0


def cmd_view(args) -> int:
    return subprocess.run(["gh", "run", "view", args.run_id]).returncode


def cmd_failed(args) -> int:
    print(f"### Run {args.run_id} 失敗ログ")
    return subprocess.run(["gh", "run", "view", args.run_id, "--log-failed"]).returncode


def cmd_run(args) -> int:
    ref = args.ref or current_branch()
    print(f"### Dispatch: {args.workflow} (ref={ref})")
    result = subprocess.run(["gh", "workflow", "run", args.workflow, "--ref", ref])
    if result.returncode == 0:
        print("※ 実行開始はわずかに遅延する。'pr-actions.py list' で run_id を確認してください。")
    return result.returncode


def cmd_watch(args) -> int:
    return subprocess.run(["gh", "run", "watch", args.run_id, "--exit-status"]).returncode


def main() -> int:
    parser = argparse.ArgumentParser(prog="pr-actions.py")
    sub = parser.add_subparsers(dest="command", required=True)

    p_list = sub.add_parser("list", help="直近のrun一覧")
    p_list.add_argument("branch", nargs="?")
    p_list.set_defaults(func=cmd_list)

    p_pr = sub.add_parser("pr", help="対象PRのHEADコミットに紐づくrun一覧")
    p_pr.add_argument("pr_number")
    p_pr.set_defaults(func=cmd_pr)

    p_view = sub.add_parser("view", help="run詳細")
    p_view.add_argument("run_id")
    p_view.set_defaults(func=cmd_view)

    p_failed = sub.add_parser("failed", help="失敗したstepのログのみ")
    p_failed.add_argument("run_id")
    p_failed.set_defaults(func=cmd_failed)

    p_run = sub.add_parser("run", help="ワークフロー手動実行")
    p_run.add_argument("workflow")
    p_run.add_argument("ref", nargs="?")
    p_run.set_defaults(func=cmd_run)

    p_watch = sub.add_parser("watch", help="完了まで追跡")
    p_watch.add_argument("run_id")
    p_watch.set_defaults(func=cmd_watch)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(run_cli(main))
