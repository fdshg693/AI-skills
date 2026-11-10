---
name: skill-group
description: 様々なスキルをグループ化したスキル
disable-model-invocation: false
user-invocable: true
meta:
  tag: []
  requires_repo_tools: none
  requires_env: python
  dependencies: none
  requires_install: none
  requires_hooks: none
  requires_skills: none
  status: stable
  description: no description
  version: 1.0.0
---

`${CLAUDE_SKILL_DIR}/sub_skills.yaml` に定義された複数のスキルグループ（フォルダ）配下のサブスキルを確認するスキルです。

## 利用可能なスキルグループ一覧

!`python ${CLAUDE_SKILL_DIR}/list-skills.py`

### スクリプトの引数仕様

```bash
python ${CLAUDE_SKILL_DIR}/list-skills.py                          # グループ名一覧を出力（groups と同じ）
python ${CLAUDE_SKILL_DIR}/list-skills.py list <group>              # 指定グループ配下のスキル名一覧を出力
python ${CLAUDE_SKILL_DIR}/list-skills.py show <name> [<name>...]   # 指定スキルの 名前/説明/SKILL.mdパス を出力
```

3段階の情報開示になっている:

1. 引数なし（または `groups`）: `sub_skills.yaml` に定義された各グループの `name` を改行区切りで出力
2. `list <group>`: 指定グループの `path` 配下を再帰探索し、各 `SKILL.md` のフロントマター `name` を改行区切りで出力
3. `show <name> [<name>...]`: 全グループを横断して該当スキルを探し、以下を Markdown 形式で出力
   - `## <name>`
   - `- description: <フロントマターのdescription>`
   - `- path: <SKILL.mdの絶対パス>`

スキル名は全グループを通じて重複しない想定のため、`show` にはグループ名の指定は不要。

## サブスキルの利用

- 利用したいサブスキルが見つかった場合は直接SKILLのファイルを読み込み、内容を確認して利用することが可能
  - スキルとしての呼び出しはできないことに注意してください
