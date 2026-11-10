---
name: copilot-cli-docs
description: Use when answering questions about the GitHub Copilot CLI (`copilot` command) — options, commands, help topics, MCP config, permissions, etc. Grounds answers in the CLI's own `--help` output instead of training-data memory, which may be stale.
meta:
  tag: []
  requires_repo_tools: none
  requires_env: none
  dependencies: python, copilot-cli
  requires_install: none
  requires_hooks: none
  requires_skills: none
  status: stable
  description: no description
  version: 1.0.4
---

# GitHub Copilot CLI ヘルプ参照

GitHub Copilot CLI（`copilot` コマンド）に関する質問に、学習データの記憶ではなく `copilot --help` の実際の出力を根拠に回答するためのスキル。

## 手順

最新の CLI ヘルプが必要な場合は、このスキルのディレクトリを作業ディレクトリにして `python generate_copilot_help_yaml.py` を実行し、`output/help_result.yaml` を更新する。スクリプト実行には Copilot CLI と Python が必要で、実行前に内容を確認する。

1. **`output/help_result.yaml` を Read/Grep して回答する**

   - オプション名・サブコマンド名・Examples を検索し、該当エントリの `description` を根拠として提示する
   - 回答には、どのオプション/コマンドを参照したかを明示する（例: `--allow-tool` オプションの説明に基づく、など）
