---
name: writing-plugins
description: Use when creating, reviewing, installing, distributing, or troubleshooting a GitHub Copilot agent plugin for Copilot CLI, Copilot cloud agent, or VS Code. Covers plugin.json, bundled agents/skills/hooks/MCP/LSP, marketplace.json, enabledPlugins, local testing, host differences, and safe validation. Do not use for Claude Code plugins or VS Code extension API development.
meta:
  tag: []
  requires_repo_tools: none
  requires_env: none
  dependencies: none
  requires_install: none
  requires_hooks: none
  requires_skills: github-copilot-docs, vscode-copilot-docs
  status: stable
  description: no description
  version: 1.0.3
---

# GitHub Copilot Plugin の作成・利用

GitHub Copilot の agent plugin を作成・導入・配布するときに使う。これは Copilot が読む plugin の仕様を扱うスキルであり、このスキル自身の `SKILL.md` や Claude Code の Plugin 仕様を編集するためのものではない。

## 使い分け

依頼に必要なファイルだけを読み込む。

- 新規作成・manifest・ローカル開発: [references/create-plugin.md](references/create-plugin.md)
- agents / skills / commands / hooks / MCP / LSP の設計: [references/components.md](references/components.md)
- Copilot CLI で探す・入れる・更新する・使う: [references/cli-usage.md](references/cli-usage.md)
- VS Code の Agent Plugins と他ツール互換: [references/vscode-usage.md](references/vscode-usage.md)
- Copilot cloud agent とリポジトリ設定: [references/cloud-agent-usage.md](references/cloud-agent-usage.md)
- marketplace の作成・登録・配布: [references/marketplace.md](references/marketplace.md)
- 読み込み失敗・重複・キャッシュ・安全性の切り分け: [references/troubleshooting.md](references/troubleshooting.md)

## 共通手順

1. 対象ホスト（CLI、cloud agent、VS Code）と、作成・利用・配布・障害対応のどれかを確定する。ホストが複数なら、共通部分と差分を分けて説明する。
2. 既存の `plugin.json`、marketplace、関連する component の配置を確認する。対象が GitHub Copilot か Claude Code か不明な場合は、manifest の場所と実行クライアントを確認してから編集する。
3. 仕様が変わり得る項目は [github-copilot-docs](../github-copilot-docs/SKILL.md) の手順で公式 `docs.github.com` を確認する。VS Code 固有の項目は [vscode-copilot-docs](../vscode-copilot-docs/SKILL.md) と `code.visualstudio.com` を確認する。
4. JSON、名前、相対パス、component の読み込み結果を検証する。hooks と MCP はコードを実行するため、インストール前に内容・権限・外部通信・秘密情報の扱いをレビューする。
5. 完了時には、対象ホスト、インストール方法、検証コマンド、既知の制限を明示する。

詳細な仕様・例・コマンドは、上記のユースケース別ファイルを必要なときだけ参照する。
