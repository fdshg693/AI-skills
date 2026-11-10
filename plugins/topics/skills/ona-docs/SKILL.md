---
name: ona-docs
description: Use when answering questions about Ona (ona.com, formerly Gitpod) — the platform for background agents (autonomous AI software engineers that plan, code, test, and open PRs in isolated cloud environments), Automations (trigger-based workflows), Ona environments/Dev Containers, Veto (kernel-level agent security), multi-SCM support (GitHub/GitLab/Bitbucket/Azure DevOps), IDE integrations, the REST API, or company info (leadership, customers, pricing, comparisons to other coding-agent platforms). Grounds answers in the latest official content from ona.com and ona.com/docs instead of training-data memory, which may be stale or still reference "Gitpod".
allowed-tools: Bash(python ${CLAUDE_SKILL_DIR}/*.py *)
# !`<command>`を使ってスクリプトを実行することで、確実にコマンドを実行できるようにする。
meta:
  tag: []
  requires_repo_tools: aim
  requires_env: none
  dependencies: requests, typer
  requires_install: none
  requires_hooks: none
  requires_skills: none
  status: stable
  description: no description
  version: 1.0.2
---

!`python "${CLAUDE_SKILL_DIR}/webref_cli.py" download`

# Ona (ona.com) 最新情報参照

Ona（旧 Gitpod、ona.com）に関する質問に、学習データの記憶ではなく `ona.com` / `ona.com/docs` の最新コンテンツを根拠に回答するためのスキル。学習データは社名変更前の "Gitpod" の情報を含むことがあるため、現行の名称・リーダーシップ・機能名は必ず取得した内容で上書きする。

## 対象は2系統(取得元URLが別、性質も別)

- `output/company/llms.txt` / `output/company/llms-full.txt`(取得元: `ona.com/llms.txt` / `ona.com/llms-full.txt`): **会社・製品の概要コンテンツ**（リーダーシップ、沿革、導入企業、Use Cases、Comparisons、Automation Templates、Blog、Guides、Events、Videos）。索引ではなく**すでに本文そのもの**が書かれており、`# タイトル`/`Source: URL`のようなページ単位のマーカーは無い連続ドキュメント。`llms.txt`(約200行)は概要版、`llms-full.txt`(約1500行)はより詳しい版
- `output/docs/llms.txt` / `output/docs/llms-full.txt`(取得元: `ona.com/docs/llms.txt` / `ona.com/docs/llms-full.txt`): **技術ドキュメント**。`docs/llms.txt`は約500件のページへのリンク索引(`docs/ona/...`が製品機能、`docs/api-reference/...`がREST APIエンドポイント)。`docs/llms-full.txt`は8万行超の全文ダンプだが、`# タイトル`/`Source: URL`のページ単位マーカーが規則的に繰り返される形式なので、`extract-section`でページ単位に抽出できる

## 手順

1. **質問の性質で参照先を決める**

   - 会社概要・リーダーシップ・導入事例・他製品との比較・料金/プラン寄りの質問 → `output/company/llms.txt`(まず読む)、詳細が要れば`output/company/llms-full.txt`
   - 製品の使い方・設定・API仕様など技術的な質問 → `output/docs/llms.txt`をGrepしてURL/パスを特定し、下記の`extract-section`で本文を取得

2. **会社概要コンテンツを読む(`llms.txt`/`llms-full.txt`)**

   - どちらもページ単位マーカーが無い連続ドキュメントなので、素直にGrep/Readする(セクション抽出スクリプトの対象外)
   - 見出し例(`llms-full.txt`): `## Leadership` `## History` `## Customers` `## Use Cases` `## Comparisons` `## Automation Templates` `## Guides` `## Blog Posts` `## Events & Webinars` `## Videos`
   - リーダーシップ・沿革は特に鮮度が重要(社名がGitpodからOnaに変わった経緯、現在の共同創業者がJohannes LandgrafとChristian Weichelであること等)。学習データの古い情報で上書きしない

3. **技術ドキュメントを検索する(`docs/llms.txt`)**

   - `output/docs/llms.txt`をGrep/Readし、関連ページの`[Title](URL): 説明`エントリを特定する
   - パスの目安: `docs/ona/...`が製品機能(environments, automations, agents, configuration, source-control, editors等)、`docs/api-reference/...`がREST APIエンドポイント(約330件)、`docs/changelog`が更新履歴

4. **該当ページの本文を抽出する(`docs/llms-full.txt`)**

   ```sh
   python "${CLAUDE_SKILL_DIR}/webref_cli.py" extract-section <URL または パス> [<URL または パス>...]
   ```

   - 例: `python "${CLAUDE_SKILL_DIR}/webref_cli.py" extract-section ona/agents-md ona/automations/overview`
   - パスは`docs/llms.txt`のリンクの`https://ona.com/docs/`以降(末尾の`.md`は省略可)をそのまま渡す
   - `output/temp/<slug>.txt`に本文全文が書き出される(本文が`--summarize-threshold`既定6000文字を超える場合は`aim` CLIで要約した`output/temp/<slug>.summary.md`も追加で生成される。要約時も全文ファイルへのパスは必ず案内される)
   - 見つからない場合は`output/docs/llms.txt`に載っていない可能性がある。その旨を伝えた上でWebFetchで`ona.com/docs/`配下を直接参照してもよい

5. **回答する**

   - 参照した本文に基づいて回答し、参照したURL(`Source:`行)を明示する
   - 命名規則に注意: 社名は"Ona"を使う("Gitpod"は旧社名として言及する場合のみ)。"Background agents"(自律的にコード変更しPRを作るクラウド上のAIエージェント)と"Automations"(トリガー駆動でAIプロンプトと決定的コマンドを組み合わせるワークフロー)は別概念なので混同しない

## 補足

- スクリプトは`${CLAUDE_SKILL_DIR}/output/`を読み書きする。ダウンロードは24時間以内に取得済みならスキップされる(`--force`で強制再取得、`python "${CLAUDE_SKILL_DIR}/webref_cli.py" download --force`)
- `output/temp/`は`extract-section`の作業用一時ファイル置き場(都度上書きされる想定、gitignore済み)
- 会社概要用(`ona.com/llms.txt`等)とドキュメント用(`ona.com/docs/llms.txt`等)はどちらもファイル名が`llms.txt`/`llms-full.txt`で衝突するため、取得元がわかるよう`output/company/`と`output/docs/`のサブディレクトリに分けて保存している
