---
name: codegraph-docs
description: Use when exploring a codebase with CodeGraph (colbymchenry/codegraph) via MCP codegraph_explore or CLI `codegraph explore` — symbols, callers, callees, impact, or how code flows — before falling back to grep/Read, or when answering questions about CodeGraph itself (install, MCP, CLI flags and subcommands such as --max-files / --json / serve --mcp, indexing, languages, agent integrations). Grounds product answers in the local official-docs snapshot from colbymchenry/codegraph site/src/content/docs, and CLI interface answers in the bundled `codegraph --help` YAML.
allowed-tools: Bash(python ${CLAUDE_SKILL_DIR}/*.py *) Bash(uv run ${CLAUDE_SKILL_DIR}/*.py *)
# 同梱ファイル: using-codegraph.md（地図は files/status、流れは explore）/ cli-help.md（フラグ一次情報）/ output/（公式docs）/ output/cli/（--help YAML）
# 前提:
#   - コード探索には `codegraph` が PATH にあり、対象プロジェクトに `.codegraph/` 索引があること
#   - 公式docs取得はこのスキルの download スクリプトが `gh api` を呼ぶ（公開リポジトリ。レート制限回避のため `gh auth login` 済みが望ましい）
#   - CLI ヘルプ生成は `codegraph` が PATH にあること。無い環境では同梱の output/cli/help_result.yaml を使う
#   - MCP はエージェントが `codegraph serve --mcp` を起動する。手起動しない
# !`<command>` で起動時に必ずスナップショットを更新/確認する
meta:
  tag: []
  requires_repo_tools: none
  requires_env: none
  dependencies: PyYAML, gh
  requires_install: npm i -g @colbymchenry/codegraph
  requires_hooks: none
  requires_skills: none
  status: stable
  description: CodeGraph 公式docsミラー、CLI --help YAML、MCP/CLI 実行時判断
  version: 1.0.4
---

!`python "${CLAUDE_SKILL_DIR}/download_codegraph_docs.py"`
!`uv run "${CLAUDE_SKILL_DIR}/generate_codegraph_help_yaml.py"`

# CodeGraph

目的に応じて、該当する方だけ読む。フラグ名・呼び出し形が公式 CLI 節と食い違うときは [cli-help.md](cli-help.md) を優先する。

1. **コードを調べる / MCP・CLI を実行する** — [using-codegraph.md](using-codegraph.md)（地図・概要は `files` / `status` が先。explore は名前の付いた流れから）
2. **CLI のフラグ・サブコマンド・正確な呼び出し形** — [cli-help.md](cli-help.md)
3. **CodeGraph 製品の公式ドキュメントを根拠に答える** — 下記

## 公式ドキュメントを参照するとき

学習データの記憶ではなく、GitHub 上の公式ドキュメント（`colbymchenry/codegraph` の `site/src/content/docs`）を根拠にする。

1. `${CLAUDE_SKILL_DIR}/output/summary.md` を Read/Grep し、関係するパスを特定する
   - `getting-started/`（導入・設定）、`core-concepts/`（知識グラフ・解決）、`guides/`（索引・ビューア・ルート・affected tests）、`reference/`（MCP / CLI / API / 言語 / 連携）、`troubleshooting.md`
2. `${CLAUDE_SKILL_DIR}/output/<相対パス>` だけ Read する。`output/` をまとめて流さない
3. 読んだ本文で答え、相対パスと可能なら上流 URL を明示する
   - 上流: `https://github.com/colbymchenry/codegraph/blob/main/site/src/content/docs/<相対パス>`
   - 公開サイト: `https://colbymchenry.github.io/codegraph/<slug>/`（`.md` を除き末尾スラッシュ。例: `reference/cli.md` → `.../reference/cli/`）
   - `summary.md` に無い話題なら、その旨を伝え、必要なら上流を別途確認する

強制再取得: docs は `python "${CLAUDE_SKILL_DIR}/download_codegraph_docs.py" --force`（メタは `output/_meta.json`）。CLI ヘルプは `uv run "${CLAUDE_SKILL_DIR}/generate_codegraph_help_yaml.py" --force`。
