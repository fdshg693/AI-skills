#!/usr/bin/env python3
"""review スキル（diff_report.py / uncommitted_report.py）を手動検証するための
使い捨てgitリポジトリを、このディレクトリ配下の fixture-repo/ に作り直す。

fixture-repo/ はこのディレクトリの .gitignore で除外されているため、
リポジトリ本体のgit状態を汚さない。毎回削除してから作り直すので、
何度実行しても同じ状態から始められる。

使い方:
    python setup_fixture.py            # 標準シナリオのみ
    python setup_fixture.py --bulk 40  # 40件の未追跡ファイルを追加し、分割/INDEX.md生成も試せるようにする

作られるシナリオ:
    - ブランチ間差分用: main ブランチと feature ブランチ
      （feature.txt 追加 / a.txt 変更 が feature 側のみに存在）
    - 未コミット変更用（feature ブランチをcheckoutした状態）:
      staged変更(b.txt) / unstaged変更(a.txt) / 未追跡ファイル(untracked.txt) /
      削除(keep.txt) / バイナリファイル(bin.dat) / .diffignore対象になりうるファイル(pkg.lock)

検証コマンド例（このディレクトリから実行）:
    python ../skills/review/diff_report.py main --repo fixture-repo
    python ../skills/review/uncommitted_report.py --repo fixture-repo
"""

import argparse
import shutil
import subprocess
from pathlib import Path

FIXTURE_DIRNAME = "fixture-repo"


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


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--bulk",
        type=int,
        default=0,
        help="分割/INDEX.md生成を試すための未追跡ファイルを追加する数",
    )
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    fixture_dir = script_dir / FIXTURE_DIRNAME

    if fixture_dir.exists():
        shutil.rmtree(fixture_dir)
    fixture_dir.mkdir(parents=True)

    run(fixture_dir, ["init", "-q"])
    run(fixture_dir, ["config", "user.email", "fixture@example.com"])
    run(fixture_dir, ["config", "user.name", "fixture"])

    # --- ベースコミット（main の元になる） ---
    write(fixture_dir / "a.txt", "line1\nline2\nline3\n")
    write(fixture_dir / "b.txt", "unchanged\n")
    write(fixture_dir / "keep.txt", "keep me\n")
    run(fixture_dir, ["add", "-A"])
    run(fixture_dir, ["commit", "-q", "-m", "init"])
    run(fixture_dir, ["branch", "main"])

    # --- feature ブランチ（ブランチ間差分レビュー用） ---
    run(fixture_dir, ["checkout", "-q", "-b", "feature"])
    write(fixture_dir / "a.txt", "line1\nline2 modified on feature\nline3\n")
    write(fixture_dir / "feature.txt", "new file added on feature branch\n")
    run(fixture_dir, ["add", "-A"])
    run(fixture_dir, ["commit", "-q", "-m", "feature work"])

    # --- feature ブランチ上の未コミット変更（未コミット変更レビュー用） ---
    write(fixture_dir / "b.txt", "unchanged\nstaged addition\n")
    run(fixture_dir, ["add", "b.txt"])  # staged

    write(
        fixture_dir / "a.txt", "line1\nline2 modified on feature\nline3\nunstaged addition\n"
    )  # unstaged

    (fixture_dir / "keep.txt").unlink()  # unstaged deletion

    write(fixture_dir / "untracked.txt", "brand new untracked file\n")  # untracked
    (fixture_dir / "bin.dat").write_bytes(b"\x00\x01\x02binary\xff")  # untracked binary
    write(fixture_dir / "pkg.lock", "lockfile-like content\n")  # untracked, .diffignoreの動作確認用

    if args.bulk > 0:
        for i in range(1, args.bulk + 1):
            write(
                fixture_dir / f"bulk_{i:02d}.txt", "\n".join(f"line {j}" for j in range(20)) + "\n"
            )

    print(f"fixture-repo を作成しました: {fixture_dir}")
    print("現在のブランチ: feature（main が分岐元）")
    print()
    print("検証コマンド例:")
    print(
        f"  python {script_dir.parent / 'skills' / 'review' / 'diff_report.py'} main --repo {fixture_dir}"
    )
    print(
        f"  python {script_dir.parent / 'skills' / 'review' / 'uncommitted_report.py'} --repo {fixture_dir}"
    )


if __name__ == "__main__":
    main()
