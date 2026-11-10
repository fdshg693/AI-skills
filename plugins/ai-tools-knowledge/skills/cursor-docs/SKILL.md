---
name: cursor-docs
description: Use when answering questions about Cursor (the AI code editor) — features, settings, Agent mode, Plan mode, rules, skills, subagents, hooks, MCP, cloud agents, models & pricing, integrations, etc. Grounds answers in the latest official docs (cursor.com/docs) instead of training-data memory, which may be stale.
allowed-tools: Bash(python skills/plugins/ai-tools-knowledge/skills/cursor-docs/*.py *)
# !`<command>`を使ってスクリプトを実行することで、確実にコマンドを実行できるようにする。
meta:
  tag: []
  requires_repo_tools: none
  requires_env: none
  dependencies: none
  requires_install: none
  requires_hooks: none
  requires_skills: none
  status: stable
  description: no description
  version: 1.0.5
---

!`python "${CLAUDE_SKILL_DIR}/download_cursor_reference.py"`

# Cursor 最新ドキュメント参照

Cursor（AIコードエディタ）に関する質問に、学習データの記憶ではなく `cursor.com/docs` の最新ドキュメントを根拠に回答するためのスキル。

## 注意: llms-full.txt は存在しない

`cursor.com` は `llms-full.txt`（全ページ本文の連結ファイル）を公開していない（マーケティングのトップページが返るだけで本文ダンプではない）。`llms.txt` はセクション見出し（`## Get Started` `## Agent` `## customizing` `## cloud-agents` `## Integrations` など）でグループ化された各ページ URL の階層インデックスのみで、説明文は付いていない。

**ただし各 URL は末尾が `.md` になっている**（例: `https://cursor.com/docs/agent/overview.md`）。これは加工済みの Markdown 本文がそのまま返るエンドポイントなので、WebFetch すればHTMLのノイズなしで本文を取得できる。

## 手順

1. **関連箇所を探す**

   - `./output/llms.txt` を Grep/Read して、質問に関連しそうなページの URL を特定する
   - セクション見出し（`## Get Started` `## Agent` `## customizing` `## cloud-agents` `## Integrations` など）で大まかなカテゴリを絞り込める

2. **該当ページの本文を取得する**

   - 見つけた `.md` で終わる URL を WebFetch で取得する
   - 複数ページにまたがりそうな質問（例: Agent のツール一覧など、親ページの下にネストされた項目がある場合）は、関連しそうな URL を複数 WebFetch してよい

3. **回答する**

   - 取得した本文に基づいて回答し、参照した URL を明示する
   - `./output/llms.txt` に該当ページが見つからない場合は、その旨を伝えた上で `https://cursor.com/docs` 配下や `https://cursor.com/changelog` を WebFetch 等で直接探索してもよい

## 補足

- スクリプトはこのディレクトリ（`skills/plugins/ai-tools-knowledge/skills/cursor-docs/`）を基準に `output/` を読み書きする
- ダウンロードは24時間以内に取得済みならスキップされる（`--force` で強制再取得）
- `output/llms.txt` は生成物だが、ネットワークが使えない環境でも索引だけは参照できるようリポジトリにコミットして同梱している（本文自体はコミットされないため、本文が必要な質問には結局 WebFetch が要る）
