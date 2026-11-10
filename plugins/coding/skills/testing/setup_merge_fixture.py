#!/usr/bin/env python3
"""merge-proposal スキル（merge_report.py）を手動検証するための
使い捨てgitリポジトリを、このディレクトリ配下の merge-fixture-repo/ に作り直す。

merge-fixture-repo/ はこのディレクトリの .gitignore で除外されているため、
リポジトリ本体のgit状態を汚さない。毎回削除してから作り直す。

使い方:
    python setup_merge_fixture.py

作られるシナリオ（feature ブランチをcheckoutした状態。main を feature に取り込む想定）:
    - calc.py: 両側で同じ行を変更 → content コンフリクト
    - config.txt: main で削除 / feature で変更 → modify/delete コンフリクト
    - api.py: main で関数名を変更(greet -> say_hello)。feature は別ファイル
      app.py で greet を新たに呼び出している → コンフリクトは無いが取り込み後に修正が必要
    - shared.txt: 両側で別の行を変更 → 自動マージされる両側変更
    - docs.md: main のみで変更 / pkg.lock: .diffignore 確認用

検証コマンド例（このディレクトリから実行）:
    python ../merge-proposal/merge_report.py main --repo merge-fixture-repo
"""

import shutil
import subprocess
from pathlib import Path

FIXTURE_DIRNAME = "merge-fixture-repo"


def run(cwd, args):
    result = subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    if result.returncode != 0:
        raise SystemExit(f"エラー: git {' '.join(args)} が失敗しました:\n{result.stderr.strip()}")
    return result


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def commit(repo, message):
    run(repo, ["add", "-A"])
    run(repo, ["commit", "-q", "-m", message])


def main():
    repo = Path(__file__).resolve().parent / FIXTURE_DIRNAME
    if repo.exists():
        shutil.rmtree(repo)
    repo.mkdir(parents=True)

    run(repo, ["init", "-q"])
    run(repo, ["config", "core.autocrlf", "false"])
    run(repo, ["config", "user.email", "fixture@example.com"])
    run(repo, ["config", "user.name", "fixture"])

    # --- ベース ---
    write(repo / "calc.py", "def add(a, b):\n    return a + b\n\n\nRATE = 1.0\n")
    write(repo / "config.txt", "timeout=10\n")
    write(repo / "api.py", "def greet(name):\n    return f'hi {name}'\n")
    write(repo / "shared.txt", "".join(f"line{i}\n" for i in range(1, 21)))
    write(repo / "docs.md", "# Docs\n")
    write(repo / "pkg.lock", "lock=1\n")
    commit(repo, "init")
    run(repo, ["branch", "-M", "main"])
    run(repo, ["branch", "feature"])

    # --- main 側の変更（取り込まれる側） ---
    write(repo / "calc.py", "def add(a, b):\n    return a + b\n\n\nRATE = 1.1  # main\n")
    (repo / "config.txt").unlink()
    write(repo / "api.py", "def say_hello(name):\n    return f'hello {name}'\n")
    commit(repo, "rename greet to say_hello, drop config.txt")
    shared = [f"line{i}\n" for i in range(1, 21)]
    shared[1] = "line2 changed on main\n"
    write(repo / "shared.txt", "".join(shared))
    write(repo / "docs.md", "# Docs\n\nsay_hello を使うこと。\n")
    write(repo / "pkg.lock", "lock=2\n")
    commit(repo, "update docs and shared")

    # --- feature 側の変更（取り込み先） ---
    run(repo, ["checkout", "-q", "feature"])
    write(repo / "calc.py", "def add(a, b):\n    return a + b\n\n\nRATE = 2.0  # feature\n")
    write(repo / "config.txt", "timeout=30\n")
    write(repo / "app.py", "from api import greet\n\nprint(greet('world'))\n")
    shared[1] = "line2\n"
    shared[18] = "line19 changed on feature\n"
    write(repo / "shared.txt", "".join(shared))
    commit(repo, "feature work")

    print(f"作成しました: {repo}")


if __name__ == "__main__":
    main()
