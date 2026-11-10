---
name: ai-sdk-docs
description: Use when answering questions about the Vercel AI SDK (the `ai` package, `@ai-sdk/*` providers, AI SDK Core/UI) — generateText/streamText, generateObject/streamObject, tools, ToolLoopAgent, useChat/useCompletion/useObject, embeddings, image/speech/transcription, providers, AI Gateway, or React/Next.js/Vue/Svelte/Node integrations. Grounds answers in the latest official docs (ai-sdk.dev) instead of training-data memory, which may be stale.
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
  description: Official AI SDK docs snapshot (llms.txt / sitemap.md) plus search-docs and per-page .md fetch from ai-sdk.dev
  version: 1.0.1
---

!`python "${CLAUDE_SKILL_DIR}/webref_cli.py" download`

# Vercel AI SDK 最新ドキュメント参照

Vercel AI SDK（`ai` / `@ai-sdk/*`、[ai-sdk.dev](https://ai-sdk.dev/llms.txt)）に関する質問に、学習データの記憶ではなく公式ドキュメントを根拠に回答する。

## 注意: 索引と本文の取り方

- `${CLAUDE_SKILL_DIR}/output/llms.txt`: 公式の短い案内（検索エンドポイントと起点ページ）。約50行なのでそのまま Read してよい
- `${CLAUDE_SKILL_DIR}/output/sitemap.md`: 全ページのパス一覧（`/docs/...` `/providers/...` `/cookbook/...`）。Grep 用
- `${CLAUDE_SKILL_DIR}/output/llms-full.txt`: 全文連結ダンプ（数MB）。`# タイトル` / `Source: URL` のページ境界が無いのでセクション抽出は使わない。**全体を Read しない**
- 各ページ本文は URL 末尾に `.md` を付けて取れる（公式の指定）。`fetch-page` がその取得をする

`npx skills add vercel/ai` は公式の実装スキルであり、このスキルとは別物。API・現行シグネチャの確認はこのスキルで行う。

## 手順

1. **関連ページを探す**

   - 起点が分かっている（Getting Started、AI SDK Core/UI、Agents、Providers、Reference）なら `${CLAUDE_SKILL_DIR}/output/llms.txt` を Read する
   - API名・機能名で探すなら検索する:

     ```sh
     python "${CLAUDE_SKILL_DIR}/webref_cli.py" search "ToolLoopAgent"
     ```

   - パスのカテゴリが分かっているなら `${CLAUDE_SKILL_DIR}/output/sitemap.md` を Grep する（例: `generate-text`、`use-chat`、`ai-gateway`）

2. **本文を取得する**

   ```sh
   python "${CLAUDE_SKILL_DIR}/webref_cli.py" fetch-page docs/agents docs/reference/ai-sdk-core/tool-loop-agent
   ```

   - 引数は検索結果の URL、sitemap の `/docs/...`、または末尾 `.md` 付き URL。`.md` は省略可
   - `${CLAUDE_SKILL_DIR}/output/temp/<slug>.txt` に全文が書き出される。6000文字を超えるページは `aim` で要約した `${CLAUDE_SKILL_DIR}/output/temp/<slug>.summary.md` も作る（失敗時は全文ファイルへフォールバック。要約しても全文パスは必ず印字される）
   - 要約がある場合は要約を先に読み、コード例・引数・既定値が要る箇所だけ全文を Read/Grep する

3. **回答する**

   - 取得した本文に基づいて回答し、参照した URL（`Source:` 行、`.md` を除いた https://ai-sdk.dev/...）を明示する
   - 学習データにある古い API（`experimental_useChat`、Assistant 時代の形、廃止済みのプロバイダ import など）で答えず、取得した現行のシグネチャ・パッケージ名を使う
   - 検索にも sitemap にも無い場合だけ `${CLAUDE_SKILL_DIR}/output/llms-full.txt` を Grep する（`head_limit` 付き）。ヒットしたら近くの `#` 見出し / `title:` を sitemap と照合し、見つかったパスを `fetch-page` する。ダンプの行を本文代わりにしない

## 補足

- ダウンロードは24時間以内ならスキップされる（`--force` で再取得: `python "${CLAUDE_SKILL_DIR}/webref_cli.py" download --force`）
- `output/temp/` は都度上書きされる作業置き場（gitignore 済み）
- `output/llms-full.txt` も gitignore。スキル起動時の download がキャッシュする
- 公式検索: `https://ai-sdk.dev/api/search-docs?q=...`（`search` サブコマンドがこれを叩く）
