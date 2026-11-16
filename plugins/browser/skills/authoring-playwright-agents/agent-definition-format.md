# エージェント定義のフォーマットと作成手順

公式の planner / generator / healer は「ループ非依存の `*.agent.md` 1 つ」を各エージェンティックループの形式へ
変換して配る構造になっている。自作の Playwright 特化エージェントもこの構造に合わせる。

- [1. 作成・レビュー手順](#1-作成レビュー手順)
- [2. `*.agent.md` のフォーマット](#2-agentmd-のフォーマット)
- [3. ツール名のループ別変換](#3-ツール名のループ別変換)
- [4. 指定できる MCP ツール](#4-指定できる-mcp-ツール)

パスはすべて `${CLAUDE_SKILL_DIR}/output/` からの相対。断定する前に該当ファイルを Read する。

## 1. 作成・レビュー手順

1. **雛形を選ぶ** — 作りたいものに一番近い公式定義を丸ごと Read する
   - `agents/playwright-test-planner.agent.md` — アプリを探索して Markdown のテストプランを書く
   - `agents/playwright-test-generator.agent.md` — プランを `*.spec.ts` に変換する
   - `agents/playwright-test-healer.agent.md` — 失敗テストを実行して修復する
2. **`name` / `description` を書く** — `name` はファイル名と一致させる。`description` は「いつ呼ぶか」を書く（何をするかではない）
3. **`tools` を必要最小限に絞る** — 読むだけのエージェントに `edit` を入れない。MCP ツールは §4 で実在を確認してから足す
4. **本文（instructions）を書く** — 公式の 3 つはいずれも「手順 → 制約 → 出力形式」の順で、出力先ファイル名まで指定している。同じ具体度で書く
5. **`<example>` を 1〜2 個付ける** — 呼び出し判断の精度がここで決まる
6. **配置する**
   - 公式ループに乗せる → `*.agent.md` として置き、`agents/generateAgents.ts` 相当の変換をかける
   - Claude Code で使う → §3 の変換を手で適用し、作業中のプロジェクトの `.claude/agents/<name>.md` に置く

レビュー時は §2 の必須フィールド、§3 のツール名、§4 の実在確認を順に照合する。

## 2. `*.agent.md` のフォーマット

`agents/agentParser.ts` が要求する形:

```markdown
---
name: <エージェント名。ファイル名と一致させる>
description: <いつ使うかの一文。必須>
model: sonnet
color: green
tools:
  - search
  - playwright-test/browser_click
  - playwright-test/planner_save_plan
---

<本文＝そのまま instructions になる>

<example>ユーザー発話とエージェントの応答の例</example>
```

- `name` と `description` は必須。欠けるとパースエラー
- 本文は最初の `<example>` の手前までが `instructions`。`<example>...</example>` は個別に抽出され、
  `description` の末尾に `Examples: <example>...</example>` として連結される
- `tools` の書き方は 2 通り
  - **抽象名** — `search` / `edit`。ループごとに実ツール名へ展開される
  - **MCP ツール** — `<MCP サーバ名>/<ツール名>`（例 `playwright-test/browser_snapshot`）

## 3. ツール名のループ別変換

`agents/generateAgents.ts` の `ClaudeGenerator.agentSpec()`:

| `*.agent.md` の書き方           | Claude Code 側                        |
| ------------------------------- | ------------------------------------- |
| `search`                        | `Glob, Grep, Read, LS`                |
| `edit`                          | `Edit, MultiEdit, Write`              |
| `playwright-test/browser_click` | `mcp__playwright-test__browser_click` |
| その他（`Bash` など）           | そのまま                              |

出力先は `.claude/agents/<name>.md`（frontmatter は `name` / `description` / `tools` / `model` / `color`）。
同時に `.mcp.json` へ `playwright-test` サーバ（`npx playwright run-test-mcp-server`、Windows は `cmd /c` 経由）が書かれる。

Codex 向けは `.codex/agents/<snake_case>.toml` で、ハイフンを `_` に変換し、`edit` の有無で
`sandbox_mode` を `workspace-write` / `read-only` に切り替える。
移植性を考えるなら、ツール名の直書きより抽象名（`search` / `edit`）を優先する。

## 4. 指定できる MCP ツール

`tools:` に書ける `playwright-test/*` の実体は `mcp-tools/` にある。存在しない名前を書いても無言で無効になるため、
足す前に該当ファイルを Grep して確認する。

| ファイル                      | ツール                                                               |
| ----------------------------- | -------------------------------------------------------------------- |
| `mcp-tools/plannerTools.ts`   | `planner_setup_page`, `planner_submit_plan`, `planner_save_plan`     |
| `mcp-tools/generatorTools.ts` | `generator_setup_page`, `generator_read_log`, `generator_write_test` |
| `mcp-tools/testTools.ts`      | `test_list`, `test_run`, `test_debug`                                |
| `mcp-tools/testTool.ts`       | ツール定義の共通型（`TestTool`）。個別ツールではない                 |

ブラウザ操作系（`browser_*`）は planner / generator の frontmatter に並んでいるものをコピーするのが確実。
