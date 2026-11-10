---
name: ona-cli-docs
description: Use when constructing or explaining raw Ona official CLI (`ona` command) invocations -- e.g. `ona-run`'s `--command` needs a hand-built `ona environment exec`/`ona environment ssh` line, or a question is about `ona login`/personal access tokens, environment/automation subcommands, or CLI configuration. Grounds answers in a curated excerpt of ona.com's official docs (via the ona-docs skill's cached llms.txt) instead of training-data memory, which may be stale or reference the pre-rename "Gitpod" CLI.
meta:
  tag: []
  requires_repo_tools: aim
  requires_env: none
  dependencies: none
  requires_install: none
  requires_hooks: none
  requires_skills: ona-docs
  status: experimental
  description: no description
  version: 1.0.3
---

# Ona 公式CLI（`ona`コマンド）リファレンス（抜粋版）

`ona-run`（`tools/_plugin/my-tools/skills/ona-run/`）のようなテンプレート型ラッパーでは表現できない、Ona公式CLI（`ona`コマンド）そのものの細かい使い方に答えるためのスキル。学習データの記憶ではなく、[ona-docs](../ona-docs/SKILL.md)スキルが取得済みの`docs/llms.txt`から抜粋した`output/cli-excerpt.md`を根拠に回答する。

このスキルは**新規ダウンロードを行わない**。`output/cli-excerpt.md`が古い/見つからない場合は、まず[ona-docs](../ona-docs/SKILL.md)スキルの取得処理（`webref_cli.py download`）を実行して`docs/llms.txt`を最新化してから使う。

## 手順

1. **抜粋ファイルを探す**

   - `./output/cli-excerpt.md`をGrep/Readして、質問に関連しそうなページのURLと短い説明を特定する
   - 収録ページは5件（インストール/認証/コマンド一覧を含むCLI本体2件、Personal access token、外部エージェントからのCLI操作ガイド、Automations as Code）

2. **該当ページの本文を取得する**（説明文だけで回答できない場合）

   - [ona-docs](../ona-docs/SKILL.md)スキルの`extract-section`コマンドで本文を取得する
     ```sh
     python "<ona-docsスキルのディレクトリ>/webref_cli.py" extract-section <URLまたはパス>
     ```
   - パスは`https://ona.com/docs/`以降（末尾の`.md`は省略可）。例: `ona/integrations/cli`, `ona/reference/cli`
   - 複数ページにまたがりそうな質問なら、関連しそうなパスを複数まとめて渡してよい

3. **回答する**

   - 取得した本文に基づいて回答し、参照したURLを明示する
   - `./output/cli-excerpt.md`に該当ページが見つからない場合は、`ona-docs`スキルの`output/docs/llms.txt`全体（CLI以外の製品ドキュメントも含む約450件）をGrepするか、`https://ona.com/docs/`配下を直接WebFetchで探索してもよい

## 他スキルとの役割分担

- Ona製品全体（会社概要、Automations全般、環境設定等）の質問は[ona-docs](../ona-docs/SKILL.md)スキルを使う。このスキルは「`ona`コマンドを実際に打つ場面」に特化した部分集合
- `ona-run`利用中に`--agent`テンプレートでは表現できない`--command`を組み立てる必要がある場合にこのスキルを使う（`ona-run`のSKILL.md/READMEからも導線あり）
- このスキルは`docs/llms.txt`からの**既存コンテンツの抜粋**であり、`--help`出力を実際に実行してキャプチャする方式のスキル（存在する場合）とは抽出方式が異なる。抜粋が古い/実際の挙動と食い違う場合は`ona --help`を直接実行して確認すること
