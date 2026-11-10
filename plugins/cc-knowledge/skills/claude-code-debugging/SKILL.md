---
# このスキルの設計意図（DRY非優先の背景）・ファイル間の役割分担・実地検証で見つかった相違点の一覧は同階層のREADME.md参照（人間のメンテナ向け）
# 同梱ファイル: logs-and-settings.md（既存ログ所在・デバッグフラグ/スラッシュコマンド・settings切り分け）/ hooks-logging.md（hookでのログ仕込み）/ otel-reference.md（OpenTelemetry。otel-stack/にローカル収集基盤一式、scripts/query_otel_logs.pyにクエリCLIを同梱）/ testing.md（サブエージェント/CLI分離でのテスト手法）/ scripts/extract_log.py（巨大ログの抽出）
# 依存: 一次情報の細部（公式ドキュメント本文・CLIヘルプの正確な文言）のみ claude-code-docs / claude-cli-docs スキルに委譲する。hookの書き方（イベント種別・stdin/stdout構造・exit code・settings.jsonへの登録方法）を含め、それ以外は全て本スキル配下に転記・保持する
# 参考: claude-logs-investigate / claude-settings スキルは本スキル作成時の参考資料。あえて要約・委譲せず内容を本スキル配下に重複して書き切っている（DRYより網羅性を優先。両スキル自体は変更しない）
name: claude-code-debugging
description: Claude Code自体（CLIツール）のデバッグを一箇所で完結させたい時に使う。既存ログの所在・読み方、デバッグフラグ・スラッシュコマンドでの切り分け、settings起因の不具合切り分け、hookを使ったログの仕込み方、OpenTelemetryでの計装、サブエージェント/CLI分離でのテスト手法、巨大ログの抽出+aim CLIでの要約まで扱う。「Claude Codeがなぜ期待通り動かないか調べたい」「hookやOTelでログを仕込みたい」「セッションログを抽出して分析したい」といった要求で使う。
allowed-tools: Bash(python ${CLAUDE_SKILL_DIR}/scripts/*.py *)
meta:
  tag: []
  requires_repo_tools: none
  requires_env: none
  dependencies: none
  requires_install: none
  requires_hooks: none
  requires_skills: claude-code-docs, claude-cli-docs
  status: stable
  description: no description
  version: 1.0.1
---

# Claude Codeデバッグ包括スキル

Claude Code自体（CLIツール）の挙動を調査・検証するための情報を一箇所にまとめる。非常に細かい一次情報（公式ドキュメント本文・CLIヘルプの正確な文言）だけは `claude-code-docs` / `claude-cli-docs` スキルに譲り、それ以外はこのスキル配下のファイルで対応。

## 何をしたいかで見るものを選ぶ

| したいこと                                                                                 | 見る/使うもの                                                                                                                                                            |
| ------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 既存のセッションログ・トランスクリプトを振り返りたい                                       | [logs-and-settings.md](logs-and-settings.md) の「既存ログの所在」                                                                                                        |
| デバッグフラグ・スラッシュコマンドで設定/hook/MCPの不具合を切り分けたい                    | [logs-and-settings.md](logs-and-settings.md) の「デバッグフラグ・スラッシュコマンド」                                                                                    |
| settingsのスコープ・優先順位起因の不具合を切り分けたい                                     | [logs-and-settings.md](logs-and-settings.md) の「settingsスコープ」                                                                                                      |
| hookで特定のツール呼び出しを自分の形式でログに記録し続けたい                               | [hooks-logging.md](hooks-logging.md)（hook機構全体・実際に動作確認済みのテンプレート）                                                                                   |
| 使用状況を継続的にOpenTelemetryで外部（監視基盤/SIEM）に送りたい                           | [otel-reference.md](otel-reference.md)                                                                                                                                   |
| OTelイベントをローカルで継続的に集約・クエリしたい（コンソール出力を都度読むのをやめたい） | [otel-reference.md](otel-reference.md) の「ローカル収集基盤」節。`otel-stack/`で`docker compose up -d`→ `${CLAUDE_SKILL_DIR}/scripts/query_otel_logs.py logs --since 1h` |
| hook/OTel/skillの変更が実際に効いているかをサブエージェントやCLI分離起動で検証したい       | [testing.md](testing.md)                                                                                                                                                 |
| 巨大なセッションログ(jsonl)から必要な部分だけ抜き出し、`aim` CLI等で要約したい             | `${CLAUDE_SKILL_DIR}/scripts/extract_log.py`（使い方は [testing.md](testing.md) の抽出節、または直接 `--help`）                                                          |

## 前提として知っておくこと

- ここでの「デバッグ」対象は常に **Claude Code自体（CLIツール）の挙動** であり、ユーザーのプロジェクトコードのデバッグではない
- 各ファイルの記述は実際にこの環境（Windows）で動かして検証した結果を含む。ドキュメント上の記載と実際の挙動が食い違っていた点は各ファイル内に明記してある（バージョンが進むと再度乖離する可能性があるため、致命的に見える相違は `claude-code-docs` / `claude-cli-docs` で最新化されていないか確認すること）
- `claude-logs-investigate` ・ `claude-settings` ・ `writing-hooks` スキルは本スキルの作成時に参考にしたが、内容は独立して重複保持している。あちらを更新しても本スキルには自動反映されない

## 参照

- `claude-code-docs` スキル — `monitoring-usage` / `sessions` / `debug-your-config` 等、公式ドキュメントの最新版
- `claude-cli-docs` スキル — `--debug` / `--debug-file` / `--safe-mode` 等CLIフラグの正確な文言
- `writing-hooks` スキル — 本スキルの`hooks-logging.md`作成時に参考にした一次情報源（内容は`hooks-logging.md`側に転記・保持済み）
- `my-tools:aim-cli` スキル — `aim` CLIでの単発モデル呼び出し・モデル選定
