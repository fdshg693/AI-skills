---
name: cursor-cli-docs
description: Use when answering questions about the Cursor CLI (`agent` command, formerly `cursor-agent`) — options, subcommands, sandbox/approval flags, MCP config, worktrees, etc. Grounds answers in the CLI's own `--help` output instead of training-data memory, which may be stale.
allowed-tools: Bash(python skills/plugins/ai-tools-knowledge/skills/cursor-cli-docs/*.py *)
# !`<command>`を使ってスクリプトを実行することで、確実にコマンドを実行できるようにする。
meta:
  tag: []
  requires_repo_tools: none
  requires_env: none
  dependencies: python
  requires_install: none
  requires_hooks: none
  requires_skills: none
  status: stable
  description: no description
  version: 1.0.6
---

!`python "${CLAUDE_SKILL_DIR}/generate_cursor_agent_help_yaml.py"`

# Cursor CLI ヘルプ参照

Cursor CLI（`agent` コマンド、旧名 `cursor-agent`）に関する質問に、学習データの記憶ではなく `agent --help` の実際の出力を根拠に回答するためのスキル。

## 手順

1. **`output/help_result.yaml` を Read/Grep して回答する**

   - `usage` / `description` / `arguments` / `options` / `commands` を検索し、該当エントリの `description` を根拠として提示する
   - 回答には、どのオプション/サブコマンドを参照したかを明示する（例: `--sandbox` オプションの説明に基づく、など）
   - `-f, --force` / `--yolo`（サンドボックス無効化・自動許可系）について聞かれた場合は、`description` の内容（`Force allow commands unless explicitly denied` 等）をそのまま伝える

2. **サブコマンド固有の詳細は `agent <サブコマンド> --help` の実行結果で確認する**

   トップレベルの `agent --help` には `commands` の一行説明しかない（`mcp` / `login` / `models` / `resume` など）。それぞれの詳しいオプションを聞かれたら、以下のいずれかで確認する。

   - `agent <サブコマンド> --help` を実行し、出力をそのまま読んで回答する（例: `agent mcp --help` で `mcp login` / `list` / `list-tools` / `enable` / `disable` のさらに一段下のサブコマンドが分かる）
   - 構造化して残したい場合は `generate_cursor_agent_help_yaml.py --help-file <キャプチャしたファイル> --output output/<サブコマンド>.yaml` でパースし直す（このスキルのパーサーは Commander.js 由来の `Arguments:` / `Options:` / `Commands:` セクション構造であれば、トップレベル以外にも使える）

## 補足

- スクリプトはこのディレクトリ（`skills/plugins/ai-tools-knowledge/skills/cursor-cli-docs/`）を基準に `output/` を読み書きする
- `agent --version` と `agent --help` を実行し、構造化した結果を `output/help_result.yaml` に書き出す（バージョン、usage、description、arguments、options、commands）
- Cursor CLI のコマンド名は `agent`（旧名 `cursor-agent` は同じバイナリを指すレガシーエイリアスとして残っている）。`--help` は Commander.js（Node.js）製で、GitHub Copilot CLI と同じ「フラグ名の行 + 2スペース以上区切りの説明」形式（Codex CLI の clap 製ヘルプとはレイアウトが異なる）。トップレベルには Examples/Help Topics/Learn More に相当するセクションは無い
- `agent` コマンドが無い/失敗する環境ではスクリプトの実行が失敗するが、その場合はバンドル済みの `output/help_result.yaml`(同梱の生成済みスナップショット)をそのまま使う
- `output/help_result.yaml` は生成物だが、`cursor-agent` CLI が使えない環境でも参照できるようリポジトリにコミットして同梱している
