---
name: vscode-docs
description: Use when answering questions about Visual Studio Code (the editor) features, settings, keybindings, extensions, tasks, debugging, source control, Copilot Chat/Agent mode in VS Code, etc. Grounds answers in the latest official docs (code.visualstudio.com) instead of training-data memory, which may be stale.
allowed-tools: Bash(python skills/plugins/others/skills/vscode-docs/*.py *)
# !`<command>`を使ってスクリプトを実行することで、確実にコマンドを実行できるようにする。
meta:
  tag: []
  requires_repo_tools: none
  requires_env: none
  dependencies: python
  requires_install: none
  requires_hooks: none
  requires_skills: none
  status: stable
  description: no description
  version: 1.0.6
---

!`python skills/plugins/others/skills/vscode-docs/download_vscode_reference.py`

# VS Code 最新ドキュメント参照

Visual Studio Code に関する質問に、学習データの記憶ではなく `code.visualstudio.com` の最新ドキュメントを根拠に回答するためのスキル。

## 注意: llms-full.txt は存在しない

`code.claude.com` と異なり、`code.visualstudio.com` は `llms-full.txt`（全ページ本文の連結ファイル）を公開していない（404）。`llms.txt` は各ページへのリンクと短い説明のみを含むインデックスなので、本文が必要な場合はページごとに WebFetch で取得する。

## 手順

1. **関連箇所を探す**

   - `./output/llms.txt` を Grep/Read して、質問に関連しそうなページの URL と短い説明を特定する
   - セクション見出し（`## Get Started` `## Editor` `## Source Control` など）で大まかなカテゴリを絞り込める

2. **該当ページの本文を取得する**（説明文だけで回答できない場合）

   - 見つけた URL を WebFetch で取得する
   - 複数ページにまたがりそうな質問なら、関連しそうな URL を複数 WebFetch してよい

3. **回答する**

   - 取得した本文に基づいて回答し、参照した URL を明示する
   - `./output/llms.txt` に該当ページが見つからない場合は、その旨を伝えた上で `https://code.visualstudio.com/docs` 配下を WebFetch 等で直接探索してもよい

## 補足

- スクリプトはこのディレクトリ（`skills/plugins/others/skills/vscode-docs/`）を基準に `./output/` を読み書きする
- `download_vscode_reference.py` は writing-skill-web の `download_web_reference.py` テンプレートを標準ライブラリだけで動くように写したもの（github-copilot-docs の `download_copilot_reference.py` も同じ形）
- ダウンロードは 24 時間以内に取得済みならスキップされる（`--force` で強制再取得）
