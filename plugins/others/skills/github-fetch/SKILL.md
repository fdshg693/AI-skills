---
name: github-fetch
description: Pull only a specific subset of files from a GitHub repository into the local filesystem, without cloning the whole repo. Narrows scope step by step via the GitHub REST API (README, then progressively deeper folder listings) before downloading anything. Use when the user wants "just this folder/file from some GitHub repo", wants to inspect an unfamiliar repo's structure before deciding what to pull, or explicitly says not to `git clone` the whole thing.
context: fork
agent: general-purpose

# 前提条件:
#   - Python 3(標準ライブラリのみで動作。追加パッケージ不要)
#   - ネットワークアクセス(api.github.com への到達性)
#   - 認証は任意だが推奨。次のいずれかでトークンを渡すと
#     レート制限が 60/時間 -> 5000/時間 に上がり、private リポジトリにもアクセスできる。
#       1. --token <token>
#       2. 環境変数 GITHUB_TOKEN または GH_TOKEN
#       3. このスキル同階層の .env（例: GITHUB_TOKEN=ghp_...）
#     未設定でも public リポジトリの少量アクセスなら動くが、匿名はすぐレート制限に当たる。
#
# context: fork の理由:
#   絞り込みには「list を何段か試す -> tree で確認 -> get/get-tree」という
#   ツール呼び出しの繰り返しが発生し、各ステップの生出力(ディレクトリ一覧やファイル一覧)は
#   最終結果(ローカルに書き出したファイルパス一覧)にとって不要なノイズになる。
#   フォークされたサブエージェントに探索させ、確定したファイルパス一覧だけを
#   呼び出し元に返させることで、本会話のコンテキストを汚さない。
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
  version: 1.0.0
---

## 全体の流れ

1. **README を読む** — リポジトリの目的・構成を把握する
   ```
   python "${CLAUDE_SKILL_DIR}/gh_fetch.py" readme <owner>/<repo> [--ref <branch>]
   ```
2. **ルート直下を一覧** — `list` にパスを渡さない(または `""`)とルートを見る
   ```
   python "${CLAUDE_SKILL_DIR}/gh_fetch.py" list <owner>/<repo>
   ```
3. **候補フォルダを絞り込む** — README とルート一覧から目的に近いフォルダに当たりを付け、`list` にそのパスを渡して1階層ずつ潜る。ここを何度か繰り返す(判断はエージェント自身が行う。スクリプトは1階層分の子要素を返すだけ)
   ```
   python "${CLAUDE_SKILL_DIR}/gh_fetch.py" list <owner>/<repo> <path>
   ```
4. **十分絞れたら再帰一覧で確認** — これ以上潜らなくてよい(ファイル数が扱える規模)と判断したら `tree` でそのパス配下全ファイルを確認する
   ```
   python "${CLAUDE_SKILL_DIR}/gh_fetch.py" tree <owner>/<repo> <path>
   ```
   出力に `WARNING: ... truncated` が出た場合はまだ広すぎるので、ステップ3に戻ってさらに深い/狭いパスを選び直す。
5. **必要なファイルだけをローカルに取得**
   - 特定の1ファイルだけでよいなら `get`
     ```
     python "${CLAUDE_SKILL_DIR}/gh_fetch.py" get <owner>/<repo> <file-path> <local-dest>
     ```
   - 絞り込んだフォルダ配下をまるごと取得するなら `get-tree`(構造を保ったまま `<local-dest>` 配下に書き出す。`<path>` 部分はローカル側のパスから取り除かれる)
     ```
     python "${CLAUDE_SKILL_DIR}/gh_fetch.py" get-tree <owner>/<repo> <path> <local-dest> [--include "*.py"] [--exclude "*_test.py"]
     ```
     デフォルトで一度に取得できるのは200ファイルまで(`--max-files`)。超える場合はエラーになるので、フォルダをさらに絞るか `--include`/`--exclude` で絞るか、本当に必要なら `--max-files` を明示的に上げる。

全コマンド共通で `--ref <branch|tag|sha>` を指定できる(省略時はデフォルトブランチ)。

## 使用上の注意

- **いきなり `get-tree` をルートやブランチ全体に対して使わない。** このスキルの主目的は「絞り込んでから取る」こと。ステップ2〜4を飛ばして広い範囲を一括取得しようとする(あるいは `--max-files` を安易に引き上げる)のは、このスキルを使う意味がない。
- `list` は1階層だけ返す(サブフォルダの中身までは見えない)。深い場所を見たいときは `list` を繰り返し呼ぶか、十分絞れていると確信できるなら直接 `tree` を試してもよい(広すぎれば `truncated` 警告で分かる)。
- `tree`/`get-tree` はパスがファイルだった場合や存在しない場合、分かりやすいエラーを返す。エラーメッセージ通りにパスを直せばよい。
- 大きめのリポジトリを何度も操作する、あるいは private リポジトリにアクセスする場合は、スキル同階層に `.env`（`GITHUB_TOKEN=...`）を置くか環境変数 / `--token` を設定しておく(未設定でも動くが、匿名アクセスは60リクエスト/時間で頭打ちになる)。`.env` はリポジトリの `*.env` gitignore 対象。
- 全サブコマンドの詳細な引数は `--help` で確認できる:
  ```
  python "${CLAUDE_SKILL_DIR}/gh_fetch.py" --help
  python "${CLAUDE_SKILL_DIR}/gh_fetch.py" get-tree --help
  ```

## 呼び出し元への報告

このスキルはフォークされたサブエージェント上で実行される。作業完了時は、取得したファイルの**ローカルパス一覧**と、その元になったリポジトリ上のパス(`<owner>/<repo>@<ref>:<path>`)を簡潔にまとめて返すこと。`list`/`tree` の生出力をそのまま返す必要はない。
