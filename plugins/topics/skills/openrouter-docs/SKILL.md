---
name: openrouter-docs
description: Use when answering questions about OpenRouter (openrouter.ai) — the unified API for routing requests across many LLM providers/models, its Agent SDK, Client SDKs (TypeScript/Python/Go), REST API reference, model routing/variants (:nitro, :online, :thinking, etc.), plugins, guardrails, presets, workspaces, pricing/BYOK, or integrating OpenRouter with coding agents (Claude Code, Cursor, Codex CLI, etc.). Grounds answers in the latest official docs (openrouter.ai/docs) instead of training-data memory, which may be stale.
allowed-tools: Bash(python ${CLAUDE_SKILL_DIR}/*.py *)
# !`<command>`を使ってスクリプトを実行することで、確実にコマンドを実行できるようにする。
meta:
  tag: []
  requires_repo_tools: none
  requires_env: none
  dependencies: openrouter.ai/docs
  requires_install: none
  requires_hooks: none
  requires_skills: none
  status: stable
  description: no description
  version: 1.0.6
---

!`python ${CLAUDE_SKILL_DIR}/download_openrouter_reference.py`

# OpenRouter 最新ドキュメント参照

OpenRouter (openrouter.ai) に関する質問に、学習データの記憶ではなく `openrouter.ai/docs` の最新ドキュメントを根拠に回答するためのスキル。

## 頻出トピックのリファレンス

以下4トピックは`references/`に要約を用意している。質問がこれに該当する場合はまずそちらを読む。数値・料率・対応先リスト・Beta状態など変わりやすい情報は、断定的に答える前に各ファイル内のSourceパスを[手順](#手順)の抽出スクリプトで再取得して裏取りすること。

- [references/why-openrouter.md](references/why-openrouter.md) — OpenRouterを経由してモデルを使う意味（統一API、BYOK、独自機能、プロバイダ直叩きとの違い）
- [references/server-tools.md](references/server-tools.md) — Server Toolsの意味・使い方（Plugins/ユーザー定義Toolとの違い、利用可能ツール一覧）
- [references/observability.md](references/observability.md) — Observability（Input & Output Logging、Broadcast、Router Metadata）
- [references/beta-files-classifiers.md](references/beta-files-classifiers.md) — Beta機能: Files / Classifiers
- [references/models-pricing-benchmarks.md](references/models-pricing-benchmarks.md) — Models API（`/api/v1/models`一覧・単一取得・プロバイダ別`endpoints`）での価格・ベンチマーク（Design Arena / Artificial Analysis）取得

## 手順

1. **関連箇所を探す**

   - 上記4トピックでカバーされていない、あるいはより詳細が必要な質問はここから: まず `${CLAUDE_SKILL_DIR}/output/llms.txt` を Grep/Read して、質問に関連しそうなページの URL・パスを特定する
   - セクション見出し（`## Docs` 配下のカテゴリ: `agent-sdk/`, `api/reference/`, `client-sdks/`, `cookbook/`, `guides/features/`, `guides/routing/` など）で大まかなカテゴリを絞り込める
   - 詳細な本文が必要なら `${CLAUDE_SKILL_DIR}/output/llms-full.txt` を Grep して該当セクションのおおよその位置を掴む

2. **該当セクションを抽出する**（本文が長い場合に推奨）

   ```bash
   python ${CLAUDE_SKILL_DIR}/extract_doc_section.py <URL または パス> [<URL または パス>...]
   ```

   - 例: `python ${CLAUDE_SKILL_DIR}/extract_doc_section.py guides/features/tool-calling guides/routing/provider-selection`
   - パスは `llms.txt` に載っているリンクの `https://openrouter.ai/docs/` 以降（末尾の `.md` は省略可）をそのまま渡す
   - `${CLAUDE_SKILL_DIR}/output/temp/<slug>.txt` に該当セクションだけが書き出されるので、それを Read して内容を確認する

3. **回答する**

   - 抽出した本文に基づいて回答し、参照した URL（`Source:` 行）を明示する
   - `${CLAUDE_SKILL_DIR}/output/llms-full.txt` に該当ページが見つからない場合は、その旨を伝えた上で WebFetch 等で `openrouter.ai/docs` を直接参照してもよい

## 補足

- スクリプトは`${CLAUDE_SKILL_DIR}/output/`を読み書きする
- `${CLAUDE_SKILL_DIR}/output/temp/` は作業用の一時ファイル置き場（都度上書きされる想定）
- OpenRouter のドキュメントパスは `client-sdks/go/sdks/chat/README` `client-sdks/python/sdks/chat/README` のように末尾（`README` など）が重複するものが多数ある。`extract_doc_section.py` の抽出キー・出力ファイル名は URL パス全体（`/` を `__` に置換）を使っているため、末尾だけの曖昧な指定は避け、`llms.txt` で見つけた完全なパスを渡すこと
