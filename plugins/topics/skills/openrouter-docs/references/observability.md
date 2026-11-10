# Observability

Source: `guides/features/input-output-logging`, `guides/features/broadcast`, `guides/features/router-metadata`

目的の異なる2つの主要機能がある。

|              | Input & Output Logging（Beta）       | Broadcast                                     |
| ------------ | ------------------------------------ | --------------------------------------------- |
| 保存先       | OpenRouter上（GCSに暗号化保存）      | 外部プラットフォーム（destination単位で設定） |
| 設定         | ワークスペース設定のトグル1つ        | destinationごとに認証情報を設定               |
| アクセス     | Logsページ（組織はadmin限定）        | 各外部ツール側                                |
| 用途         | デバッグ・応答比較・プロンプト最適化 | 本番監視・分析                                |
| プライバシー | 常にプライベート（学習等に不使用）   | destinationごとにPrivacy Mode設定可           |

## Broadcast

対応先はLangfuse, LangSmith, Datadog, Sentry, Grafana Cloud, New Relic, S3/S3互換, Snowflake, ClickHouse, PostHog, Braintrust, Comet Opik, Arize AX, W\&B Weave, OpenTelemetry Collector, Webhook, Ramp, Raindropなど（随時追加、最新リストは[Broadcast設定ページ](https://openrouter.ai/settings/observability)）。

- `trace_id`/`session_id`/`user`/`parent_span_id`等のメタデータでリクエストをグルーピングでき、`parent_span_id`で自前のOTel等トレースにネストさせることも可能
- destinationごとにAPIキーフィルタ・サンプリングレート・Privacy Modeも設定できる
- 管理はSDKの`openRouter.observability.{list,create,get,update,delete}()`（Management API Key必須）

なお「OpenRouterへのデータ利用許可（Privacy設定、全モデル1%割引）」はInput & Output Loggingとは別設定で、両者は独立に有効化できる。

## Grafana Cloud

Source: `guides/features/broadcast/grafana`

Broadcast先の1つ、[Grafana Cloud](https://grafana.com/products/cloud/)（Tempoによる分散トレーシングを含むフルマネージドObservabilityプラットフォーム）向けの詳細。OpenRouterは標準のOTLP HTTP/JSONエンドポイント経由でトレースを送信する。

- **必要な認証情報（3つ）**
  - 前提: 「スタック」とはGrafana Cloud上の1つのGrafanaインスタンス環境（Grafana本体＋Prometheus/Loki/Tempo等がセットになったもの）のこと。無料登録すると**サインアップ時に自動で1つ作成される**ため、複数の環境を使い分けていない限り、自分のスタックは通常1個しかない（「スタックを選択」に選択肢の迷いは基本ない）
  - Base URL / Instance ID: `https://grafana.com/` にログイン → Cloud Portal（自分の組織のスタック一覧が表示される。org名やURLを事前に組み立てる必要はない）→ 自分のスタック（の箱/タイル）をクリックして開く → スタック詳細ページ上の複数タイル（Grafana / Prometheus / Loki / Tempo / OpenTelemetry 等、各プロダクトごとに1枚ずつ並んでいる）のうち **OpenTelemetry のタイルだけを開く**（Configure/Detailsボタン）→ そのパネルに **OTLP Endpoint（Base URL）と Instance ID（数値、OTLP認証のbasic-auth usernameとして使う）が同じ画面にまとめて表示される**。メインのGrafanaダッシュボードURL自体はBase URLではないので混同しないこと
  - 補足: Instance IDはスタック全体で1つではなく、タイルごと（Prometheus用、Loki用、Tempo用…）に別々の値が存在する。OTLP用に使うのは**OpenTelemetryのタイルに表示された値だけ**であり、他のタイルの値と混同しないこと。正確な画面上のラベル・ボタン名はUI変更で変わることがあるため、食い違う場合はログイン後の実際の画面表示を優先すること
  - API Key: `traces:write` スコープのAccess Policyから発行したAPIトークン（`glc_...`で始まる）
- **設定手順**: `Settings > Observability`（`https://openrouter.ai/settings/observability`）でBroadcastを有効化 → Grafana Cloudの編集アイコンから上記3つを入力 → Test Connectionで疎通確認（成功時のみ保存）→ テストリクエストを送りトレースを確認
- **閲覧方法**: Grafana Cloud側でExplore > Tempoデータソース（`grafanacloud-*-traces`）> TraceQLタブ、または Drilldown > Traces
- **トレース属性**
  - リソース属性: `service.name`（常に`openrouter`）, `service.version`, `openrouter.trace.id`
  - スパン属性: `gen_ai.operation.name`, `gen_ai.system`, `gen_ai.request.model`, `gen_ai.response.model`, `gen_ai.usage.{input,output,total}_tokens`, `gen_ai.response.finish_reason`
- **カスタムメタデータのマッピング**（リクエストの`trace`フィールド・`user`・`session_id`から）

  | Key                           | Grafana Mapping                  | 説明                                                 |
  | ----------------------------- | -------------------------------- | ---------------------------------------------------- |
  | `trace_id`                    | Trace ID                         | 複数リクエストを1つのトレースにまとめる              |
  | `trace_name`                  | Span Name                        | ルートspanのカスタム名                               |
  | `span_name`                   | Span Name                        | 階層内の中間spanの名前                               |
  | `generation_name`             | Span Name                        | LLM生成spanの名前                                    |
  | `parent_span_id`              | Parent Span ID                   | 既存トレース階層内の親spanへのリンク                 |
  | （`trace`内のその他任意キー） | `trace.metadata.*`配下のspan属性 | TraceQLで`span.trace.metadata.<key>`としてクエリ可能 |
  | リクエストの`user`            | `user.id` span属性               |                                                      |
  | リクエストの`session_id`      | `session.id` span属性            |                                                      |

  リクエスト例:

  ```json
  {
    "model": "openai/gpt-4o",
    "messages": [{ "role": "user", "content": "Analyze this metric..." }],
    "user": "user_12345",
    "session_id": "session_abc",
    "trace": {
      "trace_id": "monitoring_pipeline_001",
      "trace_name": "Metric Analysis Pipeline",
      "generation_name": "Anomaly Detection",
      "environment": "production",
      "alert_id": "alert_789"
    }
  }
  ```

- **TraceQLクエリ例**

  ```traceql
  { resource.service.name = "openrouter" }
  { resource.service.name = "openrouter" && span.gen_ai.request.model = "openai/gpt-4-turbo" }
  { resource.service.name = "openrouter" && span.trace.metadata.environment = "production" }
  { resource.service.name = "openrouter" && duration > 5s }
  { resource.service.name = "openrouter" && span.user.id = "user_abc123" }
  { resource.service.name = "openrouter" && status = error }
  ```

- **Privacy Mode**: 有効化するとprompt/completion本文はトレースから除外されるが、トークン使用量・コスト・タイミング・モデル情報・カスタムメタデータは通常通り送信される
- **トラブルシューティング**（トレースが表示されない場合）
  1. Grafanaの時間範囲ピッカーを確認（"Last 1 hour"等に広げる）
  2. OTLP gateway URLを使っているか確認（メインのGrafana URLではない）
  3. Instance IDが数値か、APIキーに`traces:write`権限があるか確認
  4. 反映まで1〜2分のタイムラグがあることを考慮する

設定手順・属性名・クエリ構文は変わりやすいので、断定的に答える前に上記Sourceパスを`extract_doc_section.py`で再取得して裏取りすること。

## Router Metadata（リクエスト単位）

[Router Metadata](https://openrouter.ai/docs/guides/features/router-metadata)は、ワークスペース全体を継続監視するBroadcast/Loggingとは別軸で、単発リクエストのルーティング挙動をデバッグする機能。`X-OpenRouter-Metadata: enabled`ヘッダを付けるとレスポンスに`openrouter_metadata`（選ばれたprovider、フォールバック試行、ガードレール/コンテキスト圧縮/サーバーツール等のpipeline実行内容）が載る。

使い分け: 継続的な監視・分析はBroadcast/Logging、単発リクエストの「なぜこのproviderが選ばれたか」を追うにはRouter Metadata。

対応先リストや料率は変わりやすいので、断定的に答える前に上記Sourceパスを`extract_doc_section.py`で再取得して裏取りすること。
