#!/usr/bin/env python3
"""skill-group のスキルグループ/スキル一覧/詳細を出力するスクリプト

使い方:
  list-skills.py                          # グループ名一覧を改行区切りで出力
  list-skills.py groups                   # 同上
  list-skills.py list <group>             # 指定グループ配下のスキル名一覧を改行区切りで出力
  list-skills.py show <name> [<name>...]  # 指定スキル（全グループ横断）の 名前/説明/SKILL.mdパス を出力
                                           # 存在しない名前は stderr に警告
  list-skills.py check-unique             # メンテナンス用: 全グループ横断でスキル名の重複を検査
                                           # （重複があれば stderr に一覧を出し、終了コード1）

グループ定義は同階層の sub_skills.yaml (name/description/path のフラットなリスト) から読み込む。
同じ name を持つエントリを複数書くと、それらの path がまとめて1つのグループとして扱われる。
"""

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
GROUPS_YAML = SCRIPT_DIR / "sub_skills.yaml"


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


def _unquote(value: str) -> str:
    return value.strip().strip('"').strip("'")


def load_groups():
    """sub_skills.yaml から `- name / description / path` のフラットなリストのみを読み取る簡易パーサー。

    本スキルが必要とする単純なスキーマ（ネストなしのリスト）だけをサポートし、
    PyYAML 等の追加パッケージには依存しない。
    """
    if not GROUPS_YAML.exists():
        return []
    groups = []
    current = None
    for raw_line in GROUPS_YAML.read_text(encoding="utf-8").splitlines():
        line = raw_line.split(" #", 1)[0].rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("- "):
            current = {}
            groups.append(current)
            stripped = stripped[2:].strip()
            if not stripped:
                continue
        if current is None or ":" not in stripped:
            continue
        key, _, value = stripped.partition(":")
        current[key.strip()] = _unquote(value)
    return groups


def find_groups(name: str):
    """同じ name を持つ全エントリを返す（複数 path を1グループ名に束ねるため）。"""
    return [group for group in load_groups() if group.get("name") == name]


def group_skill_dir(group: dict) -> Path:
    return (SCRIPT_DIR / group.get("path", "")).resolve()


def find_skill_files_in(base_dir: Path):
    if not base_dir.is_dir():
        return []
    return sorted(base_dir.glob("**/SKILL.md"))


def cmd_groups():
    seen = set()
    for group in load_groups():
        name = group.get("name", "")
        if name and name not in seen:
            seen.add(name)
            print(name)


def cmd_list(group_name: str):
    groups = find_groups(group_name)
    if not groups:
        print(f"WARNING: group '{group_name}' not found in {GROUPS_YAML}", file=sys.stderr)
        return
    files = []
    for group in groups:
        files.extend(find_skill_files_in(group_skill_dir(group)))
    for f in sorted(set(files)):
        name = parse_frontmatter(f).get("name", "")
        print(name)


def cmd_show(target: str):
    for group in load_groups():
        for f in find_skill_files_in(group_skill_dir(group)):
            fm = parse_frontmatter(f)
            if fm.get("name") == target:
                print(f"## {fm.get('name', '')}")
                print(f"- description: {fm.get('description', '')}")
                print(f"- path: {f}")
                print()
                return
    print(f"WARNING: skill '{target}' not found in any group", file=sys.stderr)


def cmd_check_unique() -> bool:
    """全グループ横断でスキル名（フロントマターの name）が重複していないかチェックする（メンテナンス用）。"""
    name_to_paths = {}
    for group in load_groups():
        for f in find_skill_files_in(group_skill_dir(group)):
            name = parse_frontmatter(f).get("name", "")
            if not name:
                continue
            name_to_paths.setdefault(name, set()).add(f)

    duplicates = {name: paths for name, paths in name_to_paths.items() if len(paths) > 1}
    if not duplicates:
        print("OK: all skill names are unique")
        return True

    for name in sorted(duplicates):
        print(f"DUPLICATE: '{name}' found in:", file=sys.stderr)
        for f in sorted(duplicates[name]):
            print(f"  - {f}", file=sys.stderr)
    return False


def main() -> None:
    args = sys.argv[1:]
    if not args or (len(args) == 1 and args[0] == "groups"):
        cmd_groups()
        return

    sub, rest = args[0], args[1:]
    if sub == "list":
        if len(rest) != 1:
            print("USAGE: list-skills.py list <group>", file=sys.stderr)
            sys.exit(1)
        cmd_list(rest[0])
    elif sub == "show":
        if not rest:
            print("USAGE: list-skills.py show <name> [<name>...]", file=sys.stderr)
            sys.exit(1)
        for name in rest:
            cmd_show(name)
    elif sub == "check-unique":
        if rest:
            print("USAGE: list-skills.py check-unique", file=sys.stderr)
            sys.exit(1)
        if not cmd_check_unique():
            sys.exit(1)
    else:
        print(
            "USAGE: list-skills.py [groups | list <group> | show <name> [<name>...] | check-unique]",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
