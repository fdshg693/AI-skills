---
name: authoring-playwright-agents
description: Authors and reviews Playwright-specialised agent definitions, grounded in a local snapshot of microsoft/playwright. Use when writing or reviewing an `*.agent.md`, a `.claude/agents/*.md`, or a prompt that drives Playwright; when asked about `npx playwright init-agents`, the official planner / generator / healer agents, or the `playwright-test` MCP tools (`planner_*`, `generator_*`, `test_*`, `browser_*`).
allowed-tools: Bash(uv run ${CLAUDE_SKILL_DIR}/*.py *)
# 同梱ファイル:
#   - agent-definition-format.md: *.agent.md のフォーマットとループ別ツール変換、作成手順
#   - download_playwright_agents.py: upstream スナップショット取得（!`` で起動時に実行）
#   - output/: microsoft/playwright main のスナップショット（生成物。手で編集しない）
#   - README.md: メンテナ向け。取得対象の増やし方、設計意図
# 暗黙の前提:
#   - `gh` が PATH にあること（公開リポジトリなので未認証でも動くが、レート制限回避のため `gh auth login` 済みが望ましい）
#   - `uv` が PATH にあること（スクリプトは標準ライブラリのみ使用）
#   - 手元の Playwright やチェックアウトは古い/改変されうるため、判断の根拠は常に output/ のスナップショットを使う
# 依存スキル: なし
meta:
  tag: []
  requires_repo_tools: none
  requires_env: none
  dependencies: gh, uv
  requires_install: none
  requires_hooks: none
  requires_skills: none
  status: experimental
  description: Playwright 公式エージェント定義・playwright-test MCP ツールのミラーと、エージェント定義の書き方
  version: 1.0.0
---

!`uv run "${CLAUDE_SKILL_DIR}/download_playwright_agents.py"`

# Playwright 特化エージェントの作成

記憶ではなく `${CLAUDE_SKILL_DIR}/output/`（microsoft/playwright `main` のスナップショット）を根拠にする。
上のコマンドで取得済み。エラーが出ていた場合は原因（`gh` 未インストール等）を伝えてから続行する。

目的に応じて、該当する方だけ読む。

1. **エージェント定義を書く・レビューする** — [agent-definition-format.md](agent-definition-format.md) を読み、その手順に従う
2. **公式定義・MCP ツール・CLI の挙動を答える** — 下記の対応表から必要なファイルだけ Read する

## 参照先の対応表

`${CLAUDE_SKILL_DIR}/output/` 配下。全体の索引は `output/summary.md`。`output/` をまとめて流さない。

| 探しもの                                                  | 見る場所                                                            |
| --------------------------------------------------------- | ------------------------------------------------------------------- |
| 公式エージェントの指示文・tools・examples                 | `output/agents/playwright-test-{planner,generator,healer}.agent.md` |
| スラッシュコマンド用プロンプト                            | `output/agents/playwright-test-*.prompt.md`                         |
| `.agent.md` のパース規則（必須フィールド・examples 抽出） | `output/agents/agentParser.ts`                                      |
| ループ別の出力先とツール名マッピング                      | `output/agents/generateAgents.ts`                                   |
| `playwright-test` MCP ツールの実体・引数                  | `output/mcp-tools/*.ts`                                             |
| `init-agents` の CLI オプション                           | `output/cli/program.ts` の `addInitAgentsCommand`                   |
| ユーザー向けの説明・ワークフロー                          | `output/docs/test-agents-js.md`                                     |

読んだ本文で答え、`output/` 内の相対パスと上流 URL（`https://github.com/microsoft/playwright/blob/main/<元パス>`、元パスは `output/_meta.json`）を示す。
対応表に無い話題ならその旨を伝える。手元にインストールされた Playwright と upstream に差があれば、差として報告する。

## スナップショットの更新

既定では 7 日以内に取得済みならスキップされる。強制再取得:

```bash
uv run "${CLAUDE_SKILL_DIR}/download_playwright_agents.py" --force
```

公式定義は Playwright のリリースごとに更新される。バージョン差が問題になりそうなときは `--force` してから答える。
