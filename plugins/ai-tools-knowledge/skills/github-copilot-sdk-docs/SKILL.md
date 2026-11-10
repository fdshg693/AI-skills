---
name: github-copilot-sdk-docs
description: Use when answering questions about the GitHub Copilot SDK (`@github/copilot-sdk` and its Python/Go/Rust/Java/.NET equivalents) — installation, authentication (GitHub OAuth, BYOK, Azure managed identity), sending/streaming messages, custom tools, hooks, custom agents, MCP integration, fleet mode, cloud/remote sessions, session persistence/limits, skills, plugin directories, usage & billing, deployment/scaling/multi-tenancy, or troubleshooting. Grounds answers in the latest official docs (docs.github.com) instead of training-data memory, which may be stale.
meta:
  tag: []
  requires_repo_tools: none
  requires_env: none
  dependencies: none
  requires_install: none
  requires_hooks: none
  requires_skills: github-copilot-docs, github-copilot-observability-docs
  status: stable
  description: no description
  version: 1.0.2
---

# GitHub Copilot SDK 最新ドキュメント参照

GitHub Copilot SDK（`@github/copilot-sdk` およびその Python / Go / Rust / Java / .NET 版。TypeScript/Node.js 20+, Python 3.11+, Go 1.24+, Rust 1.94+, Java 17+, .NET 8.0+ に対応）に関する質問に、学習データの記憶ではなく `docs.github.com` の最新ドキュメントを根拠に回答するためのスキル。SDK は Copilot CLI をエンジンとしてアプリケーションに組み込むためのライブラリで、CLI 単体の操作は [copilot-cli-docs](../copilot-cli-docs/SKILL.md)、GitHub Copilot 全般の仕様は [github-copilot-docs](../github-copilot-docs/SKILL.md) に委譲する。

## 対象を切り分ける

質問を次のいずれかに分類する。分類によって参照すべきページと言語ごとの API 差異が変わる。

- **導入・認証**: インストール、`sendMessage` / streaming、GitHub OAuth、BYOK（Bring Your Own Key）、Azure managed identity
- **機能**: カスタムツール、hooks（セッションライフサイクルへのフック）、custom agents（sub-agent orchestration）、MCP サーバー連携、fleet mode（並列 sub-agent 実行）、skills（再利用可能なプロンプトモジュール）、plugin directories
- **セッション制御**: cloud/remote sessions（Mission Control 経由の GitHub-hosted compute、Web/mobile アクセス）、session persistence（一時停止・再開）、session limits（AI Credits 予算）、context management、steering/queueing、citations、image input、streaming events のフィールド仕様
- **運用・課金**: usage-and-billing（トークン数・使用率・コスト・quota）
- **デプロイ・スケーリング**: backend services への組み込み、multi-tenancy（ユーザーごとの state/認証/tool 分離）、scaling（同時セッション・水平スケール）、bundled CLI と local CLI（カスタムバイナリパス）の違い
- **Observability**: OpenTelemetry・`TelemetryConfig`・trace context 伝播 → [github-copilot-observability-docs](../github-copilot-observability-docs/SKILL.md) に委譲する（このスキルでは扱わない）
- **トラブルシューティング**: SDK 特有のエラー・診断

## 参照する公式ドキュメント

`https://docs.github.com/en/copilot/how-tos/copilot-sdk` 配下。索引ページから辿るか、直接 WebFetch する。

1. **導入**
   - [Getting started](https://docs.github.com/en/copilot/how-tos/copilot-sdk/getting-started) — インストール → メッセージ送信 → streaming → custom tools → 対話型アシスタント構築の 5 ステップ
   - [Authentication overview](https://docs.github.com/en/copilot/how-tos/copilot-sdk/auth) / [Authenticate](https://docs.github.com/en/copilot/how-tos/copilot-sdk/auth/authenticate) / [BYOK](https://docs.github.com/en/copilot/how-tos/copilot-sdk/auth/byok) — デプロイ形態に応じた認証方式の選び方

2. **機能** (`features/`)
   - [Agent loop](https://docs.github.com/en/copilot/how-tos/copilot-sdk/features/agent-loop) — prompt から `session.idle` までの処理フロー
   - [Custom agents](https://docs.github.com/en/copilot/how-tos/copilot-sdk/features/custom-agents) — スコープ付きツールを持つ専用エージェントと sub-agent orchestration
   - [Hooks](https://docs.github.com/en/copilot/how-tos/copilot-sdk/features/hooks) と [Hooks API reference](https://docs.github.com/en/copilot/how-tos/copilot-sdk/hooks) — セッションライフサイクルへのカスタムロジック注入
   - [MCP](https://docs.github.com/en/copilot/how-tos/copilot-sdk/features/mcp) — MCP サーバーによる機能拡張
   - [Fleet mode](https://docs.github.com/en/copilot/how-tos/copilot-sdk/features/fleet-mode) — 複数 sub-agent への並列ディスパッチ
   - [Skills](https://docs.github.com/en/copilot/how-tos/copilot-sdk/features/skills) / [Plugin directories](https://docs.github.com/en/copilot/how-tos/copilot-sdk/features/plugin-directories) — 再利用可能な能力のパッケージ化
   - [Cloud sessions](https://docs.github.com/en/copilot/how-tos/copilot-sdk/features/cloud-sessions) / [Remote sessions](https://docs.github.com/en/copilot/how-tos/copilot-sdk/features/remote-sessions) — Mission Control 経由の GitHub-hosted compute・Web/mobile アクセス
   - [Session persistence](https://docs.github.com/en/copilot/how-tos/copilot-sdk/features/session-persistence) / [Session limits](https://docs.github.com/en/copilot/how-tos/copilot-sdk/features/session-limits) / [Context management](https://docs.github.com/en/copilot/how-tos/copilot-sdk/features/context-management)
   - [Steering and queueing](https://docs.github.com/en/copilot/how-tos/copilot-sdk/features/steering-and-queueing) / [Streaming events](https://docs.github.com/en/copilot/how-tos/copilot-sdk/features/streaming-events) / [Citations](https://docs.github.com/en/copilot/how-tos/copilot-sdk/features/citations) / [Image input](https://docs.github.com/en/copilot/how-tos/copilot-sdk/features/image-input)
   - [Usage and billing](https://docs.github.com/en/copilot/how-tos/copilot-sdk/features/usage-and-billing) — トークン数・利用率・コスト・quota

3. **セットアップ・デプロイ** (`setup/`)
   - [Choosing a setup path](https://docs.github.com/en/copilot/how-tos/copilot-sdk/setup/choosing-a-setup-path) — 個人利用から本番プラットフォームまでの構成ガイド一覧
   - [Bundled CLI](https://docs.github.com/en/copilot/how-tos/copilot-sdk/setup/bundled-cli)（Node.js / .NET SDK は CLI 同梱で追加設定不要）/ [Local CLI](https://docs.github.com/en/copilot/how-tos/copilot-sdk/setup/local-cli)（カスタムバイナリパスの指定）
   - [Backend services](https://docs.github.com/en/copilot/how-tos/copilot-sdk/setup/backend-services) — API・マイクロサービス・バックグラウンドワーカーへの組み込み
   - [Multi-tenancy](https://docs.github.com/en/copilot/how-tos/copilot-sdk/setup/multi-tenancy) / [Scaling](https://docs.github.com/en/copilot/how-tos/copilot-sdk/setup/scaling) — 複数ユーザー・同時セッション・水平スケール
   - [GitHub OAuth](https://docs.github.com/en/copilot/how-tos/copilot-sdk/setup/github-oauth) / [Azure managed identity](https://docs.github.com/en/copilot/how-tos/copilot-sdk/setup/azure-managed-identity)（BYOK と組み合わせた静的 API key の代替）

4. **統合・その他**
   - [Integrations](https://docs.github.com/en/copilot/how-tos/copilot-sdk/integrations) — 外部フレームワーク連携。現時点で [Microsoft Agent Framework](https://docs.github.com/en/copilot/how-tos/copilot-sdk/integrations/microsoft-agent-framework)（Copilot SDK を agent provider として組み込むマルチエージェントオーケストレーション）を含む
   - [Troubleshooting](https://docs.github.com/en/copilot/how-tos/copilot-sdk/troubleshooting) — SDK 特有の問題診断
   - [OpenTelemetry instrumentation for Copilot SDK](https://docs.github.com/en/copilot/how-tos/copilot-sdk/observability/opentelemetry) — 詳細は [github-copilot-observability-docs](../github-copilot-observability-docs/SKILL.md) に委譲

`docs.github.com/api/article/body?pathname=...` エンドポイントで該当ページの本文を Markdown で直接取得できる（[github-copilot-docs](../github-copilot-docs/SKILL.md) 参照、例: `curl "https://docs.github.com/api/article/body?pathname=/en/copilot/how-tos/copilot-sdk/getting-started"`）。

## 回答手順

1. **対象を確認する**: 質問がどの言語（TypeScript/Node.js, Python, Go, Rust, Java, .NET）を対象にしているかを明確にする。SDK の概念（session, hook, tool, agent loop）は言語共通だが、API の命名・型・パッケージ配布方法は言語ごとに異なるため、断定する前に対象言語を確認するか、複数言語がありうる旨を明示する。
2. **該当ページを特定する**: 上記の「参照する公式ドキュメント」または `github-copilot-docs` の `output/llms.txt` から関連 URL を探す。`copilot-sdk` セクションは新しく、`llms.txt` の索引に含まれていないことがあるため、見つからない場合は上記の直接リンクか `https://docs.github.com/en/copilot/how-tos/copilot-sdk` を WebFetch する。
3. **本文を取得して検証する**: 設定キー、メソッド名、既定値、preview/GA の別、必要な CLI バージョンは記憶で補わず本文で確認する。
4. **回答する**: 参照した URL を明示し、言語固有の差異がある場合はその旨を添える。

## 委譲

- Copilot CLI 単体のコマンド・設定は [copilot-cli-docs](../copilot-cli-docs/SKILL.md)
- GitHub Copilot の一般的な仕様（プラン、IDE 設定、Chat 等)は [github-copilot-docs](../github-copilot-docs/SKILL.md)
- ログ・監視・OpenTelemetry は [github-copilot-observability-docs](../github-copilot-observability-docs/SKILL.md)
