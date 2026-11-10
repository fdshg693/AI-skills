---
name: apify-docs
description: Use when answering questions about Apify (apify.com / docs.apify.com) — Actors (serverless scraping/automation programs), Apify Store and finding an Actor for a task, running Actors via the REST API v2 / `apify-client` (JS/Python) / Apify MCP server, building Actors with the Apify SDK (JS/Python) and Apify CLI (actor.json, input/output/dataset schemas, Standby mode, deployment), storage (datasets, key-value stores, request queues), proxy, schedules/tasks/webhooks, pricing and Actor monetization (pay-per-event, pay-per-result, rental), limits, and integrations (Claude Code, Cursor, LangChain, n8n, Make, Zapier, etc.). Grounds answers in the latest official docs and Store data instead of training-data memory, which may be stale.
allowed-tools: Bash(python ${CLAUDE_SKILL_DIR}/*.py *) Bash(uv run ${CLAUDE_SKILL_DIR}/*.py *)
# !`<command>`を使ってスクリプトを実行することで、確実にコマンドを実行できるようにする。
meta:
  tag: []
  requires_repo_tools: aim
  requires_env: none
  dependencies: requests, typer
  requires_install: none
  requires_hooks: none
  requires_skills: none
  status: stable
  description: Apify docs snapshot (docs.apify.com / apify.com llms.txt + curated excerpt) with per-page .md fetch and public Store search
  version: 1.0.1
---

!`python "${CLAUDE_SKILL_DIR}/webref_cli.py" download`

# Apify 最新ドキュメント参照

Apify（Actor・Apify Store・API・SDK・CLI・MCP サーバー）に関する質問に、学習データの記憶ではなく公式ドキュメントと Store の実データを根拠に回答する。

## 索引ファイル

| ファイル                                        | 中身                                                                                               | 読み方                                          |
| ----------------------------------------------- | -------------------------------------------------------------------------------------------------- | ----------------------------------------------- |
| `${CLAUDE_SKILL_DIR}/output/excerpt.md`         | 主要ページだけの抜粋（各領域の overview / quick start、Actor・storage の概念、MCP・AI 連携）約80件 | **最初に Read する**                            |
| `${CLAUDE_SKILL_DIR}/output/llms.txt`           | docs.apify.com の全索引（API 各エンドポイント、SDK/クライアントのクラス、Academy 含む）約500行     | 抜粋に無いときだけ Grep。全体を Read しない     |
| `${CLAUDE_SKILL_DIR}/output/apify-com-llms.txt` | apify.com 側の索引（Store、料金、MCP サーバー、エージェント向け quickstart `agents.md`）           | Store・料金・エージェント連携の質問で Read する |

`docs.apify.com/llms-full.txt`（全文ダンプ、約45MB、ページ境界マーカーなし）は取得しない。本文は各ページ URL 末尾に `.md` を付けて個別に取る。

## 手順

1. **関連ページを探す**

   - まず `${CLAUDE_SKILL_DIR}/output/excerpt.md` を Read する
   - 無ければ `${CLAUDE_SKILL_DIR}/output/llms.txt` を Grep する（例: `run-sync`, `input-schema`, `webhook`, `ActorClient`, `proxy`）。REST エンドポイント個別ページは `api/v2/<操作名>` 形式
   - 「〜をスクレイピングする Actor はあるか」なら Store を検索する（トークン不要）:

     ```sh
     python "${CLAUDE_SKILL_DIR}/webref_cli.py" search-store "google maps" --limit 5
     ```

     キーワードは目的（"leads"）ではなくサイト・製品名（"google maps", "instagram"）にする

2. **本文を取得する**

   ```sh
   python "${CLAUDE_SKILL_DIR}/webref_cli.py" fetch-page actors/development/actor-definition/input-schema cli/docs/reference
   python "${CLAUDE_SKILL_DIR}/webref_cli.py" fetch-page https://apify.com/agents.md https://apify.com/compass/crawler-google-places
   ```

   - 引数は索引の URL（`.md` 付きのままでよい）、`docs.apify.com/` 以降のパス、または `apify.com` の URL。Store の Actor ページ（`apify.com/<user>/<actor>`）も README・入力・料金込みの Markdown で取れる。他ホストは拒否する
   - `${CLAUDE_SKILL_DIR}/output/temp/<slug>.txt` に全文が書き出される。6000文字を超えるページは `aim` で要約した `<slug>.summary.md` も作る（失敗時は全文を使う）。要約を先に読み、コード例・パラメータ・既定値が要る箇所だけ全文を Read/Grep する

3. **回答する**

   - 取得した本文に基づき、参照 URL（`Source:` 行）を明示する
   - Actor の料金・利用者数・評価は Store 検索や Actor ページの取得時点の値として示す（頻繁に変わる）

## 取り違えやすい点

- Actor を**呼び出す**側のライブラリは `apify-client`（JS / Python）。`apify` パッケージは Actor を**作る** SDK
- "Actor" は Apify のサーバーレスプログラムのことで、AI エージェントではない。常に大文字始まり
- API 認証は `Authorization: Bearer <APIFY_TOKEN>` ヘッダー。トークンをクエリ文字列や回答中のコードに直書きさせない
- コーディングエージェントから Apify を使う方法（MCP サーバー `https://mcp.apify.com`、公式 Agent Skills `apify/agent-skills`、Claude Code 用プラグイン等）は `https://apify.com/agents.md` と excerpt の integrations 節を取得して答える。公式 Agent Skills は Actor 実行・開発用の別物で、このスキルは仕様・API の確認用

## 補足

- 索引は24時間以内ならスキップされる（`python "${CLAUDE_SKILL_DIR}/webref_cli.py" download --force` で再取得）
- `output/temp/` は都度上書きされる作業置き場（gitignore 済み）
- 抜粋の再生成・検証（`generate-excerpt` / `check-excerpt`）はメンテナ向け。手順は同階層の README.md
