---
name: langchain-docs
description: Use when answering questions about LangChain, LangGraph, LangSmith, or langchain-ai's Python/JavaScript SDKs and integration packages (chat models, agents, tools, retrieval/RAG, checkpointers, MCP adapters, etc.) — API signatures, parameters, return types, which package/class to use, or deprecated-vs-current patterns (e.g. LLMChain/AgentExecutor vs create_agent). Grounds answers in the latest official API reference (reference.langchain.com) instead of training-data memory, which may be stale.
allowed-tools: Bash(python ${CLAUDE_SKILL_DIR}/*.py *)
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
  version: 1.0.3
---

!`python "${CLAUDE_SKILL_DIR}/webref_cli.py" download`

# LangChain API リファレンス参照

LangChain / LangGraph / LangSmith およびその周辺パッケージ（`langchain-openai`、`@langchain/core` 等の統合パッケージ)に関する質問に、学習データの記憶ではなく `reference.langchain.com` の最新 API リファレンスを根拠に回答するためのスキル。

## 注意: 索引はあるが全文ダンプではない

`reference.langchain.com` は `llms.txt` と `llms-full.txt` の両方を公開しているが、他サイト（`openrouter.ai` 等）の `llms-full.txt` と異なり **どちらも「索引」であって各ページの本文そのものは含まない**。

- `${CLAUDE_SKILL_DIR}/output/llms.txt`: **パッケージ単位**の索引。Python/JavaScript の各パッケージ（`langchain`, `langchain_core`, `langgraph`, `@langchain/core` 等）ごとに1エントリ、概要の説明文つき。約170行で全パッケージを一望できる規模なので、抜粋(excerpt)は作っていない
- `${CLAUDE_SKILL_DIR}/output/llms-full.txt`: **シンボル単位**の索引（クラス/関数/属性を1行1件、`(attribute)`/`(class)`/`(function)` 等の種別つきでリンク）。ページ末尾に `This listing was truncated due to size limits.` とある通り**全パッケージ分は載っていない**（`langchain`, `langchain_core`, `langchain_mcp_adapters` の途中まで）。載っていないパッケージ/シンボルは索引に無くても実在しうる

## 手順

1. **関連パッケージ/シンボルを探す**

   - まず `${CLAUDE_SKILL_DIR}/output/llms.txt` を Grep/Read し、質問に関係するパッケージ（`## Python Packages` / `## JavaScript Packages` セクション配下)を特定する
   - 具体的なクラス名・関数名が分かっているなら `${CLAUDE_SKILL_DIR}/output/llms-full.txt` を Grep する。ヒットすれば、その行のリンクが直接そのシンボルのURL(`.md`)
   - `llms-full.txt` にヒットしない場合(truncateされている、または元々索引に無いシンボル)は、下記のURLパターンに沿って自分でURLを組み立てて構わない(index段階の網羅性を前提にしない)

2. **本文を取得する**

   - 特定したURLをそのまま WebFetch する(すでに`.md`ならそのまま、`.md`が無ければ末尾に`.md`を付ける)
   - URLパターン(`reference.langchain.com/skill.md` に記載の公式パターン):

     ```text
     https://reference.langchain.com/{language}/{package}.md                    # パッケージ概要
     https://reference.langchain.com/{language}/{package}/{Symbol}.md           # シンボル本体
     https://reference.langchain.com/{language}/{package}/{Symbol}/{member}.md  # ネストしたメンバー(メソッド等)
     ```

     `{language}` は `python` / `javascript`（`java`/`go`向けページも存在する)。クラス名・メソッド名はドット区切りで書かれることが多いが、URLではスラッシュに変換する(例: `RunnableSequence.invoke` → `.../RunnableSequence/invoke.md`)

3. **回答する**

   - 取得した本文に基づいて回答し、参照したURLを明示する
   - パッケージ名の言語差に注意する: Python は `langchain-core`(ハイフン)、JavaScript は `@langchain/core`(スコープ付きパッケージ)のように命名規則が異なる。API は似ているが同一ではないため、質問がどちらの言語かを取り違えない

## 補足

- スクリプトは `${CLAUDE_SKILL_DIR}/output/` を読み書きする。ダウンロードは24時間以内に取得済みならスキップされる(`--force`で強制再取得、`python "${CLAUDE_SKILL_DIR}/webref_cli.py" download --force`)
- **非推奨パターンに注意**: `LLMChain` → `create_agent`/`create_deep_agent`、`ConversationChain` → `create_agent`(履歴付き)、直接の `AgentExecutor` → `create_agent`/`create_deep_agent`、LCEL チェーンの新規利用 → `create_agent` を優先、が公式の推奨(`reference.langchain.com/skill.md` より)。学習データにある古いパターンで回答しないよう、ユーザーの質問がこれらの非推奨パターンに触れている場合は現行APIへの置き換えを併記する
- **概念的なガイド/チュートリアルはこのスキルの対象外**。`reference.langchain.com` は API リファレンスのみで、LangChain/LangGraph/Deep Agents/LangSmith の使い方ガイドは `docs.langchain.com`(製品ごとに別の skill file が `docs.langchain.com/.well-known/agent-skills/index.json` に公開されている)にある。ガイド寄りの質問が来たら、その旨を伝えた上で WebFetch で `docs.langchain.com` を直接参照してよい
