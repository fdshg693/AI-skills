"""pr-check スキルの各スクリプトが共有するヘルパー。

pr-detail.py / pr-create.py / pr-actions.py の全てから import される。
gh/git コマンドの実行と JSON パースのみを扱う。
"""

from __future__ import annotations

import json
import subprocess
import sys


class PrCheckError(RuntimeError):
    pass


def run(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if check and result.returncode != 0:
        raise PrCheckError(f"{' '.join(cmd)} failed:\n{result.stderr.strip()}")
    return result


def run_json(cmd: list[str]):
    return json.loads(run(cmd).stdout)


def current_branch() -> str:
    return run(["git", "branch", "--show-current"]).stdout.strip()


def repo_name_with_owner() -> str:
    return run_json(["gh", "repo", "view", "--json", "nameWithOwner"])["nameWithOwner"]


def default_branch() -> str:
    return run_json(["gh", "repo", "view", "--json", "defaultBranchRef"])["defaultBranchRef"][
        "name"
    ]


def run_cli(main) -> int:
    """main() を実行し、PrCheckError を error: 付きでstderrに出す共通エントリポイント。"""
    try:
        return main() or 0
    except PrCheckError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
