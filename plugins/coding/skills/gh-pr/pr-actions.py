#!/usr/bin/env python3
"""GitHub Actions（ワークフロー実行）の一覧・詳細・失敗ログ・手動実行を扱う。

使い方（全サブコマンドで -R OWNER/REPO を付けられる。既定はカレントディレクトリのリポジトリ）:
  python pr-actions.py list [branch]            # 直近のrun一覧（既定: 現在のブランチ、最大20件）
  python pr-actions.py pr <PR番号>              # 対象PRのHEADコミットに紐づくrun一覧
  python pr-actions.py view <run_id|URL>        # run詳細（ジョブ毎の成否とannotations）。job URLならそのjobだけ
  python pr-actions.py failed <run_id|URL>      # 失敗したstepのログのみ。job URLならそのjobだけ
  python pr-actions.py run <workflow> [ref]     # ワークフロー手動実行（workflow_dispatch必須）
  python pr-actions.py watch <run_id|URL>       # 完了まで追跡

URL は .../actions/runs/<id>、.../attempts/<n>、.../job/<id> を受け付け、URL のリポジトリを対象にする。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pr_common import current_branch, parse_run_target, run_cli, run_json, set_repo, stream


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


def _run_view(target: str, extra: list[str]) -> list[str]:
    run_id, job_id = parse_run_target(target)
    cmd = ["gh", "run", "view", run_id, *extra]
    if job_id:
        cmd += ["--job", job_id]
    return cmd


def cmd_view(args) -> int:
    return stream(_run_view(args.target, []))


def cmd_failed(args) -> int:
    cmd = _run_view(args.target, ["--log-failed"])
    print(f"### Run {cmd[3]} 失敗ログ")
    return stream(cmd)


def cmd_run(args) -> int:
    ref = args.ref or current_branch()
    print(f"### Dispatch: {args.workflow} (ref={ref})")
    code = stream(["gh", "workflow", "run", args.workflow, "--ref", ref])
    if code == 0:
        print("※ 実行開始はわずかに遅延する。'pr-actions.py list' で run_id を確認してください。")
    return code


def cmd_watch(args) -> int:
    run_id, _ = parse_run_target(args.target)
    return stream(["gh", "run", "watch", run_id, "--exit-status"])


def main() -> int:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "-R", "--repo", help="対象リポジトリ OWNER/REPO（既定: カレントディレクトリのリポジトリ）"
    )

    parser = argparse.ArgumentParser(prog="pr-actions.py")
    sub = parser.add_subparsers(dest="command", required=True)

    def add(name: str, help_: str, func):
        p = sub.add_parser(name, help=help_, parents=[common])
        p.set_defaults(func=func)
        return p

    add("list", "直近のrun一覧", cmd_list).add_argument("branch", nargs="?")
    add("pr", "対象PRのHEADコミットに紐づくrun一覧", cmd_pr).add_argument("pr_number")
    add("view", "run詳細", cmd_view).add_argument("target", metavar="run_id|URL")
    add("failed", "失敗したstepのログのみ", cmd_failed).add_argument("target", metavar="run_id|URL")
    p_run = add("run", "ワークフロー手動実行", cmd_run)
    p_run.add_argument("workflow")
    p_run.add_argument("ref", nargs="?")
    add("watch", "完了まで追跡", cmd_watch).add_argument("target", metavar="run_id|URL")

    args = parser.parse_args()
    set_repo(args.repo)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(run_cli(main))
