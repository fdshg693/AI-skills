#!/usr/bin/env python3
"""../list-skills.py のユニットテスト。

実行方法（リポジトリルートから）:
    python -m unittest discover -s skills/plugins/special/skills/skill-group/tests -v

このディレクトリ内から直接実行する場合:
    python test_list_skills.py

sub_skills.yaml / SKILL.md はテストごとに tempfile.TemporaryDirectory() 配下に
一時生成し、list_skills.SCRIPT_DIR / GROUPS_YAML をそこに向けて実行する。
リポジトリ本体の sub_skills.yaml やスキルフォルダには一切触れない。
"""

import contextlib
import importlib.util
import io
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parent.parent / "list-skills.py"


def _load_module():
    # ファイル名にハイフンを含むため import 文では読めず、importlib で明示ロードする。
    spec = importlib.util.spec_from_file_location("list_skills_under_test", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


list_skills = _load_module()


def write_skill(skill_dir: Path, name: str, description: str = "") -> Path:
    """テスト用 SKILL.md を作成して返す。"""
    skill_dir.mkdir(parents=True, exist_ok=True)
    skill_md = skill_dir / "SKILL.md"
    skill_md.write_text(
        f"---\nname: {name}\ndescription: {description}\n---\n\nbody\n",
        encoding="utf-8",
    )
    return skill_md


def write_groups_yaml(root: Path, entries) -> None:
    """テスト用 sub_skills.yaml を作成する。entries は dict のリスト（name/description/path）。"""
    lines = []
    for entry in entries:
        lines.append(f"- name: {entry['name']}")
        lines.append(f"  description: {entry.get('description', '')}")
        lines.append(f"  path: {entry['path']}")
    (root / "sub_skills.yaml").write_text("\n".join(lines) + "\n", encoding="utf-8")


class ListSkillsTestCase(unittest.TestCase):
    """list_skills.SCRIPT_DIR / GROUPS_YAML を一時ディレクトリに差し替える基底クラス。"""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.root = Path(self._tmpdir.name)
        self._orig_script_dir = list_skills.SCRIPT_DIR
        self._orig_groups_yaml = list_skills.GROUPS_YAML
        list_skills.SCRIPT_DIR = self.root
        list_skills.GROUPS_YAML = self.root / "sub_skills.yaml"

    def tearDown(self):
        list_skills.SCRIPT_DIR = self._orig_script_dir
        list_skills.GROUPS_YAML = self._orig_groups_yaml
        self._tmpdir.cleanup()

    @staticmethod
    def _capture(func, *args, **kwargs):
        """func 実行中の stdout/stderr を捕捉し、(戻り値, stdout, stderr) を返す。"""
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            result = func(*args, **kwargs)
        return result, out.getvalue(), err.getvalue()


class ParseFrontmatterTest(ListSkillsTestCase):
    def test_parses_simple_fields(self):
        skill = write_skill(self.root / "s1", "my-skill", "desc here")
        fm = list_skills.parse_frontmatter(skill)
        self.assertEqual(fm["name"], "my-skill")
        self.assertEqual(fm["description"], "desc here")

    def test_missing_frontmatter_returns_empty(self):
        f = self.root / "no-front.md"
        f.write_text("just text\n", encoding="utf-8")
        self.assertEqual(list_skills.parse_frontmatter(f), {})


class LoadGroupsTest(ListSkillsTestCase):
    def test_ignores_comments_and_blank_lines(self):
        (self.root / "sub_skills.yaml").write_text(
            "# comment\n\n- name: g1\n  description: d1\n  path: ./p1\n",
            encoding="utf-8",
        )
        groups = list_skills.load_groups()
        self.assertEqual(groups, [{"name": "g1", "description": "d1", "path": "./p1"}])

    def test_missing_file_returns_empty_list(self):
        self.assertEqual(list_skills.load_groups(), [])


class FindGroupsTest(ListSkillsTestCase):
    def test_returns_all_entries_with_same_name(self):
        write_groups_yaml(
            self.root,
            [
                {"name": "g", "path": "./p1"},
                {"name": "g", "path": "./p2"},
                {"name": "other", "path": "./p3"},
            ],
        )
        groups = list_skills.find_groups("g")
        self.assertEqual([g["path"] for g in groups], ["./p1", "./p2"])

    def test_returns_empty_for_unknown_name(self):
        write_groups_yaml(self.root, [{"name": "g", "path": "./p1"}])
        self.assertEqual(list_skills.find_groups("nope"), [])


class CmdGroupsTest(ListSkillsTestCase):
    def test_dedupes_repeated_group_names(self):
        write_groups_yaml(
            self.root,
            [
                {"name": "default", "path": "./p1"},
                {"name": "default", "path": "./p2"},
                {"name": "other", "path": "./p3"},
            ],
        )
        _, out, _ = self._capture(list_skills.cmd_groups)
        self.assertEqual(out.splitlines(), ["default", "other"])


class CmdListTest(ListSkillsTestCase):
    def test_merges_multiple_paths_for_same_group(self):
        write_skill(self.root / "p1" / "skill-a", "skill-a")
        write_skill(self.root / "p2" / "skill-b", "skill-b")
        write_groups_yaml(
            self.root,
            [
                {"name": "grp", "path": "./p1"},
                {"name": "grp", "path": "./p2"},
            ],
        )
        _, out, _ = self._capture(list_skills.cmd_list, "grp")
        self.assertEqual(sorted(out.splitlines()), ["skill-a", "skill-b"])

    def test_same_path_registered_twice_not_duplicated(self):
        write_skill(self.root / "p1" / "skill-a", "skill-a")
        write_groups_yaml(
            self.root,
            [
                {"name": "grp", "path": "./p1"},
                {"name": "grp", "path": "./p1"},
            ],
        )
        _, out, _ = self._capture(list_skills.cmd_list, "grp")
        self.assertEqual(out.splitlines(), ["skill-a"])

    def test_unknown_group_warns_on_stderr(self):
        write_groups_yaml(self.root, [{"name": "grp", "path": "./p1"}])
        _, out, err = self._capture(list_skills.cmd_list, "nope")
        self.assertEqual(out, "")
        self.assertIn("WARNING", err)
        self.assertIn("nope", err)


class CmdShowTest(ListSkillsTestCase):
    def test_finds_skill_across_groups(self):
        write_skill(self.root / "p1" / "skill-a", "skill-a", "hello")
        write_groups_yaml(self.root, [{"name": "grp", "path": "./p1"}])
        _, out, _ = self._capture(list_skills.cmd_show, "skill-a")
        self.assertIn("## skill-a", out)
        self.assertIn("- description: hello", out)
        self.assertIn(str(self.root / "p1" / "skill-a" / "SKILL.md"), out)

    def test_missing_skill_warns_on_stderr(self):
        write_groups_yaml(self.root, [{"name": "grp", "path": "./p1"}])
        _, out, err = self._capture(list_skills.cmd_show, "nope")
        self.assertEqual(out, "")
        self.assertIn("WARNING", err)


class CmdCheckUniqueTest(ListSkillsTestCase):
    def test_unique_names_pass(self):
        write_skill(self.root / "p1" / "a", "skill-a")
        write_skill(self.root / "p1" / "b", "skill-b")
        write_groups_yaml(self.root, [{"name": "grp", "path": "./p1"}])
        result, out, _ = self._capture(list_skills.cmd_check_unique)
        self.assertTrue(result)
        self.assertIn("OK", out)

    def test_duplicate_names_across_different_files_fail(self):
        write_skill(self.root / "p1" / "a", "dup-name")
        write_skill(self.root / "p2" / "b", "dup-name")
        write_groups_yaml(
            self.root,
            [
                {"name": "grp1", "path": "./p1"},
                {"name": "grp2", "path": "./p2"},
            ],
        )
        result, _, err = self._capture(list_skills.cmd_check_unique)
        self.assertFalse(result)
        self.assertIn("DUPLICATE", err)
        self.assertIn("dup-name", err)

    def test_same_file_referenced_twice_is_not_a_duplicate(self):
        write_skill(self.root / "p1" / "a", "skill-a")
        write_groups_yaml(
            self.root,
            [
                {"name": "grp", "path": "./p1"},
                {"name": "grp", "path": "./p1"},
            ],
        )
        result, out, _ = self._capture(list_skills.cmd_check_unique)
        self.assertTrue(result)
        self.assertIn("OK", out)


if __name__ == "__main__":
    unittest.main()
