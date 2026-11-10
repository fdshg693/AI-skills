---
name: codex-skill-authoring
description: Use when creating, reviewing, or updating a skill for OpenAI Codex. Explain or implement Codex SKILL.md frontmatter, trigger descriptions, progressive disclosure, repository or plugin placement, optional UI metadata, testing, and distribution. Do not apply Claude-specific conventions unless the user explicitly asks for them.
meta:
  tag: []
  requires_repo_tools: none
  requires_env: none
  dependencies: none
  requires_install: none
  requires_hooks: none
  requires_skills: none
  status: stable
  description: no description
  version: 1.0.3
---

# Codexスキルの書き方

OpenAI Codex向けのスキルを設計・作成・レビューするためのガイド。Claude Codeなど別のAIコーディングツールの仕様を混ぜない。

## 1. まず利用形態を決める

- 1つのリポジトリや作業フォルダだけで使うなら、`$REPO_ROOT/.agents/skills/<skill-name>/SKILL.md` に置く。
- ユーザー全体で使うなら、`$HOME/.agents/skills/<skill-name>/SKILL.md` に置く。
- 複数人へ配布する、複数スキルをまとめる、MCPやコネクタも同梱するならプラグインにする。
- このリポジトリのプラグインへ追加する場合は、対象プラグインの `skills/<skill-name>/SKILL.md` に置く。例えば `codex-plugins/meta/skills/<skill-name>/SKILL.md`。

## 2. 最小構成を作る

スキルは、`SKILL.md` を必須とするディレクトリである。必要なときだけ `scripts/`、`references/`、`assets/`、`agents/openai.yaml` などを追加する。

```text
<skill-name>/
├── SKILL.md
├── agents/
│   └── openai.yaml       # UI表示や起動ポリシーが必要な場合だけ
├── scripts/              # 決定的な処理や外部ツールが必要な場合だけ
└── references/           # 本文に常時入れたくない資料がある場合だけ
```

`SKILL.md` のフロントマターには少なくとも `name` と `description` を含める。プラグインへ同梱するスキルの名前は、安定した小文字の kebab-case にする。

```md
---
name: example-skill
description: Use when reviewing API changes in this repository. Check compatibility, update tests, and report remaining risks.
---

# Example skill

Follow the workflow below and report the result in the requested format.
```

## 3. `description` で発動条件を明確にする

Codexは最初にスキルの名前、説明、パスを見て候補を選ぶ。フルの `SKILL.md` は選択後に読み込まれるため、`description` は暗黙起動の重要なインターフェースである。

- 冒頭に対象タスクとトリガー語を書く。
- 何をするスキルか、どの入力を扱うかを具体的に書く。
- 対象外や境界も短く書き、似たスキルとの競合を減らす。
- 長い背景説明、手順、例は本文や `references/` に置く。

明示的な起動は、CLI/IDEでは `$skill-name` のメンション、または `/skills` から行える。暗黙起動だけに依存せず、明示起動した場合にも成立する本文にする。

## 4. 本文は1つの仕事に集中させる

本文はCodexへの実行指示として、命令形で、入力・手順・出力を具体化する。

1. 前提、対象ファイル、入力を確認する。
2. 調査・変更の手順を順序立てて実行する。
3. 変更してよい範囲、禁止事項、承認が必要な操作を明記する。
4. テストや検証を実行する。
5. 変更ファイル、検証結果、未解決事項を決めた形式で報告する。

スキルは一つの焦点を持つ。再利用したい知識でも、毎回必ず必要でない長文や例は `references/` に分離する。スクリプトは外部ツールや決定的な変換が必要な場合だけ追加し、スクリプトの入力・出力・失敗時の扱いを本文から明示する。

## 5. `agents/openai.yaml` は必要な場合だけ使う

UI表示名、短い説明、既定プロンプト、暗黙起動ポリシー、MCP依存関係を定義する場合は `agents/openai.yaml` を追加する。

```yaml
interface:
  display_name: "Example Skill"
  short_description: "Review API changes consistently."
  default_prompt: "Use $example-skill to review this API change."

policy:
  allow_implicit_invocation: true
```

`allow_implicit_invocation: false` にすると暗黙起動を無効にできるが、明示的な `$skill-name` 起動は使える。ツール依存関係を宣言する場合は、実際に必要なMCPツールだけを記載する。

## 6. プラグインへ同梱する場合

プラグインのルートに `.codex-plugin/plugin.json` を置き、マニフェストからスキルディレクトリを相対パスで指定する。

```json
{
  "name": "example-plugin",
  "version": "1.0.0",
  "description": "Reusable Codex skills.",
  "skills": "./skills/"
}
```

マニフェストのパスは `./` で始め、プラグインルート内に留める。`.codex-plugin/` に置くのは `plugin.json` だけにし、`skills/`、`scripts/`、`assets/` などはプラグインルート直下に置く。共有・配布が目的でなければ、まずローカルのリポジトリスキルとして検証する。

## 7. 作成後に検証する

- フロントマターの `name` と `description` があり、スキル名・ディレクトリ名・メンション名が意図どおりか確認する。
- 典型的なプロンプトで暗黙起動されるか、対象外のプロンプトで誤起動されないか試す。
- `$skill-name` で明示起動し、本文だけ読んでも入力・変更範囲・出力が分かるか確認する。
- scriptsやreferencesへの相対パス、実行コマンド、失敗時の扱いを確認する。
- プラグインなら `.codex-plugin/plugin.json` のパスとバージョンを確認し、インストール先の新しいコピーで試す。
- Codexが変更を認識しない場合は再起動して再確認する。

## レビュー時のチェックリスト

- [ ] Codex向けの仕様であり、Claude固有のメタデータやディレクトリ規約を混ぜていない
- [ ] 1つの明確な仕事に絞っている
- [ ] `description` に発動条件・対象・境界がある
- [ ] 本文が命令形で、入力・手順・出力・検証を定義している
- [ ] 常時必要でない資料をreferencesへ分離している
- [ ] 破壊的操作、秘密情報、外部通信の扱いを必要に応じて明記している
- [ ] 実際のプロンプトで暗黙・明示起動をテストしている

参照した公式ドキュメント:

- https://developers.openai.com/codex/build-skills
- https://developers.openai.com/codex/skills-and-plugins
- https://developers.openai.com/codex/build-plugins
