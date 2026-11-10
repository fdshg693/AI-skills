---
# 詳細仕様は同階層の agents-md.md / instructions.md / context.md を必要時だけ読む。
name: kilo-memory-guide
description: Kilo Code（kilo.ai、CLI/TUI/VS Code拡張）のAIコンテキスト・指示を設計・整理するための実践スキル。AGENTS.md、Custom Instructions/Rules、エージェント固有prompt、コンテキスト制御、設定の優先順位や適用範囲を選ぶときに使う。
meta:
  tag: []
  requires_repo_tools: none
  requires_env: none
  dependencies: none
  requires_install: none
  requires_hooks: none
  requires_skills: none
  status: experimental
  description: Kiloの永続的な指示とコンテキストの使い分けガイド
  version: 1.0.1
---

# Kilo Memory / Context Guide

Kilo Codeで「次のタスクでも守らせたい知識・制約」を、適切なスコープと仕組みに配置するためのガイド。ここでいうメモリは単一のデータベース機能ではなく、指示ファイル、設定の`instructions`、エージェントprompt、コンテキスト機能の組み合わせを指す。

## まず選ぶ

1. **プロジェクトの常設ルール・設計知識** → ルートの`AGENTS.md`
2. **サブディレクトリだけの補足** → 対象ディレクトリの`AGENTS.md`
3. **Kilo固有の複数ルール、glob、URL、順序制御** → `kilo.jsonc`の`instructions`
4. **特定agentだけの人格・作業手順** → agentの`prompt`またはCustom Mode

## 運用フロー

1. 指示の対象（全プロジェクト、プロジェクト、ディレクトリ、agent、オンデマンド）を決める。
2. 秘密情報・矛盾・重複を除き、短い規則と具体例にする。
3. ルールを分割し、常時注入する情報を増やしすぎない。
4. Kiloを新しいタスクまたはセッションで起動し、実際に適用されたか確認する。
5. 仕様が不明な場合は、詳細資料の公式URLを再確認する。学習データの記憶だけでパスや優先順位を断定しない。

## 重要な注意

- AGENTS.mdは指示ファイルであり、会話をまたぐ事実の自動記録・検索データベースではない。更新は明示的に行う。
- 機密情報、APIキー、個人情報を指示ファイルや設定に保存しない。

## 詳細資料

- [agents-md.md](agents-md.md): AGENTS.mdの場所、命名、動的ロード、優先順位
- [instructions.md](instructions.md): Custom Instructions/Rulesと`kilo.jsonc`
- [context.md](context.md): コンテキスト、condensing、ignoreの整理

## 出典

- https://kilo.ai/docs/customize/agents-md
- https://kilo.ai/docs/customize/custom-instructions
- https://kilo.ai/docs/customize/custom-rules
- https://kilo.ai/docs/customize/context/context-condensing
- https://kilo.ai/docs/customize/context/kilocodeignore

公式ページの確認日: 2026-09-01
