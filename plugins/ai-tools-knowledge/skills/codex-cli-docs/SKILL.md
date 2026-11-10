---
name: codex-cli-docs
description: Use when answering questions about the OpenAI Codex CLI (`codex` command) — options, subcommands, sandbox/approval policies, MCP config, etc. Grounds answers in the CLI's own `--help` output instead of training-data memory, which may be stale.
allowed-tools: Bash(python skills/plugins/ai-tools-knowledge/skills/codex-cli-docs/*.py *)
# !`<command>`を使ってスクリプトを実行することで、確実にコマンドを実行できるようにする。
meta:
  tag: []
  requires_repo_tools: none
  requires_env: CLAUDE_SKILL_DIR
  dependencies: python, codex
  requires_install: none
  requires_hooks: none
  requires_skills: none
  status: stable
  description: no description
  version: 1.0.5
---

!`python "${CLAUDE_SKILL_DIR}/generate_codex_help_yaml.py"`

# Codex CLI ヘルプ参照

OpenAI Codex CLI（`codex` コマンド）に関する質問に、学習データの記憶ではなく `codex --help` の実際の出力を根拠に回答するためのスキル。

## 手順

1. **`output/help_result.yaml` を Read/Grep して回答する**

   - `usage` / `description` / `commands`（サブコマンド一覧）/ `arguments` / `options` を検索し、該当エントリの `description` を根拠として提示する
   - 回答には、どのオプション/サブコマンドを参照したかを明示する（例: `--dangerously-bypass-approvals-and-sandbox` オプションの説明に基づく、など）
   - `--dangerously-*` や `-s, --sandbox` のような危険操作・権限関連のオプションについて聞かれた場合は、`description` に書かれている警告文（EXTREMELY DANGEROUS 等）をそのまま伝える

2. **サブコマンド固有の詳細は `codex <サブコマンド> --help` の実行結果で確認する**

   `codex --help` のトップレベル出力には `commands` の一行説明しかない（`exec` / `review` / `mcp` / `plugin` / `resume` / `sandbox` / `debug` など多数のサブコマンドがある）。それぞれの詳しいオプションを聞かれたら、以下のいずれかで確認する。

   - `codex <サブコマンド> --help` を実行し、出力をそのまま読んで回答する
   - 構造化して残したい場合は `generate_codex_help_yaml.py --help-file <キャプチャしたファイル> --output output/<サブコマンド>.yaml` でパースし直す（このスキルのパーサーは clap 由来の `Commands:` / `Arguments:` / `Options:` セクション構造であれば、トップレベル以外にも使える）

## 補足

- スクリプトはこのディレクトリ（`skills/plugins/ai-tools-knowledge/skills/codex-cli-docs/`）を基準に `output/` を読み書きする
- `codex --version` と `codex --help` を実行し、構造化した結果を `output/help_result.yaml` に書き出す（バージョン、usage、description、commands、arguments、options）
- Codex CLI の `--help` は clap（Rust）製で GitHub Copilot CLI とはヘルプの書式が異なる（`Arguments:`/`Options:` の各エントリは「フラグ名の行」＋「インデントされた説明行（複数行・空行区切りの段落を含む）」の形。パーサーはこれらの説明行を空白1つで連結して1つの `description` にまとめている）
- `codex` コマンドが無い/失敗する環境ではスクリプトの実行が失敗するが、その場合はバンドル済みの `output/help_result.yaml`(同梱の生成済みスナップショット、`codex-help.md` から生成)をそのまま使う
- `output/help_result.yaml` は生成物だが、`codex` CLI が使えない環境でも参照できるようリポジトリにコミットして同梱している
