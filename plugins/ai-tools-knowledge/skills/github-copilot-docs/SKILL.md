---
name: github-copilot-docs
description: Use when answering questions about GitHub Copilot (Copilot Chat, Copilot CLI, coding agent / cloud agent, agent skills, custom instructions, MCP integration, plans, billing, model access, IDE setup, troubleshooting, etc.). Grounds answers in the latest official docs (docs.github.com) instead of training-data memory, which may be stale.
meta:
  tag: []
  requires_repo_tools: none
  requires_env: none
  dependencies: python3, curl
  requires_install: none
  requires_hooks: none
  requires_skills: none
  status: stable
  description: no description
  version: 1.0.5
---

# GitHub Copilot 最新ドキュメント参照

GitHub Copilot に関する質問に、学習データの記憶ではなく `docs.github.com` の最新ドキュメントを根拠に回答するためのスキル。

## 注意: llms-full.txt は存在しない

`code.claude.com` と異なり、`docs.github.com` は `llms-full.txt`（全ページ本文の連結ファイル）を公開していない（404）。`llms.txt` は GitHub Docs 全体（Copilot 以外のセクションも含む）へのリンクと短い説明のみを含むインデックスなので、本文が必要な場合はページごとに WebFetch で取得する。

## 手順

`output/llms.txt` が存在しない、または更新が必要な場合は、このスキルのディレクトリを作業ディレクトリにして `python download_copilot_reference.py` を実行する。ネットワークアクセスと書き込みを伴うため、実行前に内容を確認する。

1. **関連箇所を探す**

   - `./output/llms.txt` を Grep/Read して、質問に関連しそうなページの URL と短い説明を特定する
   - `## GitHub Copilot` セクションが本題の中心だが、`## Building with GitHub, for coding agents and automation`（MCP・Copilot CLI・cloud agent 関連）など他セクションに関連ページがあることもある

2. **該当ページの本文を取得する**（説明文だけで回答できない場合）

   - 見つけた URL を WebFetch で取得する
   - 複数ページにまたがりそうな質問なら、関連しそうな URL を複数 WebFetch してよい
   - `./output/llms.txt` の説明にある `docs.github.com/api/article/body?pathname=...` エンドポイントを使うと、該当ページの本文を Markdown で直接取得できる（例: `curl "https://docs.github.com/api/article/body?pathname=/en/copilot/get-started/quickstart"`）

3. **回答する**

   - 取得した本文に基づいて回答し、参照した URL を明示する
   - `./output/llms.txt` に該当ページが見つからない場合は、その旨を伝えた上で `https://docs.github.com/en/copilot` 配下や `https://docs.github.com/api/search/v1?query=...` を使って直接探索してもよい

## 補足

- スクリプトはこのスキルのディレクトリを基準に `./output/` を読み書きする
- ダウンロードは 24 時間以内に取得済みならスキップされる（`--force` で強制再取得）
