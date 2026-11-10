---
name: cline-sdk-docs
description: Explain and implement Cline SDK applications using current official documentation. Use when the user asks about @cline/sdk, @cline/core, @cline/agents, @cline/llms, Cline agents, custom tools, events, providers, permissions, sessions, plugins, automation, or SDK application architecture. Do not use for the Cline REST API or CLI-only questions.
# 依存: 詳細なSDKパターンは同階層のsdk-reference.md、公式ページの対応表はsdk-reference-map.mdを参照する。最新仕様の取得はcline-docsに委譲する。cline-cli-docsはCLI専用。
meta:
  tag: []
  requires_repo_tools: none
  requires_env: none
  dependencies: "@cline/sdk,@cline/core,@cline/agents,@cline/llms"
  requires_install: none
  requires_hooks: none
  requires_skills: cline-docs,cline-cli-docs
  status: stable
  description: no description
  version: 2.0.3
---

# Cline SDK 公式ドキュメント解説

Cline SDK の質問には、まず [sdk-reference.md](sdk-reference.md) の該当する実装パターンを読み、必要な公式ページを [sdk-reference-map.md](sdk-reference-map.md) から選ぶ。回答では、パッケージ選択、最小コード、イベント・結果・権限の扱いまで具体化し、確認した公式 URL を示す。

## 手順

1. SDK と REST API（`/api`）、CLI（`cline` コマンド）を切り分ける。CLI のフラグ確認だけなら `cline-cli-docs` に切り替える。
2. 目的に応じて [sdk-reference.md](sdk-reference.md) の「パッケージ選択」「Agent」「カスタムツール」「ClineCore」など必要な節だけ読む。
3. `Agent`、`ClineCore`、イベント、ツール、プロバイダー、権限のいずれを使うかを決め、最小の TypeScript 例を質問へ適合させる。APIキーは環境変数から渡す。
4. 詳細な型・未掲載機能・仕様差異が必要なら、[sdk-reference-map.md](sdk-reference-map.md) の URL を使う。まず `cline-docs/SKILL.md` のスナップショット抽出手順を使い、索引にない・古い疑いがある場合だけ `https://docs.cline.bot/sdk/` の該当ページを直接確認する。
5. 公式資料で確認できない仕様は推測で補わず、未確認またはバージョン依存として明記する。

## 回答の基準

- デフォルトは `@cline/sdk` の `Agent`。ステートレスな1回実行、`run` / `continue` / `abort`、購読、`snapshot` を説明する。
- セッション永続化、組み込みツール、Hub、Automation が必要なら `ClineCore`。`create` → `start` → `send` とセッション購読・破棄を説明する。
- カスタムツールでは用途・戻り値・使用条件・制約を説明し、入力スキーマ、入力検証、エラー、承認ポリシーを省略しない。
- 実装回答には、成功だけでなく `status` / `finishReason`、中断、失敗、使用量、タイムアウト、コスト上限を質問の範囲に応じて含める。
- 同階層の詳細資料と公式リファレンスに差異があれば、公式リファレンスを優先し、差異を明示して詳細資料の更新候補にする。
