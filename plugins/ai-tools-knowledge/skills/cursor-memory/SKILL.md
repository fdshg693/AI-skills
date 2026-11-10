---
# 同梱ファイル: memory.md（配置判断・書き方の詳細）/ references/（公式ドキュメント原文スナップショット）
name: cursor-memory
description: >-
  Guides placement and authoring of Cursor persistent Agent guidance — project
  rules (.cursor/rules/*.mdc), AGENTS.md, CLAUDE.md, User Rules, and Team Rules.
  Use when deciding what belongs in each mechanism, writing or editing rule
  files, configuring alwaysApply/globs/description, setting up nested AGENTS.md,
  migrating from .cursorrules, or troubleshooting why a rule is not applied.
  Not for Agent Skills (use cursor-skill-use) or general Cursor features (use
  cursor-docs).
meta:
  tag: []
  requires_repo_tools: none
  requires_env: none
  dependencies: none
  requires_install: none
  requires_hooks: none
  requires_skills: cursor-skill-use, cursor-docs, claude-code-memory
  status: stable
  description: no description
  version: 1.0.3
---

# Cursorのメモリ設計（Rules / AGENTS.md）

Project Rules・`AGENTS.md`/`CLAUDE.md`・User Rules・Team Rulesのうち**どれに何を書くか**を判断し、実際に配置するためのスキル。各機構の詳細（frontmatter対応表・優先順位・ネスト挙動・FAQ）は同梱の [memory.md](memory.md) を参照。

Cursorでは LLM が補完間で記憶を持たないため、Rules / `AGENTS.md` が「永続コンテキスト」としてプロンプト先頭に注入される。強制力のある設定ではない（Agentが従わない可能性がある）。強制したい処理は **Hooks** を検討する。

このスキルの内容は 2026-07-20 時点の公式ドキュメント（https://cursor.com/docs/rules.md 他）に基づく。原文スナップショットは [references/](references/) に同梱している。

## 判断手順

1. **誰向け・どのスコープか決める**
   - チーム共有・Git管理したい → Project Rules（`.cursor/rules/*.mdc`）またはルート/`AGENTS.md`
   - 自分の全プロジェクト共通の好み（文体など） → **User Rules**（Customize → Rules。ファイルシステム上のプロジェクト配下には置かない）
   - 組織全体で強制したい → **Team Rules**（ダッシュボード。Team/Enterprise。ユーザーがファイルを手書きする対象ではない）
2. **シンプルな指示か、適用条件が要るか決める**
   - 常時適用の短い指示で十分 → ルートの `AGENTS.md`（または互換の `CLAUDE.md`）
   - パス限定・Agent判断・手動 `@` 言及が要る → `.cursor/rules/<name>.mdc`（拡張子は必ず `.mdc`。`.md` は rules として無視される）
3. **`.mdc` の適用タイプを決める**（frontmatter の組み合わせ）

   | 欲しい挙動                                 | `alwaysApply` | `description` | `globs`  |
   | ------------------------------------------ | ------------- | ------------- | -------- |
   | 毎チャットに含める                         | `true`        | （無視）      | （無視） |
   | マッチするファイルがコンテキストにあるとき | `false`       | —             | 指定     |
   | Agentが description を見て関連時に取る     | `false`       | 指定          | 省略     |
   | `@rule-name` したときだけ                  | `false`       | 省略          | 省略     |

4. **ディレクトリ単位の指示が要るか**
   - サブツリー固有の指示 → その配下にネストした `AGENTS.md`（親と結合され、より具体的な方が優先）
   - ファイル種別・glob で絞りたい → `.mdc` の `globs`（ネスト `AGENTS.md` では不可）
5. **書く**
   - 500行未満・1関心1ファイル。曖昧な指示を避け、検証可能な粒度（具体コマンド・数値・禁止パス）で書く
   - 長いコードやスタイルガイド全文は貼らず、`@path/to/file` で参照する
   - 同じミスが繰り返されたらルールを足す。先回りで過剰に書かない
6. **スキルにすべき内容は切り出す**
   - 手順・スクリプト・オンデマンド知識 → **Skills**（`cursor-skill-use`）。`alwaysApply: false` かつ `globs` なしの「Apply Intelligently」ルールは `/migrate-to-skills` の移行候補

## チェックリスト

- [ ] Cursor向けであり、Claude Codeの `.claude/rules`（`paths` frontmatter）や Codex 固有の仕組みと混同していない
- [ ] Project Rules は `.cursor/rules/**/*.mdc`（`.md` ではない）
- [ ] `alwaysApply` / `description` / `globs` の組み合わせが意図した適用タイプと一致している
- [ ] `Apply Intelligently` なら `description` がある。`Apply to Specific Files` なら `globs` が実ファイルにマッチする
- [ ] `AGENTS.md` / `CLAUDE.md` は常時適用前提（条件付きなら `.mdc` へ）
- [ ] ルールは Agent（Chat）向け。Tab / Inline Edit（Ctrl+K）には効かないことを説明済み
- [ ] レガシー `.cursorrules` が残っていれば Always Apply の `.mdc` へ移行を提案

## 困ったときは

1. まず同梱の [memory.md](memory.md) を確認する
2. 一次情報の原文が必要なら [references/rules.md](references/rules.md)・[references/help-rules.md](references/help-rules.md)
3. 仕様が変わっている可能性がある、またはルール以外の Cursor 機能が絡む場合は **cursor-docsスキル**（このスキルはスナップショットベースで陳腐化しうる）
4. Skills の作成・移行は **cursor-skill-useスキル**。Claude Code の `CLAUDE.md` / `.claude/rules` 設計は **claude-code-memoryスキル**（別ツール。混同しない）
