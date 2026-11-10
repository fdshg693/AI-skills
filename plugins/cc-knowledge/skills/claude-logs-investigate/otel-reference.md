# Claude Code OpenTelemetry 環境変数・メトリクス・イベント リファレンス

出典: `code.claude.com/docs/en/monitoring-usage`。最新情報が必要な場合は `claude-code-docs` スキルで再取得すること。

## 有効化・エクスポータ選択

| 環境変数                       | 説明                                                                                |
| ------------------------------ | ----------------------------------------------------------------------------------- |
| `CLAUDE_CODE_ENABLE_TELEMETRY` | `1` でテレメトリ送信を有効化(これが無いと他の設定は無視される)                      |
| `OTEL_METRICS_EXPORTER`        | `otlp` / `prometheus` / `console` / `none`                                          |
| `OTEL_LOGS_EXPORTER`           | `otlp` / `console` / `none`                                                         |
| `OTEL_TRACES_EXPORTER`         | トレース出力先。有効化には `CLAUDE_CODE_ENHANCED_TELEMETRY_BETA=1` も必要(beta機能) |

## 送信先・プロトコル

| 環境変数                                                                      | 説明                                                                               |
| ----------------------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| `OTEL_EXPORTER_OTLP_ENDPOINT`                                                 | OTLPコレクタのエンドポイント(全信号共通のデフォルト)                               |
| `OTEL_EXPORTER_OTLP_PROTOCOL`                                                 | `grpc` / `http/json` / `http/protobuf`                                             |
| `OTEL_EXPORTER_OTLP_METRICS_ENDPOINT` / `_LOGS_ENDPOINT` / `_TRACES_ENDPOINT` | 信号ごとにエンドポイントを個別上書き(SIEM連携等でログだけ別送り先にする場合に使う) |
| `OTEL_EXPORTER_OTLP_HEADERS`                                                  | 認証ヘッダ等を付与                                                                 |

## エクスポート間隔

| 環境変数                      | デフォルト |
| ----------------------------- | ---------- |
| `OTEL_METRIC_EXPORT_INTERVAL` | 60000ms    |
| `OTEL_LOGS_EXPORT_INTERVAL`   | 5000ms     |

## 送信内容の詳細度制御

| 環境変数                              | 説明                                                                                                  |
| ------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| `OTEL_LOG_USER_PROMPTS`               | ユーザープロンプト本文をログに含めるか                                                                |
| `OTEL_LOG_ASSISTANT_RESPONSES`        | アシスタント応答本文を含めるか                                                                        |
| `OTEL_LOG_TOOL_DETAILS`               | Bashコマンド内容・MCPサーバー名等のツール詳細を含めるか                                               |
| `OTEL_LOG_TOOL_CONTENT`               | ツール入出力の内容まで含めるか(トレース有効化が前提)                                                  |
| `OTEL_LOG_RAW_API_BODIES`             | APIリクエスト/レスポンスの生ボディを含めるか。`file:<dir>` を指定するとボディ全文をファイル保存できる |
| `CLAUDE_CODE_OTEL_CONTENT_MAX_LENGTH` | OpenTelemetryのcontent系属性のトランケーション上限（デフォルト60KB）を変更する                        |

## カーディナリティ制御(メトリクスの属性を絞る)

| 環境変数                                   |
| ------------------------------------------ |
| `OTEL_METRICS_INCLUDE_SESSION_ID`          |
| `OTEL_METRICS_INCLUDE_VERSION`             |
| `OTEL_METRICS_INCLUDE_ACCOUNT_UUID`        |
| `OTEL_METRICS_INCLUDE_ENTRYPOINT`          |
| `OTEL_METRICS_INCLUDE_RESOURCE_ATTRIBUTES` |

## メトリクス名(8種)

- `claude_code.session.count`
- `claude_code.lines_of_code.count`
- `claude_code.pull_request.count`
- `claude_code.commit.count`
- `claude_code.cost.usage`
- `claude_code.token.usage`
- `claude_code.code_edit_tool.decision`
- `claude_code.active_time.total`

## イベント名(ログとして送信されるもの)

- `claude_code.user_prompt`
- `claude_code.assistant_response`
- `claude_code.tool_result`
- `claude_code.api_request`
- `claude_code.api_error`
- `claude_code.api_refusal`
- `claude_code.api_request_body`
- `claude_code.api_response_body`
- `claude_code.tool_decision`
- `claude_code.permission_mode_changed`
- `claude_code.auth`
- `claude_code.mcp_server_connection`
- `claude_code.internal_error`
- `claude_code.plugin_installed`
- `claude_code.plugin_loaded`
- `claude_code.skill_activated`
- `claude_code.at_mention`
- `claude_code.api_retries_exhausted`
- `claude_code.hook_registered`
- `claude_code.hook_execution_start`
- `claude_code.hook_execution_complete`
- `claude_code.hook_plugin_metrics`
- `claude_code.compaction`
- `claude_code.feedback_survey`

MCPサーバーの接続や利用状況を監査したい場合は `mcp_server_connection` / `tool_result` / `tool_decision` を `OTEL_LOG_TOOL_DETAILS=1` と組み合わせて見る。

## 標準属性

送信される全信号に付与されうる属性:

- `session.id`
- `app.version`
- `app.entrypoint`
- `organization.id`
- `user.account_uuid`
- `user.id`
- `user.email`
- `terminal.type`

## 組織全体への強制配布

managed settings の `settings.json` の `env` キーに上記環境変数を設定すると、組織全体のClaude Codeインスタンスに強制適用できる。管理側で`OTEL_EXPORTER_OTLP_ENDPOINT`を設定した場合、下位スコープの信号別上書き（`_METRICS_ENDPOINT`等）よりも管理設定側が優先される（以前はバグで信号別上書きがmanaged設定を上書きしてしまっていたが修正済み）。

## Agent SDKとの関係

Agent SDKはClaude Code CLIをそのまま子プロセスとして起動して使うため、CLI本体のOpenTelemetry計装をそのまま利用する。SDK自体が独自のテレメトリを生成するわけではなく、設定する環境変数もCLIと共通。
