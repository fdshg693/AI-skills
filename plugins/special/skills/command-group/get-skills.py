#!/usr/bin/env python3
"""command-group のサブスキル内容を結合出力するスクリプト

使い方:
  get-skills.py <name> [<name>...]     # 指定スキルのSKILL.md内容をパス付きで連結出力
                                        # 存在しない名前は stderr に警告してスキップ
"""

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SKILLS_DIR = SCRIPT_DIR / "sub_commands"


def parse_frontmatter(path: Path) -> dict:
    """SKILL.md 先頭の YAML フロントマターから単純な `key: value` 行を読み取る。"""
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    fields = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip().strip('"').strip("'")
    return fields


def find_skill_files():
    return sorted(SKILLS_DIR.glob("**/SKILL.md"))


def emit_skill(target: str) -> None:
    for f in find_skill_files():
        name = parse_frontmatter(f).get("name", "")
        if name == target:
            print(f"## スキル: {name}")
            print()
            print(f"- path: {f}")
            print()
            print("### SKILL.md 内容")
            print()
            print("```markdown")
            print(f.read_text(encoding="utf-8"), end="")
            print("```")
            print()
            return
    print(f"WARNING: skill '{target}' not found under {SKILLS_DIR}", file=sys.stderr)


def main() -> None:
    args = sys.argv[1:]
    if not args:
        print(f"usage: {Path(sys.argv[0]).name} <skill_name> [<skill_name>...]", file=sys.stderr)
        sys.exit(1)
    for arg in args:
        emit_skill(arg)


if __name__ == "__main__":
    main()
