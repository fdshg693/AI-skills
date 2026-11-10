---
name: claude-logs-investigate
description: Claude Code自体(CLIツール)の動作ログ・デバッグ情報・テレメトリを調査する、または新たに記録する仕組みを仕込む際に使う。セッショントランスクリプトやシェルスナップショットなど既存ログの場所と見方に加え、デバッグフラグ・スラッシュコマンドでの原因切り分け、hookを使った独自ログの仕込み、OpenTelemetryによるテレメトリ送信設定までを扱う。「Claude Codeのログを見たい/調べたい」「なぜ設定やhook、MCPが効かないか調査したい」「ツール呼び出し履歴を記録したい」「テレメトリ/OTelを設定したい」といった要求で使う。
# hookそのものの書き方(イベント種別・stdin/stdout構造・exit code・settings.jsonへの登録方法)は writing-hooks スキルに依存・委譲する
meta:
  tag: []
  requires_repo_tools: none
  requires_env: CLAUDE_CODE_ENABLE_TELEMETRY, OTEL_METRICS_EXPORTER, OTEL_LOGS_EXPORTER, OTEL_EXPORTER_OTLP_ENDPOINT, OTEL_EXPORTER_OTLP_PROTOCOL
  dependencies: none
  requires_install: none
  requires_hooks: none
  requires_skills: writing-hooks, claude-code-docs, claude-cli-docs
  status: stable
  description: no description
  version: 1.0.1
---

# Claude Code ログ調査・仕込みスキル

Claude Code自体の挙動を、既存ログから調査する/新たに記録する仕組みを仕込む、の両面をカバーする。

## 何をしたいかで使うものを選ぶ

| したいこと                                       | 見る/使うもの                                                                                                                                                                               |
| ------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 過去の会話・ツール呼び出し内容を振り返りたい     | セッショントランスクリプト `~/.claude/projects/<project>/<session-id>.jsonl`。`/resume` で該当セッションを再開してもよい                                                                    |
| 設定・hook・MCPが反映されない原因を切り分けたい  | `/doctor` `/hooks` `/mcp` `/context` `/status` と `--safe-mode` / `CLAUDE_CONFIG_DIR` 分離起動                                                                                              |
| MCPサーバーとの通信(stderr)を見たい              | `claude --debug`(かつての `mcp` サブ引数は廃止され、統一された `--debug` でカバーされる)                                                                                                    |
| hookのマッチャー判定・実行結果を見たい           | `claude --debug`(かつての `hooks` サブ引数は廃止され、統一された `--debug` でカバーされる)または `CLAUDE_CODE_DEBUG_LOG_LEVEL=verbose`(詳細は writing-hooks スキルの `hooks.md` デバッグ節) |
| 特定のツール呼び出しを自分の形式で記録し続けたい | hookでログを追記する仕込み(下記「hookでのログ仕込み」。hookの書き方自体は writing-hooks スキルへ)                                                                                           |
| 使用状況を継続的に監視・BI/SIEMへ送りたい        | OpenTelemetry設定(下記「OpenTelemetryの仕込み」、詳細は [otel-reference.md](otel-reference.md))                                                                                             |

## 既存ログを見る

### `~/.claude/` 配下のログ関連パス

- `projects/<project>/<session-id>.jsonl` — セッショントランスクリプト本体。`<project>` は作業ディレクトリの絶対パスの非英数字を `-` に置換したもの。1行1JSONで、会話・ツール呼び出し・thinking・添付ファイル等が記録される(実体は内部形式でバージョン間に差異があるため、jqやgrepで特定フィールドを拾う使い方が安全)
  - 巨大なツール出力は同名の `<session-id>/tool-results/` ディレクトリに退避され、jsonl側には参照のみが残ることがある
- `sessions/<pid>.json` — 実行中セッションのプロセスレジストリ(`pid`, `sessionId`, `cwd`, `startedAt`, `version`, `entrypoint`, `name` など)。今どんなセッションが動いているかを機械的に知りたいときに見る
- `shell-snapshots/snapshot-bash-<timestamp>-<rand>.sh` — Bashツール起動時のシェル環境(関数・エイリアス・PATH等)のスナップショット
- `session-env/<session-id>/` — セッションごとの環境情報ディレクトリ
- `history.jsonl` — プロジェクト横断のプロンプト入力履歴(`display`, `project`, `sessionId`, `timestamp`)
- `debug/` — `--debug-file` 等で明示的にファイル出力させたデバッグログの書き出し先になり得るディレクトリ(通常は空)

補足:

- `CLAUDE_CONFIG_DIR` で `~/.claude` 自体の場所を変更できる(調査環境を汚したくない時の切り分けにも使える)
- 保持期間は `settings.json` の `cleanupPeriodDays`(デフォルト30日)
- `CLAUDE_CODE_SKIP_PROMPT_HISTORY` 環境変数、または非対話1回実行時の `--no-session-persistence` フラグでトランスクリプト書き込みを抑止できる
- hookやstatuslineには `transcript_path` フィールドが渡ってくるため、そこから該当セッションのjsonlパスを直接取得できる

### デバッグフラグ・スラッシュコマンドでの調査

- `-d, --debug [filter]` — カテゴリフィルタ付きデバッグモード。例: `"api,hooks"`(該当カテゴリのみ)、`"!1p,!file"`(除外指定)
- `--debug-file <path>` — デバッグログを指定ファイルに書き出す(暗黙的にdebugモードを有効化)
- `claude --debug` — MCPサーバーのstderr出力の確認(接続してもツールが0件、等の切り分けに有効)や、hookのマッチャー判定・終了コード・出力のライブトレースをカバーする(かつての `mcp`/`hooks` サブ引数は廃止され、統一された `--debug` にまとまった)
- `--safe-mode` — 全カスタマイズ(hook/MCP/skills等)を無効化して起動し、問題の切り分けを行う
- `CLAUDE_CONFIG_DIR=/tmp/claude-clean claude` — クリーンな設定ディレクトリで起動して切り分ける
- セッション内スラッシュコマンド:
  - `/context` — コンテキスト消費の内訳
  - `/doctor` — 設定の診断(不正なキー等の検出)
  - `/hooks` — 現在有効なhook設定の一覧
  - `/mcp` — MCP接続状態
  - `/permissions` — 有効な許可/拒否ルール
  - `/status` — どの設定ソース(managed/user/project/local)が効いているか
  - `/memory` — 読み込まれているCLAUDE.md/rules
  - `/debug [issue]` — セッション内でデバッグログを有効化

これらのコマンド・フラグの使い分けの詳細な使用手順は `debug-your-config` ドキュメント相当の内容であり、`claude-code-docs` スキル経由で最新の公式ドキュメントを参照できる。

## ログを仕込む

### hookでのログ仕込み

用途: 特定のツール呼び出し(例: 全Bashコマンド、全ファイル編集)を自分の形式でjsonl等に記録し、監査や分析に使う。

- `PreToolUse`/`PostToolUse` hookのstdinには `tool_name`, `tool_input`(`PostToolUse` はさらに `tool_response`), `session_id`, `transcript_path`, `cwd` などのJSONが渡ってくる
- 最小の考え方: hookコマンドでstdinをそのまま(または加工して)ログファイルに追記する

  ```
  python -c "import sys; open(r'C:\path\to\tool-log.jsonl','a',encoding='utf-8').write(sys.stdin.read()+chr(10))"
  ```

- hookの種類(PreToolUse/PostToolUse/Stop等の全イベント)、`type`(command/http/mcp_tool/prompt/agent)、settings.jsonへの登録方法、exit codeの意味、matcherの正規表現の罠、Windows/PowerShell特有の注意点、そして **hook自体のデバッグ方法(`--debug-file`, `CLAUDE_CODE_DEBUG_LOG_LEVEL=verbose` の詳細)** は `writing-hooks` スキル(`hooks.md`)に既に整理されているため、hookの書き方そのものはそちらに従うこと。

### OpenTelemetryの仕込み

Claude Codeは使用状況(メトリクス・ログ・イベント、betaでトレース)をOpenTelemetryで外部に送信できる。CI/監視基盤やSIEMに継続的に流したい場合はこちら。

- 有効化には `CLAUDE_CODE_ENABLE_TELEMETRY=1` が必須
- 最小構成の例:

  ```
  CLAUDE_CODE_ENABLE_TELEMETRY=1
  OTEL_METRICS_EXPORTER=otlp
  OTEL_LOGS_EXPORTER=otlp
  OTEL_EXPORTER_OTLP_ENDPOINT=https://your-collector:4317
  OTEL_EXPORTER_OTLP_PROTOCOL=grpc
  ```

- 送信するイベントの詳細度(ユーザープロンプト本文・応答本文・ツール詳細・APIボディ生データまで含めるか等)は個別の環境変数で制御する。組織で全体に強制するにはmanaged settingsの `env` キーを使う
- **`OTEL_*` 系の環境変数はBashツール・hook・MCPサーバーなどの子プロセスには伝播しない**(子プロセス側で独自に計装する必要がある)
- Agent SDKはCLIをそのまま子プロセスとして使うため、CLIと同じ環境変数でテレメトリが計装される(SDK自体が別のテレメトリを生成するわけではない)
- 全メトリクス名・全イベント名・標準属性・カーディナリティ制御用の環境変数の網羅的な一覧は [otel-reference.md](otel-reference.md) を参照

## 参照

- [otel-reference.md](otel-reference.md) — OTel環境変数・メトリクス名・イベント名の全量リファレンス
- `writing-hooks` スキル — hookの書き方・登録方法・デバッグ方法の詳細
- `claude-code-docs` スキル — 上記の元になっている公式ドキュメント(`monitoring-usage`, `sessions`, `debug-your-config` 等)の最新版を直接参照したい場合
- `claude-cli-docs` スキル — `--debug`/`--debug-file`/`--verbose` などCLIフラグの正確な説明文
