#!/usr/bin/env python3
"""PR番号を引数に取り、詳細・レビューコメント・レビューを取得する。

使い方: python pr-detail.py <PR番号> [section...]
  section省略時: 3つ全て取得
  section: view | comments | reviews | all （複数指定可・スペース区切り）
  例: python pr-detail.py 42 view comments
      python pr-detail.py 42 all
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pr_common import run, run_json, repo_name_with_owner, run_cli

SECTIONS = ("view", "comments", "reviews")


def print_view(pr_number: str) -> None:
    print(f"### PR #{pr_number} 詳細")
    result = run(
        [
            "gh",
            "pr",
            "view",
            pr_number,
            "--json",
            "number,title,body,state,mergeable,mergeStateStatus,reviewDecision,url,baseRefName,headRefName",
        ]
    )
    print(result.stdout.rstrip("\n"))


def print_comments(pr_number: str, repo: str) -> None:
    print(f"### PR #{pr_number} レビューコメント（コード行への指摘）")
    comments = run_json(["gh", "api", f"repos/{repo}/pulls/{pr_number}/comments"])
    if not comments:
        print("レビューコメントはありません")
        return
    for c in comments:
        line = c.get("line") or c.get("original_line") or "N/A"
        print(f"[{c['user']['login']}] {c['path']}:{line}")
        print(f"  {c['body']}\n")


def print_reviews(pr_number: str) -> None:
    print(f"### PR #{pr_number} レビュー（承認/変更リクエスト）")
    reviews = run_json(["gh", "pr", "view", pr_number, "--json", "reviews"])["reviews"]
    reviews = [r for r in reviews if r.get("body") or r.get("state") != "COMMENTED"]
    if not reviews:
        print("レビューはありません")
        return
    for r in reviews:
        author = (r.get("author") or {}).get("login", "unknown")
        print(f"[{author}] {r['state']}")
        print(f"  {r.get('body') or '(コメントなし)'}\n")


def parse_sections(raw: list[str]) -> list[str]:
    if not raw or "all" in raw:
        return list(SECTIONS)
    seen: list[str] = []
    for s in raw:
        if s not in SECTIONS:
            print(f"Unknown section: {s} (expected: view|comments|reviews|all)", file=sys.stderr)
            raise SystemExit(1)
        if s not in seen:
            seen.append(s)
    return seen


def main() -> int:
    parser = argparse.ArgumentParser(prog="pr-detail.py")
    parser.add_argument("pr_number")
    parser.add_argument("sections", nargs="*", metavar="section")
    args = parser.parse_args()

    repo = repo_name_with_owner()
    sections = parse_sections(args.sections)
    for i, section in enumerate(sections):
        if i > 0:
            print()
        if section == "view":
            print_view(args.pr_number)
        elif section == "comments":
            print_comments(args.pr_number, repo)
        elif section == "reviews":
            print_reviews(args.pr_number)
    return 0


if __name__ == "__main__":
    raise SystemExit(run_cli(main))
