---
name: litellm-docs
description: Use when answering questions about LiteLLM SDK or LiteLLM Proxy/Gateway documentation — routing and load balancing, providers and model configuration, authentication, budgets, guardrails, observability, pass-through endpoints, or API usage. Grounds answers in current official pages under docs.litellm.ai/docs instead of training-data memory, which may be stale.
allowed-tools: Bash(python ${CLAUDE_SKILL_DIR}/*.py *) Bash(uv run ${CLAUDE_SKILL_DIR}/*.py *)
# The URL index is refreshed at skill startup; network access to docs.litellm.ai is required.
# The pinned Markdown fallback is used only when a rendered page is insufficient.
meta:
  tag: []
  requires_repo_tools: none
  requires_env: none
  dependencies: requests, typer, uv
  requires_install: none
  requires_hooks: none
  requires_skills: none
  status: stable
  description: Current LiteLLM technical documentation indexed from the official sitemap
  version: 1.0.1
---

!`uv run "${CLAUDE_SKILL_DIR}/webref_cli.py" download-index`

# LiteLLM 最新ドキュメント参照

LiteLLM SDK、LiteLLM Proxy/Gateway、およびその公式技術ドキュメントに関する質問へ、現在の公式ページを根拠に回答する。対象URLは厳密に `https://docs.litellm.ai/docs/` 配下だけであり、リリースノート、ブログ、タグ、会社情報などはこのSkillの対象外。

## 索引と本文の取り方

- `${CLAUDE_SKILL_DIR}/output/docs-url-tree.md`: 主要領域を把握するためのコンパクトなパスツリー。最初にReadする
- `${CLAUDE_SKILL_DIR}/output/docs-urls.md`: sitemapから生成した完全な `/docs/` URL一覧。全体をReadせず、質問の語でGrepする
- `${CLAUDE_SKILL_DIR}/output/selection.json`: `select-urls`が作る一時manifest。取得対象を明示するためだけに使う
- `${CLAUDE_SKILL_DIR}/output/temp/`: `fetch-pages`が選択済みページ本文を書き出す作業領域。本文全体を直接コンテキストへ流し込まず、必要なファイルだけ読む

`llms.txt` と `llms-full.txt` は現行技術文書の索引として使わない。公式 sitemap が現在の公開ルートを列挙し、`llms.txt` は `/docs/` の対象が少なく、`llms-full.txt` はリリース履歴を多く含みページ境界を安全に判定できないためである。

## 手順

1. **関連領域を特定する**

   `${CLAUDE_SKILL_DIR}/output/docs-url-tree.md` をReadし、`providers`、`proxy`、`routing`、`observability`、`pass_through`、`completion` などの大分類を確認する。

2. **候補URLを絞る**

   `${CLAUDE_SKILL_DIR}/output/docs-urls.md` を質問のキーワードでGrepする。必要なら `providers/` や `proxy/` などのパスも同時に絞る。完全な一覧を毎回Readしない。

3. **取得対象をmanifestに固定する**

   ```sh
   uv run "${CLAUDE_SKILL_DIR}/webref_cli.py" select-urls --keyword routing --limit 8
   ```

   必要に応じて `--keyword`、`--exclude-keyword`、`--include-prefix`、`--exclude-prefix`、`--limit` を追加する。URL一覧から候補を見つけた後、質問に必要な最小限のURLだけを選ぶ。

4. **選択済みページだけ取得する**

   ```sh
   uv run "${CLAUDE_SKILL_DIR}/webref_cli.py" fetch-pages --manifest "${CLAUDE_SKILL_DIR}/output/selection.json"
   ```

   manifestまたは明示的な `--url` に含まれないページを推測して取得・クロールしない。スクリプトはHTTPS、`docs.litellm.ai`、`/docs/` prefixをリダイレクト後にも再検証する。

5. **回答する**

   取得した本文に基づき、参照した正規URL（`https://docs.litellm.ai/docs/...`）を明示する。SDKとProxyで手順が異なる場合は、該当ページの区別を保つ。現行ページで不足する場合だけ、次の固定コミットのMarkdownソースを補助的に参照する。

   `BerriAI/litellm-docs@3c0d2ef3ef4890c705577eb74a79fc473139e829`

   ```text
   https://raw.githubusercontent.com/BerriAI/litellm-docs/3c0d2ef3ef4890c705577eb74a79fc473139e829/docs/<path>.md
   ```

   fallbackは必要な単一ファイルに限定し、リポジトリ全体をclone・snapshotしない。回答の主引用は可能な限り `docs.litellm.ai/docs/...` の現行ページとする。

## 補足

- ダウンロードは `fetched_at` が24時間以内ならスキップされる。強制更新は `uv run "${CLAUDE_SKILL_DIR}/webref_cli.py" download-index --force`。
- URL一覧とツリーは生成物としてコミットする。raw sitemap、manifest、取得本文は作業データでありコミットしない。
- sitemapにないURLや `/docs/` prefix外のURLを、LiteLLM公式技術文書として扱わない。
