---
name: cline-cli-docs
description: Use when answering questions about the Cline CLI (`cline` command) — prompts, plan/act execution, providers and models, authentication, JSON output, sessions, MCP, plugins, hooks, scheduling, Hub, Kanban, worktrees, ACP, permissions, or any command-line option. Grounds answers in the installed CLI's current `--help` output and the official Cline CLI reference instead of stale memory.
allowed-tools: Bash(python skills/plugins/ai-tools-knowledge/skills/cline-cli-docs/*.py *)
# !`<command>`を使ってスクリプトを実行することで、確実にコマンドを実行できるようにする。
meta:
  tag: []
  requires_repo_tools: none
  requires_env: none
  dependencies: none
  requires_install: python
  requires_hooks: none
  requires_skills: none
  status: stable
  description: no description
  version: 1.0.5
---

!`python "${CLAUDE_SKILL_DIR}/generate_cline_help_yaml.py"`

# Cline CLI ヘルプ参照

Cline CLI（`cline` コマンド）に関する質問には、インストール済み CLI の実際のヘルプ出力を第一の根拠として回答する。Cline の CLI 仕様は更新されるため、学習データや古い例を優先しない。

## 手順

1. **`output/help_result.yaml` を Read/Grep して回答する**

   - `usage` / `description` / `arguments` / `options` / `commands` から該当項目を探す。
   - 回答では参照したオプションまたはサブコマンド名を明示し、YAML の `description` を根拠にする。
   - `--auto-approve`、`--data-dir`、`--worktree`、`--hooks-dir`、`--config`、`--key` など、実行権限・認証・状態保存に影響する項目は、ヘルプに書かれた既定値や注意書きを省略しない。

2. **サブコマンド固有の詳細を直接確認する**

   トップレベルのヘルプはサブコマンドの概要だけを示す。詳細を聞かれたら、必要なコマンドだけ `cline <サブコマンド> --help` を実行して確認する（例: `cline auth --help`、`cline mcp --help`、`cline plugin --help`、`cline schedule --help`）。

   構造化して残す必要がある場合は、ヘルプ出力をファイルに保存して次を実行する。

   ```text
   python "${CLAUDE_SKILL_DIR}/generate_cline_help_yaml.py" --help-file <captured-help> --output output/<subcommand>.yaml
   ```

   `--help-file` は Commander.js 形式の `Arguments:` / `Options:` / `Commands:` セクションを解析する。

3. **公式ドキュメントで背景を補足する**

   CLI の全体像・設定ファイル・環境変数・JSON 出力・認証フローなどの説明が必要なら、Cline 公式の [CLI Reference](https://docs.cline.bot/cli/cli-reference) を参照する。ローカルの公式ドキュメントスキルが利用できる場合は、`cli/cli-reference` を抽出して `Source:` 行を根拠にする。

   CLI の実際のヘルプと公式ページが異なる場合は、**インストール済み CLI のヘルプをコマンドの可否・引数・既定値の根拠**とし、公式ページは補足情報として扱う。差異が回答に影響する場合はその旨を明記する。

## 補足

- スクリプトはこのディレクトリを基準に `output/` を読み書きする。
- `cline --version` と `cline --help` を実行し、24 時間以内の `output/help_result.yaml` があれば再取得を省略する。最新化が必要な場合は `--force` を付ける。
- `cline` コマンドがない、または実行できない環境では、バンドル済みの `output/help_result.yaml` を使い、スナップショットの `version` と `fetched_at` を回答の前提として明示する。
- 危険な自動承認・隔離無効化・秘密情報を扱う質問では、実行例を出す前に影響範囲を説明し、キーやトークンなどの実値を出力・保存しない。
