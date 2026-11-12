---
# 同梱の memory.md は詳細な参照資料。このファイルは配置判断と実作業の入口を担う。
name: claude-code-memory
description: Guides placement of project knowledge in Claude Code, including CLAUDE.md, `.claude/rules/*.md`, and auto memory. Use when deciding what belongs in each mechanism, editing its configuration, or troubleshooting memory behavior.
meta:
  tag: []
  requires_repo_tools: none
  requires_env: none
  dependencies: none
  requires_install: none
  requires_hooks: none
  requires_skills: claude-code-docs, writing-rules, writing-hooks, claude-settings
  status: stable
  description: no description
  version: 1.0.2
---

# Claude Codeのメモリ設計

CLAUDE.md・`.claude/rules/*.md`・auto memoryの3つのうち**どれに何を書くか**を判断し、実際に配置するためのスキル。各機構の詳細（frontmatter仕様・スコープ表・保存場所など）は同梱の [memory.md](memory.md) を参照。

## 判断手順

1. **誰が書く内容か決める**
   - 人間が明示的に指示したい内容（規約・ワークフロー・アーキテクチャ） → `CLAUDE.md` か `.claude/rules/`
   - Claudeが会話中に気付いた知見（ビルドコマンド・デバッグ手法・好み） → 手を出さずauto memoryに任せる（自動で書かれる）。ユーザーが「覚えておいて」と言った内容もauto memory行き
2. **`CLAUDE.md` か `.claude/rules/` かを決める**
   - ほぼ毎回必要な内容（プロジェクト概要、必ず守らせたい規約） → `CLAUDE.md`
   - 特定のファイル種別・ディレクトリでしか関係ない内容（特定言語の書き方、特定機能が散在する箇所の説明） → `.claude/rules/<topic>.md` に `paths` frontmatter付きで
   - 判断に迷う・どちらでも良い場合はmemory.mdの使い分け表を確認
3. **スコープを決める**
   - チーム全員に共有 → プロジェクト直下（`./CLAUDE.md` / `./.claude/CLAUDE.md` / `./.claude/rules/`）、Gitにコミット
   - 自分だけ・このプロジェクト限定 → `./CLAUDE.local.md`（`.gitignore`推奨）
   - 自分の全プロジェクト共通 → `~/.claude/CLAUDE.md` / `~/.claude/rules/`
4. **`CLAUDE.md`を書く場合**
   - 200行未満を目安に、検証可能な粒度（具体的なコマンド・数値）で書く
   - 超えそうなら`.claude/rules/`への切り出しか、`@path`インポートでの分割を検討（インポートはトークン削減にはならない点に注意）
5. **`.claude/rules/`を書く場合**
   - 1トピック1ファイル。`paths`のglobパターンで対象を絞る（絞らないと`CLAUDE.md`と同じく毎回読み込まれる）
   - 複数プロジェクトで共有したい場合はsymlinkも使える
6. **auto memoryを設定する場合**
   - 既定で有効。無効化・保存先変更は`settings.json`の`autoMemoryEnabled`/`autoMemoryDirectory`、または環境変数`CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`
   - 中身の確認・編集は`/memory`から

## チェックリスト

- [ ] 動的な実行結果（コマンド出力など）をコンテキストに注入したい内容は、メモリでなく**SKILL**に切り出す（メモリは静的テキストのみ）
- [ ] 特定タイミングで必ず実行・ブロックしたい処理（コミット前チェック等）はメモリでなく**フック**にする（メモリは強制力のないコンテキストでしかない）
- [ ] `CLAUDE.md`を新規作成するときは、手書きよりまず`/init`を試す（既存があれば上書きせず改善提案になる）
- [ ] 複数の`CLAUDE.md`/rulesファイルで矛盾する指示がないか定期的に見直す（矛盾するとClaudeが恣意的にどちらかを選ぶ）
- [ ] モノレポで他チームの`CLAUDE.md`が無関係なら`claudeMdExcludes`で除外する
- [ ] auto memoryの保存先変更（`autoMemoryDirectory`）をプロジェクト設定に書く場合、ワークスペース信頼ダイアログの承認が必要な点をユーザーに伝える
- [ ] Windows環境（このマシン）では`CLAUDE.md`のシンボリックリンク運用（`AGENTS.md`共有等）は管理者権限が要るため、`@AGENTS.md`インポートを使う

## 困ったときは

1. まず同梱の [memory.md](memory.md)（CLAUDE.md/rulesのスコープ表・auto memoryの保存構造・`/memory`コマンド・トラブルシューティングの詳細）を確認する。
2. それでも解決しない、載っていない設定キーを使いたい、または仕様が変わっている可能性がある場合は**claude-code-docsスキル**で最新の公式ドキュメント（`code.claude.com`）を参照する（CLAUDE.mdのルールで必須）。
3. `.claude/rules/`のfrontmatter仕様や実際のファイル配置作業そのものは**writing-rulesスキル**、hooksの作成は**writing-hooksスキル**、settings.jsonの`autoMemoryEnabled`以外の項目は**configuring-settingsスキル**を使う。
