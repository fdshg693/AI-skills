"""gh-pr スキルの各スクリプトが共有するヘルパー。

pr-detail.py / pr-create.py / pr-actions.py の全てから import される。
gh/git コマンドの実行と JSON パース、対象リポジトリの切り替え（-R / URL）を扱う。
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys

# set_repo() で明示されたリポジトリ（OWNER/REPO）。None ならカレントディレクトリの git remote から gh が決める。
_REPO: str | None = None

_RUN_URL = re.compile(
    r"github\.com/(?P<repo>[^/\s]+/[^/\s]+)/actions/runs/(?P<run>\d+)"
    r"(?:/attempts/\d+)?(?:/job/(?P<job>\d+))?"
)


class PrCheckError(RuntimeError):
    pass


def set_repo(repo: str | None) -> None:
    """以降の gh 呼び出しの対象リポジトリを OWNER/REPO に固定する。

    gh の多くのサブコマンドと `gh api` の {owner}/{repo} は環境変数 GH_REPO に従う。
    `gh repo view` だけは GH_REPO を見ないので、repo_name_with_owner() / default_branch() で個別に扱う。
    """
    global _REPO
    if not repo:
        return
    _REPO = repo
    os.environ["GH_REPO"] = repo


def parse_run_target(target: str) -> tuple[str, str | None]:
    """run id または Actions の URL を (run_id, job_id) にする。

    URL ならそのリポジトリを set_repo() する。job URL のときだけ job_id を返す。
    """
    m = _RUN_URL.search(target)
    if m:
        set_repo(m.group("repo"))
        return m.group("run"), m.group("job")
    if target.isdigit():
        return target, None
    raise PrCheckError(f"run id または Actions の run/job URL を指定してください: {target}")


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


def stream(cmd: list[str]) -> int:
    """出力をそのまま流す gh コマンドを実行する。先に print した見出しが後ろに回らないよう flush してから起動する。"""
    sys.stdout.flush()
    return subprocess.run(cmd).returncode


def current_branch() -> str:
    return run(["git", "branch", "--show-current"]).stdout.strip()


def repo_name_with_owner() -> str:
    if _REPO:
        return _REPO
    return run_json(["gh", "repo", "view", "--json", "nameWithOwner"])["nameWithOwner"]


def default_branch() -> str:
    cmd = ["gh", "repo", "view", *([_REPO] if _REPO else []), "--json", "defaultBranchRef"]
    return run_json(cmd)["defaultBranchRef"]["name"]


def run_cli(main) -> int:
    """main() を実行し、PrCheckError を error: 付きでstderrに出す共通エントリポイント。"""
    try:
        return main() or 0
    except PrCheckError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
