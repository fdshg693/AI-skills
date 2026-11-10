---
name: doc-transcription
description: Extracts selectable text from one local PDF or PowerPoint (.pptx) file into a Markdown file and prints that file's path. Use when the text of a PDF or pptx should be taken out before reading the file, including テキスト抽出.
# 前提: `uv` が必要。対象は `.pdf` と `.pptx` のみ（大文字小文字は区別しない）。
# `uv.lock` を同梱している。初回の `uv run` は依存取得のためネットワークが要る。抽出処理そのものは外部に通信しない。
# 出力先は実行時のカレントディレクトリの temp/doc-transcription/。リポジトリルートで実行する。
# ${CLAUDE_SKILL_DIR} は Claude Code の置換変数で、PowerShell では空になる。起動例は絶対パスにする。
# 設計意図・依存の選定は同階層の README.md（人間のメンテナ向け）
allowed-tools: Bash(uv run *)
meta:
  tag: []
  requires_repo_tools: none
  requires_env: none
  dependencies: pypdf, cryptography
  requires_install: uv
  requires_hooks: none
  requires_skills: none
  status: experimental
  description: PDF / PPTX のテキスト抽出（第一版）
  version: 1.0.0
---

## 呼ぶ条件

ローカルの `.pdf` または `.pptx` から、選択できる文字を抽出してから中身を読みたいとき。引数はファイル1つ。リポジトリルートで実行する。

## 対象外

次は断る。OCR も、画像や図の内容の推測もしない。

- スキャン PDF、画像だけのスライド、図・グラフ・SmartArt・チャートの中の文字
- `.ppt` / `.doc` / `.docx` / `.xlsx`
- パスワード付きファイルの解除

抽出の限界（直さない）:

- 数式、フッター・日付・スライド番号の図形の文字
- 縦書きの読み順
- 日本語の余計な空白や文字化け。文字化けは例外にならず、ログに出るだけ
- 見出しの推定、段組み、表の行列。取れた順のまま

## 実行

リポジトリルートで実行する。`<skill-dir>` は、この SKILL.md があるディレクトリの絶対パスに置き換える。入力も絶対パスにする。どちらも引用符で囲む。

```text
uv run --project "<skill-dir>" doc-transcription "<入力ファイルの絶対パス>"
```

## 結果の読み方

終了コード 0 のとき、標準出力の1行が書いた Markdown の絶対パス。そのパスを Read する。先頭行が元のファイル名。PowerPoint で非表示スライドを除いたときだけ、次の行に件数がある。本文は `## ページ N` または `## スライド N`。ノートがあるスライドだけ `### ノート` が付く。非表示スライドの番号は詰めない。

終了コード 1 は抽出の失敗。標準エラーの理由をそのまま伝える。終了コード 2 は使い方の誤り（引数なし、無いパス、未対応の拡張子、`~$` で始まる Office の一時ファイル）。
