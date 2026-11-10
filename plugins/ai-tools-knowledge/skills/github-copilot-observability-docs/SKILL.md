---
name: github-copilot-observability-docs
description: Use when answering questions about GitHub Copilot logs, diagnostic logging, audit logs, usage metrics, agent activity monitoring, or OpenTelemetry for Copilot Chat in VS Code, Copilot CLI, Copilot SDK, or GitHub Enterprise. Grounds answers in the latest official GitHub and VS Code documentation instead of training-data memory, which may be stale.
meta:
  tag: []
  requires_repo_tools: none
  requires_env: none
  dependencies: none
  requires_install: none
  requires_hooks: none
  requires_skills: github-copilot-docs, vscode-copilot-docs, copilot-cli-docs
  status: stable
  description: no description
  version: 1.0.3
---

# GitHub Copilot のログ・監視・OpenTelemetry 最新ドキュメント参照

GitHub Copilot の実行状況を調査・収集・監視する質問に、公式ドキュメントを根拠に回答するためのスキル。Copilot のサーフェスごとに、ローカルログ、OpenTelemetry（OTel）の traces / metrics / events、GitHub の監査ログ、利用メトリクスを区別して扱う。

## 対象を切り分ける

質問を次のいずれか、または複数に分類する。分類が違うと設定、データの粒度、保持期間、権限、取得できる内容が異なる。

- **VS Code / Copilot Chat**: `github.copilot.chat.otel.*` 設定、OTLP exporter、Agent Debug Log、ローカル SQLite / JSONL 出力、Copilot managed settings
- **Copilot CLI**: `~/.copilot/logs/`、`--log-dir` / `--log-level`、hooks によるプロンプト・ツールイベントの記録、CLI の OTel
- **Copilot SDK**: `TelemetryConfig`、CLI との W3C Trace Context 伝播、アプリケーションの span との相関
- **GitHub.com / Enterprise**: enterprise audit log、agentic audit events、agent session、Copilot usage metrics、activity report、REST API
- **基盤**: OTel Collector、OTLP HTTP / gRPC、Jaeger・Grafana・Application Insights・その他の OTLP 対応バックエンド

VS Code 製品 telemetry（`telemetry.telemetryLevel`）と Copilot OTel export は別物として説明する。GitHub の audit log はプラン・設定変更や GitHub 上の agent activity の監査用であり、ローカルクライアントのプロンプト本文を含むとは限らない。

## 参照する公式ドキュメント

1. **GitHub Copilot / CLI**

   - [GitHub Copilot CLI command reference](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-command-reference) — ローカルログ、ログレベル、環境変数、CLI OTel の設定・signal・属性
   - [Copilot CLI configuration directory](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-config-dir-reference) — `~/.copilot` 配下のログとセッションデータ
   - [Using hooks with Copilot CLI](https://docs.github.com/en/copilot/tutorials/copilot-cli-hooks) — プロンプト・ツール呼び出しの監査、ポリシー制御、中央ログ基盤への転送
   - [Reviewing audit logs for GitHub Copilot](https://docs.github.com/en/copilot/how-tos/administer-copilot/manage-for-enterprise/review-audit-logs) — Copilot の設定・ライセンス変更と監査ログの制約
   - [Audit log events for agents](https://docs.github.com/en/copilot/reference/agentic-audit-log-events) — agentic event のフィールド、ストリーミング、`actor:Copilot`
   - [GitHub Copilot usage metrics](https://docs.github.com/en/copilot/concepts/copilot-usage-metrics) — ダッシュボード、API、利用・採用・コード生成メトリクス
   - [REST API endpoints for Copilot metrics](https://docs.github.com/rest/copilot/copilot-metrics) — Enterprise / organization / team 単位の集計 API
   - [OpenTelemetry instrumentation for Copilot SDK](https://docs.github.com/en/copilot/how-tos/copilot-sdk/observability/opentelemetry) — SDK の telemetry と trace context 伝播

2. **VS Code**

   - [Monitor agent usage with OpenTelemetry](https://code.visualstudio.com/docs/agents/guides/monitoring-agents) — Copilot Chat の signal、設定、環境変数、content capture、バックエンド連携
   - [Manage AI settings in enterprise environments](https://code.visualstudio.com/docs/enterprise/ai-settings) — `telemetry` managed settings、適用優先順位、ヘッダーと reload の注意点

本文が必要な場合は、既存の [github-copilot-docs](../github-copilot-docs/SKILL.md) の `output/llms.txt` や [vscode-copilot-docs](../vscode-copilot-docs/SKILL.md) の `output/copilot-excerpt.md` から URL を絞り込み、WebFetch で公式ページの現行本文を取得する。索引にない場合は上記公式 URL または公式サイト内検索を使う。

## 回答手順

1. **目的とサーフェスを確認する**。デバッグ、リアルタイム observability、監査・コンプライアンス、利用状況分析のどれかを特定し、対象が CLI / VS Code / SDK / GitHub.com のどれかを明示する。
2. **ログ種別と signal を分ける**。診断ログ（人が読むログ）、audit event（統制・変更履歴）、usage metrics（集計値）、OTel traces / metrics / events（実行観測）を混ぜない。必要なら「どの問いにどのデータが答えられるか」を先に示す。
3. **公式本文で現行値を検証する**。設定キー、環境変数、既定値、優先順位、対応プロトコル、バージョン要件、preview / GA、権限、保持期間、API の scope / 制限は記憶で補わない。
4. **最小構成を提示する**。有効化条件、exporter と endpoint、認証ヘッダー、`service.name` / resource attributes、Collector またはバックエンド側の受信設定を対象サーフェスに合わせて示す。必要に応じて Windows PowerShell の環境変数例も示す。
5. **検証方法を添える**。設定の反映（managed settings の policy diagnostics や VS Code reload を含む）、CLI のログパス、OTLP endpoint、service 名、trace / metric の到着、サンプル属性を順に確認する。
6. **制約と安全性を明記する**。content capture はプロンプト、応答、コード、tool arguments を含み得るため、既定の無効状態、redaction、アクセス制御、暗号化、保持期間、secret の非出力を確認する。ログや trace を貼るときは token・Authorization header・プロンプト本文・コード・個人情報をマスクする。
7. **公式 URL を回答に付ける**。変更されやすい仕様には参照ページと確認時点を付け、preview や surface / version による差異があれば断定を避ける。

## トラブルシューティングの優先順

- ログがない: 対象プロセスとログディレクトリ、`--log-level`、CLI / 拡張機能の再起動、OTel の有効化条件を確認する。
- OTel が届かない: endpoint の URL、HTTP / gRPC とポート、headers、Collector の受信設定、`service.name`、環境変数と設定の優先順位を確認する。
- 一部の trace だけ見える: foreground agent、Copilot CLI、Claude agent、SDK の別プロセス・別 service 名・trace context 伝播の有無を確認する。
- 内容が見えない: content capture が意図的に無効なのかを確認し、監視目的に不要な本文収集は有効化しない。必要なら metadata / token / duration のみで調査する。
- GitHub の audit log で prompt を探している: audit log、CLI hooks、クライアントログ、OTel は別の収集経路であることを説明し、必要なデータに合う経路を選ぶ。

CLI 単体の一般的なコマンド仕様は [copilot-cli-docs](../copilot-cli-docs/SKILL.md)、VS Code の Copilot 機能全般は [vscode-copilot-docs](../vscode-copilot-docs/SKILL.md)、GitHub Copilot の監視以外の一般的な仕様は [github-copilot-docs](../github-copilot-docs/SKILL.md) に委譲する。
