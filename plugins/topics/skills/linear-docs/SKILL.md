---
name: linear-docs
description: Use when answering questions about Linear, the linear.app issue tracker and product planning tool — issues, projects, cycles, initiatives, roadmaps, triage, intake, views, labels, workflows, SLAs, customer requests, Linear Agents and automation, integrations (GitHub, GitLab, Slack, Zendesk, etc.), workspace administration, importers, the Linear GraphQL API, the @linear/sdk TypeScript SDK, webhooks, OAuth apps, agent development, and the Linear MCP server. Grounds answers in the latest official Linear documentation instead of training-data memory. Not for linear algebra or other uses of the word "linear".
allowed-tools: Bash(python ${CLAUDE_SKILL_DIR}/*.py *) Bash(uv run ${CLAUDE_SKILL_DIR}/*.py *)
# スキル起動時に linear.app/llms.txt の索引スナップショットを取得する（24時間freshness、--forceで再取得）。
# network access to linear.app (and raw.githubusercontent.com for the GraphQL schema) is required.
meta:
  tag: []
  requires_repo_tools: aim
  requires_env: none
  dependencies: requests, typer, uv
  requires_install: none
  requires_hooks: none
  requires_skills: none
  status: experimental
  description: Linear documentation index snapshot (linear.app/llms.txt) plus per-page .md fetch, on-demand GraphQL schema and changelog fetch
  version: 1.0.0
---

!`uv run "${CLAUDE_SKILL_DIR}/webref_cli.py" download`

# Linear 最新ドキュメント参照

Linear（linear.app のイシュートラッカー・プロダクト計画ツール）の使い方と、開発者向け API（GraphQL API・TypeScript SDK・Webhooks・OAuth・エージェント開発・MCP サーバー）に関する質問に、学習データの記憶ではなく `linear.app` の最新ドキュメントを根拠に回答する。

このスキルはドキュメント参照用。Linear のイシューを実際に作成・更新するのは対象外（Linear 公式の MCP サーバー等の役割）。

## 索引と本文の取り方

- `output/llms.txt`: Linear 公式のエージェント向け索引（約250行）。リンクはすべて `https://linear.app/...md` 形式で、そのまま本文取得に使える
  - `## Documentation`: ユーザー向けドキュメント（約105ページ）。`###` で Getting started / Intake / Planning / Issues and cycles / Reviews / Agents and automation / Insights and outcomes / Working in Linear / Integrations / Workspace management / Importers に分類され、子ページは2スペースのインデント
  - `## Developers`: 開発者向けドキュメント（約26ページ）。GraphQL API / Authentication / Agents / TypeScript SDK / Guides
  - `## Website`: マーケティング・会社情報のページ。通常は使わない
- 各ページ本文は URL 末尾に `.md` を付けて取得できる（llms.txt 冒頭の公式案内）。`fetch-page` がこれを行う
- GraphQL スキーマ（SDL）と Changelog は索引に含めず、必要なときだけ取得する（後述）

## 手順

1. **ページを探す**

   `output/llms.txt` をキーワードで Grep する（全体 Read も可能な大きさだが、まず Grep）。使い方の質問は `## Documentation`、API・SDK・連携アプリ開発の質問は `## Developers` 節のヒットを使う。分類が分からないときは `^###` を Grep して見出し一覧から当たりを付ける。

2. **本文を取得する**

   ```sh
   uv run "${CLAUDE_SKILL_DIR}/webref_cli.py" fetch-page docs/triage developers/graphql
   ```

   - 引数は llms.txt のリンク URL（`.md` 付きのまま可）、または `docs/<slug>` / `developers/<slug>` のパス
   - `output/temp/<slug>.txt` に全文が書き出され、6000文字を超えるページは `aim` で要約した `output/temp/<slug>.summary.md` も作られる（要約に失敗しても全文へフォールバックし、全文パスは必ず印字される）
   - 要約がある場合は要約を先に読み、手順・設定項目・GraphQL のクエリ例が要る箇所だけ全文を Read/Grep する
   - 各ページ先頭の共通行「> For agents: connect to the Linear MCP server ...」は取得時に除去される。全ページ共通の案内であり、そのページの内容として扱わない

3. **回答する**

   - 取得した本文に基づいて回答し、参照した URL（保存ファイルの frontmatter の `source`、例: `https://linear.app/docs/triage`）を明示する
   - 機能名・プランごとの可否・設定場所は変わりやすい。記憶で答えず取得した現行の記述を使う（プランの違いは `docs/billing-and-plans`）

## GraphQL API / SDK を扱う場合

- 入口: `uv run "${CLAUDE_SKILL_DIR}/webref_cli.py" fetch-page developers/graphql`（エンドポイント `https://api.linear.app/graphql`、認証、クエリ例）。ページネーション・フィルタ・レート制限・Webhooks は `## Developers` の各ページ
- 型・フィールド・引数の正確な名前はスキーマで確認する:

  ```sh
  uv run "${CLAUDE_SKILL_DIR}/webref_cli.py" schema
  ```

  `output/temp/schema.graphql`（約1.4MB、24時間 freshness、gitignore）に保存される。**全体を Read せず**、`type Issue `・`input IssueCreateInput`・`issueCreate(` のように Grep し、ヒット行の前後だけ読む

- `@linear/sdk` は `developers/sdk*.md`（Getting started / Fetching & modifying data / Errors / Webhooks / Migrating）を `fetch-page` する。SDK のメソッドはスキーマから生成されている
- ワークスペースのデータを変更するミューテーションや API 呼び出しを実際に実行する手順を示すときは、実行前にユーザーの承認を得るよう案内する

## MCP サーバーを扱う場合

- 根拠は `uv run "${CLAUDE_SKILL_DIR}/webref_cli.py" fetch-page docs/mcp`。エンドポイントは `https://mcp.linear.app/mcp`、読み取り専用は `https://mcp.linear.app/mcp/readonly`（いずれも取得したページで現行値を確認してから答える）
- クライアント別の設定（Claude / Claude Code / Codex / Cursor / VS Code / Windsurf / Zed など）は同じ `docs/mcp` ページの `### <クライアント名>` 節にある。全文を Grep して該当節だけ読む。MCP クライアントとして他サーバーを Linear に接続する話は `docs/connect-mcp-servers`
- MCP 経由でイシュー等を作成・変更する操作は、実行前にユーザーの承認を得る

## 最近の変更を聞かれた場合

```sh
uv run "${CLAUDE_SKILL_DIR}/webref_cli.py" fetch-page changelog
```

`https://linear.app/changelog.md`（最新 約20件のエントリ、約75KB）を取得する。要約が作られるので、まず要約を読み、日付や機能名を全文で Grep して確認する。それより古い変更は対象外として、その旨を伝える。

## 補足

- 索引のダウンロードは24時間以内ならスキップされる（`--force` で再取得: `uv run "${CLAUDE_SKILL_DIR}/webref_cli.py" download --force`）
- 索引にページが見つからないときは、URL を推測して `fetch-page` してよい（存在しないページは 404 で失敗する）。推測で取れなかった内容を記憶で補わない
- `output/temp/` は都度上書きされる作業置き場（gitignore 済み）
