---
# 前提条件:
#   - 公式サイト側: ネットワークで ccusage.com の llms.txt / llms-full.txt を取得できること
#   - CLI 側: このリポジトリの package.json に ccusage が入っていること（pnpm install 済み）。
#     無い環境では生成スクリプトが失敗するため、同梱の output/cli/*.yaml
#     （コミット済みの生成スナップショット）をそのまま参照する
# 旧 ccusage-cli-docs をこのスキルに統合。概念は official-docs.md、フラグ一次情報は cli-help.md
# !`<command>`を使ってスクリプトを実行することで、確実にコマンドを実行できるようにする。
name: ccusage-docs
description: Use when answering questions about ccusage (ccusage.com) — the local CLI that reads coding-agent usage files and reports token usage and estimated costs across Claude Code, Codex, OpenCode, Amp, Droid, Codebuff, Hermes Agent, pi-agent, Goose, OpenClaw, Kilo, Kimi, Qwen, GitHub Copilot CLI, Gemini CLI, Antigravity, Grok Build CLI, and ZCode. Covers installation, data-source locations, config files, environment variables, cost modes, daily/weekly/monthly/session/blocks reports, JSON output, statusline, per-source setup, and raw `ccusage` CLI invocations (flags, subcommands, `ccusage claude daily` / `ccusage grok session`, date filters). Grounds answers in the latest official docs from ccusage.com and the CLI's own `--help` output instead of training-data memory, which may be stale.
allowed-tools: Bash(python ${CLAUDE_SKILL_DIR}/*.py *) Bash(uv run ${CLAUDE_SKILL_DIR}/*.py *)
meta:
  tag: []
  requires_repo_tools: aim
  requires_env: none
  dependencies: requests, typer, PyYAML
  requires_install: none
  requires_hooks: none
  requires_skills: none
  status: stable
  description: Official site (llms.txt) plus bundled `ccusage --help` YAML. Former ccusage-cli-docs lives under cli-help.md / output/cli/.
  version: 1.1.1
---

!`python "${CLAUDE_SKILL_DIR}/webref_cli.py" download`
!`uv run "${CLAUDE_SKILL_DIR}/generate_ccusage_help_yaml.py"`

# ccusage 最新ドキュメント参照

ccusage（ccusage.com）に関する質問に、学習データの記憶ではなく公式サイトと実際の `ccusage --help` を根拠に回答する。学習データは対応ソースが増える前の「Claude Code専用」という印象や、削除済みの live monitoring を残していることがあるため、現行のソース一覧・コマンド形・廃止機能は取得した内容で上書きする。

## 手順

1. **質問の性質を判定する**
   - インストール・データソースの場所・設定ファイル・環境変数・cost modes の意味・レポートの見方 → [official-docs.md](official-docs.md) を読み、その手順に従う
   - フラグ名・サブコマンド・正確な呼び出し形（`ccusage claude daily` 等）→ [cli-help.md](cli-help.md) を読み、その手順に従う
   - 両方にまたがる（「このフラグは何を意味するか」「この設定を CLI でどう渡すか」）→ 両方読む。意味・場所は公式サイト、正確なフラグ名は `--help` YAML

2. **共通の事実（どちらの手順でも守る）**
   - 既定の `ccusage daily` 等は検出できた全ソースを集計する。1ソースに絞る形は `ccusage <source> <report>`（例: `ccusage claude daily`）
   - `output/llms.txt` で `Live Monitoring (Removed)` とある機能は削除済み。現行 CLI に無いコマンドを学習データの記憶で補わない
