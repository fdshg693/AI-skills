---
# 前提条件: `claude` CLI（Claude Code）がインストールされ PATH から呼べること。
#   無い環境では生成スクリプトが失敗するため、その場合は同梱の output/help_result.yaml
#   （コミット済みの生成スナップショット）をそのまま参照する。
# 棲み分け: Claude Code の機能・設定の概念（公式サイトのドキュメント由来）は claude-code-docs スキル。
#   このスキルは `claude` コマンドの CLI インターフェース（`--help` 出力由来）に特化する。
# !`<command>`を使ってスクリプトを実行することで、確実にコマンドを実行できるようにする。
name: claude-cli-docs
description: Use when answering questions about the `claude` command's CLI interface — options, flags, and subcommands (e.g. -p/--print, --dangerously-skip-permissions, mcp, plugin, agents, doctor). Grounds answers in the CLI's own `claude --help` output instead of training-data memory, which may be stale. For Claude Code feature/settings concepts documented on the official site (hooks, skills, settings.json), use claude-code-docs instead.
allowed-tools: Bash(python ${CLAUDE_SKILL_DIR}/*.py *)
meta:
  tag: []
  requires_repo_tools: none
  requires_env: none
  dependencies: claude
  requires_install: PyYAML
  requires_hooks: none
  requires_skills: claude-code-docs
  status: stable
  description: no description
  version: 1.0.0
---

!`python ${CLAUDE_SKILL_DIR}/generate_claude_help_yaml.py`

# Claude CLI ヘルプ参照

Claude Code CLI（`claude` コマンド）に関する質問に、学習データの記憶ではなく `claude --help` の実際の出力を根拠に回答するためのスキル。

## 手順

1. **`${CLAUDE_SKILL_DIR}/output/help_result.yaml` を Read/Grep して回答する**

   - `usage` / `description` / `commands`（サブコマンド一覧）/ `arguments` / `options` を検索し、該当エントリの `description` を根拠として提示する
   - 回答には、どのオプション/サブコマンドを参照したかを明示する（例: `--dangerously-skip-permissions` オプションの説明に基づく、など）
   - `--dangerously-skip-permissions` のような危険操作・権限関連のオプションについて聞かれた場合は、`description` に書かれている警告文（"Bypass all permission checks. Recommended only for sandboxes with no internet access." 等）をそのまま伝える

2. **サブコマンド固有の詳細は `claude <サブコマンド> --help` の実行結果で確認する**

   `claude --help` のトップレベル出力には `commands` の説明しかない（`mcp` / `plugin` / `agents` / `doctor` / `install` / `auth` など多数のサブコマンドがある）。それぞれの詳しいオプションを聞かれたら、以下のいずれかで確認する。

   - `claude <サブコマンド> --help` を実行し、出力をそのまま読んで回答する
   - 構造化して残したい場合は `python ${CLAUDE_SKILL_DIR}/generate_claude_help_yaml.py --help-file <キャプチャしたファイル> --output ${CLAUDE_SKILL_DIR}/output/<サブコマンド>.yaml` でパースし直す（このスキルのパーサーは `Commands:` / `Arguments:` / `Options:` セクション構造であれば、トップレベル以外にも使える）

## 補足

- スクリプトはこのスキルのディレクトリを基準に `output/` を読み書きする
- `claude --version` と `claude --help` を実行し、構造化した結果を `output/help_result.yaml` に書き出す（バージョン、usage、description、commands、arguments、options）
- Claude Code の `--help` は commander.js（Node.js）製で、Codex CLI の clap（Rust）製とはヘルプの書式が異なる（各エントリは「インデント2の名前行＋同行または深いインデントに揃えられた説明行」の形。長いフラグ名では説明が次行に折り返される。パーサーはこれらの説明行を空白1つで連結して1つの `description` にまとめている）
- `claude` コマンドが無い/失敗する環境ではスクリプトの実行が失敗するが、その場合はバンドル済みの `output/help_result.yaml`（同梱の生成済みスナップショット）をそのまま使う
- `output/help_result.yaml` は生成物だが、`claude` CLI が使えない環境でも参照できるようリポジトリにコミットして同梱している
