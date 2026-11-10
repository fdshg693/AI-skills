---
name: vercel-docs
description: Use when answering questions about Vercel — deployments, builds, Vercel Functions and Fluid compute, runtimes, Routing Middleware, CDN/caching/ISR, environment variables, domains/DNS, the Vercel CLI, the Vercel REST API/SDK, AI Gateway, Sandbox, storage (Blob/KV/Edge Config/Postgres), observability, firewall/WAF, and other products documented on vercel.com/docs. Grounds answers in the latest official Vercel documentation instead of training-data memory, which may be stale or predate product changes, aliases, and deprecations.
allowed-tools: Bash(python ${CLAUDE_SKILL_DIR}/*.py *) Bash(uv run ${CLAUDE_SKILL_DIR}/*.py *)
# スキル起動時に vercel.com/docs の索引スナップショットを取得する（24時間freshness、--forceで再取得）。
# network access to vercel.com is required.
meta:
  tag: []
  requires_repo_tools: aim
  requires_env: none
  dependencies: requests, typer, uv
  requires_install: none
  requires_hooks: none
  requires_skills: none
  status: stable
  description: Vercel documentation snapshot (llms.txt / products.md / sitemap.md / taxonomy.json) plus per-page .md fetch from vercel.com
  version: 1.0.1
---

!`uv run "${CLAUDE_SKILL_DIR}/webref_cli.py" download`

# Vercel 最新ドキュメント参照

Vercel（ホスティング、デプロイ、Functions、CDN、CLI、REST API、AI Gateway、Sandbox、Storage などの製品）に関する質問に、学習データの記憶ではなく `vercel.com/docs` の最新ドキュメントを根拠に回答する。

## 索引と本文の取り方

- `output/products.md`: 全製品の一覧（約50行）。質問がどの製品かを最初に特定するために Read する
- `output/llms.txt`: Vercel がエージェント向けに用意した短い案内（CLI / MCP / API / 主要索引への導線）。Read 可
- `output/sitemap.md`: 全ドキュメントページの意味的索引（`- [Title](/docs/...) | Type: ... | Lastmod: ... | Summary: ... | Prerequisites: ... | Topics: ...` の約1336エントリ、約400KB）。**全体を Read せず Grep する**
- `output/taxonomy.json`: 正規の製品名・別名・非推奨/退役（`aliases` / `status` / `supersededBy` / `retiredAt`）。表記ゆれ・旧名の確認に使う
- `output/llms-full.txt`: 全ドキュメント + REST API リファレンスの連結ダンプ（約9.6MB、gitignore）。**通常は使わない。全体を Read しない**
- 各ページ本文は URL 末尾に `.md` を付けて取得できる（公式の指定）。`fetch-page` がこれを行う

Vercel AI SDK（`ai` パッケージ、ai-sdk.dev）は別スキル `ai-sdk-docs` の担当。AI SDK の API はそちらで確認する。

## 手順

1. **どの製品・領域かを特定する**

   - まず `output/products.md` を Read して製品の当たりを付ける
   - エージェント向けの導線（CLI、MCP、API、主要索引）は `output/llms.txt` を Read する

2. **ページを探す**

   `output/sitemap.md` をキーワードで Grep する（各エントリは URL と Summary を含む行なので、ヒットした行からパスが分かる）。

   - REST API のエンドポイントは `- [GET /... ](/docs/rest-api/...)` 形式で載っている。HTTP メソッドやパスで検索できる
   - `Topics:` のタグ（例: `rest api, domains`）や `Type:`（Conceptual / How-to / Reference / Tutorial）で絞り込める
   - 製品名が揺れる場合は `output/taxonomy.json` の `aliases` で正規名を確認してから検索する

3. **本文を取得する**

   ```sh
   uv run "${CLAUDE_SKILL_DIR}/webref_cli.py" fetch-page docs/functions docs/environment-variables
   ```

   - 引数は sitemap.md の `/docs/...` パス、full URL、または末尾 `.md` 付き URL（`.md` は省略可、`?from=` などのクエリは無視される）
   - `output/temp/<slug>.txt` に全文が書き出され、6000文字を超えるページは `aim` で要約した `output/temp/<slug>.summary.md` も作られる（要約に失敗しても全文へフォールバックし、全文パスは必ず印字される）
   - 要約がある場合は要約を先に読み、コード例・設定キー・既定値が要る箇所だけ全文を Read/Grep する

4. **回答する**

   - 取得した本文に基づいて回答し、参照した URL（ページ frontmatter の `canonical_url`、または `https://vercel.com/docs/...`）を明示する
   - 学習データの古い情報（廃止された `vercel.json` スキーマ、Edge Functions / Edge Middleware、Vercel KV / Postgres など）で答えず、取得した現行の仕様を使う
   - 取得したページの frontmatter には `prerequisites` / `related` がある。関連ページが必要なら `fetch-page` で辿る

## REST API を扱う場合

- 概要・認証: `uv run "${CLAUDE_SKILL_DIR}/webref_cli.py" fetch-page docs/rest-api docs/rest-api/getting-started`
- 機械可読な OpenAPI 仕様: `https://vercel.com/openapi.json`（`fetch-page` ではなく直接取得し、必要な operation だけ確認する。巨大なため全文をコンテキストへ流さない）
- エンドポイント個別ページは sitemap.md の `/docs/rest-api/...` から `fetch-page` する
- アカウントやリソースを変更する操作は、実行前にユーザーの承認を得る（Vercel 公式の案内に合わせる）

## 補足

- ダウンロードは24時間以内ならスキップされる（`--force` で再取得: `uv run "${CLAUDE_SKILL_DIR}/webref_cli.py" download --force`）
- `output/temp/` は都度上書きされる作業置き場（gitignore 済み）。`output/llms-full.txt` も gitignore
- 索引が古い/欠けている疑いがあるときだけ、`uv run "${CLAUDE_SKILL_DIR}/webref_cli.py" download --include-full` でダンプを取得し、`head_limit` 付きで Grep して見つけたパスを `fetch-page` で取り直す。ダンプの行を本文代わりにしない
- 対象は `vercel.com/docs` と REST API リファレンス。Knowledge Base / Blog / Changelog / Academy は別索引（`/kb/sitemap.md` 等）。必要な場合だけ `fetch-page kb/sitemap --no-summarize` のように取得する（索引は要約すると一覧性が失われるため `--no-summarize` を付ける）
