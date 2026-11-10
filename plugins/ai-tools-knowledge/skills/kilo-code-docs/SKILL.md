---
name: kilo-code-docs
description: Use when answering questions about Kilo Code (kilo.ai) — the open-source AI coding agent available as a VS Code/JetBrains extension and a CLI/TUI, including its modes (Orchestrator/Code/Architect/Debug/Ask), AI providers (BYOK), MCP integration, settings, KiloClaw (cloud agent gateway), pricing/credits, and troubleshooting. Grounds answers in the latest official docs (kilo.ai/docs) instead of training-data memory, which may be stale.
allowed-tools: Bash(python ${CLAUDE_SKILL_DIR}/*.py *)
# !`<command>`を使ってスクリプトを実行することで、確実にコマンドを実行できるようにする。
meta:
  tag: []
  requires_repo_tools: none
  requires_env: none
  dependencies: requests, typer
  requires_install: none
  requires_hooks: none
  requires_skills: none
  status: stable
  description: no description
  version: 1.0.0
---

!`python "${CLAUDE_SKILL_DIR}/webref_cli.py" download`

# Kilo Code (kilo.ai) 最新ドキュメント参照

Kilo Codeに関する質問に、学習データの記憶ではなく`kilo.ai/docs`の最新コンテンツを根拠に回答するためのスキル。

## `output/llms.txt`の性質(1ファイルに索引+全文が同居)

`kilo.ai/docs`は`llms-full.txt`を公開していない(確認済み: 404)。代わりに`output/llms.txt`1ファイルの中に、**ファイル冒頭のページ索引**(カテゴリ見出し + `[Title](URL)`リンク一覧、約320行)と、**それに続く全222ページ分の全文**(`## Source: /path`マーカー区切り)の両方が連結されている。つまりこの1ファイルが実質的に他スキルでの`llms.txt`+`llms-full.txt`を兼ねている。

セクション区切りは以下の形式(`Source:`行が`# タイトル`行より**先**に来る点に注意。他サイトでよくある「タイトル→Source」の逆順):

```text
## Source: /ai-providers/alibaba

---
sidebar_label: Alibaba Cloud
---

# Using Alibaba Cloud With Kilo Code

<本文>

---

## Source: /ai-providers/anaconda-desktop
...
```

## 手順

1. **索引で関連ページを特定する**

   - `output/llms.txt`の冒頭部分(`## Source:`が最初に現れるより前、約320行)をGrep/Readし、関連しそうなページの`[Title](URL)`からパス(`?path=%2F...`をURLデコードしたもの、例: `ai-providers/alibaba`)を特定する
   - カテゴリの目安: `getting-started/...`(導入・設定・FAQ)、`ai-providers/...`(各AIプロバイダの接続設定)、`automate/...`(Modes・Tools・Orchestrator等の自動化機能)、`kiloclaw/...`(クラウド上のエージェントゲートウェイ)

2. **該当ページの本文を抽出する**

   ```sh
   python "${CLAUDE_SKILL_DIR}/webref_cli.py" extract-section <パスまたはURL> [<パスまたはURL>...]
   ```

   - 例: `python "${CLAUDE_SKILL_DIR}/webref_cli.py" extract-section ai-providers/alibaba automate/agent-manager`
   - パスは索引リンクの`path=`パラメータをURLデコードしたもの(先頭の`/`は省略可)、または`https://kilo.ai/docs/...`のフルURLをそのまま渡してもよい
   - `output/temp/<slug>.txt`に本文全文が書き出される。本文は最小400字弱〜最大37,000字強までばらつきが大きく、`--summarize-threshold`(既定6000文字)を超える場合は`aim` CLIで要約した`output/temp/<slug>.summary.md`も追加で生成される(要約時も全文ファイルへのパスは必ず案内される)
   - 見つからない場合、スナップショット取得後に追加されたページの可能性がある。その旨を伝えた上でWebFetchで`https://kilo.ai/docs/<パス>`を直接参照してもよい

3. **回答する**

   - 抽出した本文に基づいて回答し、参照したURL(`Source:`行)を明示する

## 補足

- スクリプトは`${CLAUDE_SKILL_DIR}/output/`を読み書きする。ダウンロードは24時間以内に取得済みならスキップされる(`--force`で強制再取得、`python "${CLAUDE_SKILL_DIR}/webref_cli.py" download --force`)
- `output/temp/`は`extract-section`の作業用一時ファイル置き場(都度上書きされる想定、gitignore済み)
