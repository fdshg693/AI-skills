# OpenTelemetry リファレンス + ローカル収集基盤

Claude Code自体が送信するOpenTelemetry(メトリクス・ログ、betaでトレース)の環境変数・メトリクス名・イベント名の全量リファレンスと、実際に動作確認済みの有効化手順、繰り返し使えるローカル収集基盤(`otel-stack/`)の使い方をまとめる。

出典: `code.claude.com/docs/en/monitoring-usage`。最新情報が必要な場合は `claude-code-docs` スキルで再取得すること。以下の環境変数・メトリクス名・イベント名の一覧は `claude-logs-investigate/otel-reference.md` の内容をそのまま転記したもの(DRYより網羅性を優先する方針)。

## 目次

- [有効化・エクスポータ選択](#有効化エクスポータ選択)
- [送信先・プロトコル](#送信先プロトコル)
- [エクスポート間隔](#エクスポート間隔)
- [送信内容の詳細度制御](#送信内容の詳細度制御)
- [カーディナリティ制御](#カーディナリティ制御メトリクスの属性を絞る)
- [メトリクス名(8種)](#メトリクス名8種)
- [イベント名(ログとして送信されるもの)](#イベント名ログとして送信されるもの)
- [標準属性・実際に確認できた属性](#標準属性実際に確認できた属性)
- [実地検証: コンソールエクスポータでの最小確認](#実地検証-コンソールエクスポータでの最小確認)
- [実地検証: 子プロセスへの非伝播](#実地検証-子プロセスへの非伝播)
- [組織全体への強制配布](#組織全体への強制配布)
- [Agent SDKとの関係](#agent-sdkとの関係)
- [ローカル収集基盤(`otel-stack/`)](#ローカル収集基盤otel-stack)

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

> **実地検証**: デフォルト値(特にメトリクスの60000ms)は確認作業には長すぎる。動作確認時は `OTEL_METRIC_EXPORT_INTERVAL=3000〜5000` 程度に短縮すると待ち時間なく確認できる。

## 送信内容の詳細度制御

| 環境変数                              | 説明                                                                                                  |
| ------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| `OTEL_LOG_USER_PROMPTS`               | ユーザープロンプト本文をログに含めるか                                                                |
| `OTEL_LOG_ASSISTANT_RESPONSES`        | アシスタント応答本文を含めるか                                                                        |
| `OTEL_LOG_TOOL_DETAILS`               | Bashコマンド内容・MCPサーバー名等のツール詳細を含めるか                                               |
| `OTEL_LOG_TOOL_CONTENT`               | ツール入出力の内容まで含めるか(トレース有効化が前提)                                                  |
| `OTEL_LOG_RAW_API_BODIES`             | APIリクエスト/レスポンスの生ボディを含めるか。`file:<dir>` を指定するとボディ全文をファイル保存できる |
| `CLAUDE_CODE_OTEL_CONTENT_MAX_LENGTH` | OpenTelemetryのcontent系属性のトランケーション上限（デフォルト60KB）を変更する                        |

> **実地検証**: `OTEL_LOG_USER_PROMPTS` を設定しない状態(デフォルト)で `claude_code.user_prompt` / `claude_code.assistant_response` イベントを実際にLokiまで送信したところ、`prompt` / `response` 属性の値は文字列 `"<REDACTED>"` になっていた。`OTEL_LOG_USER_PROMPTS=1` を設定したコンソールエクスポータでの確認では、`prompt` 属性に実際のプロンプト文字列がそのまま載ることを確認した。デフォルトでは本文が伏せられる実装であることが実地で確認できている。

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

> **実地検証**: 単発 `claude -p` 実行(ツール未使用のQAのみ)では `session.count` / `cost.usage` / `token.usage` / `active_time.total` の4種が実際に出力された。残り4種(`lines_of_code.count` / `pull_request.count` / `commit.count` / `code_edit_tool.decision`)は該当する操作(コード編集・PR作成・コミット)を行っていないため出力されなかった。これはドキュメントとの相違ではなく、発生条件に依存するだけ。

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

> **実地検証**: 単発 `claude -p` 実行で実際に確認できたイベントは `plugin_loaded` / `user_prompt` / `api_request` / `assistant_response` / `mcp_server_connection`(claude.aiのリモートMCPへの接続/切断が単発実行でも自動的に発生する)。`-p` 実行では裏でセッションタイトル生成用の補助APIコール(`claude-haiku-4-5`)が走り、それも独立した `api_request` / `assistant_response` として記録される。`query_source` 属性の値(`generate_session_title` / `sdk` / `main` / `auxiliary`)で本処理由来のイベントと区別できる。

## 標準属性・実際に確認できた属性

ドキュメント上の「標準属性」一覧:

- `session.id`
- `app.version`
- `app.entrypoint`
- `organization.id`
- `user.account_uuid`
- `user.id`
- `user.email`
- `terminal.type`

> **実地検証**: 実際にコンソール/OTLP経由で出力された属性はこれより多い。共通属性として `user.account_id`(ドキュメント未記載)も含め全イベントに付与されていた。イベント個別の属性として `event.name` / `event.timestamp` / `event.sequence` / `prompt.id` / `message.uuid` / `request_id` / `client_request_id` / `query_source` / `effort` / `speed` / `model` / `cost_usd` / `cost_usd_micros` なども実際に確認できた(イベント種別によって付与される属性は異なる)。Lokiに取り込まれた後は、属性名のドット(`.`)がアンダースコア(`_`)に変換される(例: `event.name` → `event_name`)ことも実地で確認した。
>
> `tool_decision`イベントには`tool_source`属性(値: `builtin`/`mcp`等、ツールの出所を示す閉集合。v2.1.214以降)も付与される(公式ドキュメント由来、未実地検証)。

## 実地検証: コンソールエクスポータでの最小確認

外部コレクタなしで最短で動作確認したい場合の実際に機能した手順:

```
CLAUDE_CODE_ENABLE_TELEMETRY=1 \
OTEL_METRICS_EXPORTER=console \
OTEL_LOGS_EXPORTER=console \
OTEL_METRIC_EXPORT_INTERVAL=5000 \
OTEL_LOGS_EXPORT_INTERVAL=1000 \
OTEL_LOG_USER_PROMPTS=1 \
claude -p "1+1は?数字だけ答えて" --no-session-persistence
```

標準出力にイベント/メトリクスオブジェクトが整形されて流れる。親セッション自体の環境変数は変更せず、単発呼び出しに対してだけ環境変数を設定すること(親セッションのテレメトリ設定に影響を与えないため)。

## 実地検証: 子プロセスへの非伝播

`OTEL_*` 系の環境変数はBashツール・hook・MCPサーバーなどの子プロセスには伝播しない、という記述は `claude-logs-investigate/SKILL.md` に基づくものだが、**この項目はこの環境では実地検証できなかった**。

検証には `claude -p` セッション内でBashツールを実際に実行できる権限(またはそれに相当する分離環境)が必要だったが、以下いずれも実行環境のauto modeクラシファイアにより権限昇格とみなされブロックされた:

- `.claude/settings.local.json` を編集して一時的にBash許可を追加する
- 独立した `CLAUDE_CONFIG_DIR` を切って `--dangerously-skip-permissions` 相当で実行する

そのため、この項目は公式ドキュメント/既存スキル由来の未実地検証情報としてそのまま転記する。なお `CLAUDE_CONFIG_DIR` を切った際の副産物として、未認証の新規config dirでは `claude -p` が "Could not resolve authentication method" エラーになることを確認した(認証情報はconfig dirごとに保持されるため)。分離テスト手法([testing.md](testing.md))を使う際はこの点に注意する。

## 組織全体への強制配布

managed settings の `settings.json` の `env` キーに上記環境変数を設定すると、組織全体のClaude Codeインスタンスに強制適用できる(個人環境のため未実地検証。ドキュメント由来の情報)。管理側で`OTEL_EXPORTER_OTLP_ENDPOINT`を設定した場合、下位スコープの信号別上書きよりも管理設定側が優先される(以前はバグで信号別上書きがmanaged設定を上書きしてしまっていたが修正済み。ドキュメント由来の情報)。

## Agent SDKとの関係

Agent SDKはClaude Code CLIをそのまま子プロセスとして起動して使うため、CLI本体のOpenTelemetry計装をそのまま利用する。SDK自体が独自のテレメトリを生成するわけではなく、設定する環境変数もCLIと共通(ドキュメント由来の情報)。

## ローカル収集基盤(`otel-stack/`)

単発のコンソール出力を読むのではなく、継続的にクエリ可能なローカル専用の収集基盤(OTel Collector + Loki + Grafana)を`otel-stack/`配下に同梱している。テレメトリの向き先をいつでもこのローカル基盤に切り替えられる。

**このスタックは、さくらのクラウドVM上で恒常稼働している個人ログ基盤 `tools/infra/ai-logs/`(実利用ログを収集する別インフラ。Lokiのホットは14日保持で、それ以前はAzure Blobへ日次アーカイブする。詳細は[README.md](../../../tools/infra/ai-logs/README.md))とは無関係の別物である。** デバッグ用の実験的なテレメトリ(スキル動作確認のノイズ)を実利用アーカイブに混ぜないため、独立して使い捨てで起動・破棄する用途に限定している。設定内容は`ai-logs`の`docker/`を参考にしているが、コード・データともに共有しない。

### `ai-logs`との構成上の違い

| 項目             | `otel-stack/`(このスキル)                      | `tools/infra/ai-logs/`                                                 |
| ---------------- | ---------------------------------------------- | ---------------------------------------------------------------------- |
| 稼働場所         | ローカル(Docker Desktop)、使う時だけ起動       | さくらのクラウドVM、恒常稼働                                           |
| ポート公開       | 全ポートをループバック(`127.0.0.1`)のみに公開  | GrafanaはSSHトンネル経由のみ、OTLPは外部公開(トークン必須)             |
| OTLP受信の認証   | なし(`bearertokenauth` extension不使用)        | `bearertokenauth` extensionでBearerトークン必須                        |
| Lokiのホット公開 | あり(`127.0.0.1:3100`、直接クエリ用)           | なし(VM上のコンテナ間ネットワークのみ)                                 |
| 対象信号         | ログのみ                                       | ログのみ                                                               |
| ログの保持       | なし(使い捨て。`docker compose down -v`で消す) | Lokiは14日(Compactorのretention)、それ以前はAzure Blobの日次gzip JSONL |
| 対象ツール       | Claude Codeのデバッグ実験用途                  | Claude Code + Codex CLIの実利用ログ横断収集                            |

外部に一切公開しないループバック限定のローカル完結用途のため、VM公開を前提にした`bearertokenauth`のようなトークン認証機構は導入していない。認証はGrafanaの管理者パスワード(`.env`の`GRAFANA_ADMIN_PASSWORD`)のみに絞ってある。

### 起動手順

```
cd skills/plugins/cc-knowledge/skills/claude-code-debugging/otel-stack
cp .env.example .env   # GRAFANA_ADMIN_PASSWORD に任意のパスワードを設定
docker compose up -d
```

起動直後はLokiの `/ready` が「Ingester not ready: waiting for 15s after being ready」を返すことがある(Lokiの一般的な起動シーケンスで、Windows特有の挙動ではない)。実地検証では約15秒で `ready` になった。

health確認:

```
curl http://localhost:13133/          # Collector
curl http://localhost:3100/ready      # Loki
curl http://localhost:3000/api/health # Grafana
```

Claude Codeからこのローカル基盤へテレメトリを送る場合の環境変数(単発実行の例):

```
CLAUDE_CODE_ENABLE_TELEMETRY=1 \
OTEL_METRICS_EXPORTER=otlp \
OTEL_LOGS_EXPORTER=otlp \
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317 \
OTEL_EXPORTER_OTLP_PROTOCOL=grpc \
claude -p "..." --no-session-persistence
```

> **実地検証**: 上記の設定で送信したイベント(`user_prompt` / `api_request` / `assistant_response` / `mcp_server_connection`)が実際にLokiへ取り込まれ、Grafana UI(`admin` + `.env`のパスワードでログイン)経由・Grafanaのデータソースプロキシ経由・Lokiへの直接HTTPクエリの3経路いずれでも取得できることを確認した。

### Grafanaでの閲覧

`http://localhost:3000` を開き、`admin` / `.env`の`GRAFANA_ADMIN_PASSWORD`でログインする。データソースはLokiのみ、事前プロビジョニング済み。Explore画面で `{service_name="claude-code"}` を実行するとログが確認できる。

### Lokiへの直接クエリ(Grafana非経由)

Grafanaを経由せず、ホストから直接Loki HTTP APIへアクセスできることを実地確認済み。認証ヘッダは不要(ループバック限定公開の`auth_enabled: false`構成のため)。

```
# service_name の値一覧
curl "http://localhost:3100/loki/api/v1/label/service_name/values"

# 直近ログ取得(query_range)
curl -G "http://localhost:3100/loki/api/v1/query_range" \
  --data-urlencode 'query={service_name="claude-code"}' \
  --data-urlencode "limit=50"
```

このクエリ構築方法(`{service_name="..."}` によるLogQLクエリ、`query_range`のパラメータ設計)は `tools/infra/ai-logs/scripts/fetch_logs.py` と同じであり、そのまま踏襲できることを実地確認した。

同梱の [`scripts/query_otel_logs.py`](scripts/query_otel_logs.py) を使うと、上記のクエリをAI(Claude)自身が認証情報を直接扱わずにCLIから実行できる(`otel-stack/.env`をスクリプト自身が読み込む)。使い方は `python scripts/query_otel_logs.py --help` を参照。

### Lokiに取り込まれた際のラベル/属性の扱い

- Lokiでインデックス化される(検索の絞り込みに使われる)ラベルは `service_name`(値は常に `claude-code`)のみ
- `event_name` / `session_id` / `model` / `prompt_id` 等その他の属性は structured metadata として扱われ、インデックスには使われないが `query_range` のレスポンスの `stream` オブジェクトには一緒に返ってくるため、クエリ結果から普通に参照できる
- 属性名はOTLP送信時のドット区切り(例 `event.name`)から、Loki格納後はアンダースコア区切り(`event_name`)に変換される

### 停止・後片付け

```
docker compose down        # コンテナのみ削除、データは保持
docker compose down -v     # ボリューム(蓄積したログ)も削除
```

使い終わったら `docker compose down` でホストに常駐しない状態に戻すこと。継続的に使う場合は起動したままでよい(`ai-logs`とは異なりホストのリソースを消費し続ける点に注意)。

### 秘匿情報の扱い

`otel-stack/.env` の実体はコミットしない(`.env.example` のみコミット対象)。リポジトリ既存の `*.env` gitignoreルールで自動的に除外される。`scripts/query_otel_logs.py` は `.env` を読み込む処理を持つが、実際のクエリ経路はLoki直叩き(認証ヘッダなし)のため、現時点では読み込んだ値そのものは使わない。それでも `.env` から読み込む設計にしてあるのは、将来Grafana API経由のクエリに切り替える場合の拡張性と、秘匿情報の置き場所を一貫させておくため。
