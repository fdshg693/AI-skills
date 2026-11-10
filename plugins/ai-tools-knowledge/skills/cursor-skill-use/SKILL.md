---
# 同梱ファイル: using.md（スキルを使う側: 呼び出し・組み込み・管理・インストール・移行）/ authoring.md（スキルを作る側: 配置・記述・スコーピング・配布）/ reference.md（スキル機構の詳細リファレンス）/ references/（公式ドキュメント原文スナップショット）
name: cursor-skill-use
description: Use when using, creating, or managing Agent Skills in Cursor (the AI code editor) — invoking skills, placing and writing SKILL.md, frontmatter fields (name/description/paths/disable-model-invocation/metadata), skill discovery locations, scoping skills to files, built-in skills, installing from GitHub, migrating rules or slash commands to skills, and bundling skills into plugins. Not for Cursor CLI flags (use cursor-cli-docs) or general Cursor features (use cursor-docs).
meta:
  tag: []
  requires_repo_tools: none
  requires_env: none
  dependencies: none
  requires_install: none
  requires_hooks: none
  requires_skills: none
  status: experimental
  description: no description
  version: 1.0.3
---

# Cursorでのスキルの使い方

Cursor（AIコードエディタ）で Agent Skills を**使う・作る・管理する**ためのエントリポイント。目的に応じて参照先を切り替える。

Cursorのスキルは [Agent Skills](https://agentskills.io) オープン標準に準拠した、「`SKILL.md` を持つディレクトリ」。Claude Code など他ツール固有のスキル仕様（`allowed-tools` フィールド、`` !`command` `` による動的コンテキスト注入、`${CLAUDE_SKILL_DIR}` などの置換変数）を混ぜて書かないこと。

このスキルの内容は 2026-07-20 時点の公式ドキュメント（https://cursor.com/docs/skills.md 他）に基づく。原文スナップショットは [references/](references/) に同梱している。

## 手順

1. **スキルを使う** — 呼び出し方（自動/手動）、組み込みスキル一覧、Customize画面での確認・管理、GitHubからのインストール、ルール/コマンドからの移行 → [using.md](using.md)
2. **スキルを作る・配布する** — 配置場所の決定、`SKILL.md` の書き方、スコーピング、発動制御、スクリプト同梱、プラグインとしての配布 → [authoring.md](authoring.md)
3. **機構の詳細仕様** — 発見場所の一覧、フロントマター全フィールド、ネスト/モノレポ時の挙動 → [reference.md](reference.md)
4. **一次情報の原文**が必要なら [references/skills.md](references/skills.md)（スキル本体）・[references/plugins.md](references/plugins.md)（プラグイン配布）

## 困ったときは

- スキル以外のCursor機能、またはスキル仕様の**最新**の公式情報が必要な場合は **cursor-docsスキル**（このスキルはスナップショットベースで陳腐化しうる）
- Cursor CLI（`agent` コマンド）のフラグ・サブコマンドは **cursor-cli-docsスキル**、CLIへのタスク委譲は **cursor-cli-useスキル**
- Claude Code用スキルの作成・評価は **writing-skillスキル**、Codex用は **codex-skill-authoringスキル**。ツールごとにスキル仕様が異なるため混同しない
