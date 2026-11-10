# claude-code-debugging スキルについて

Claude Code自体（CLIツール）の挙動をデバッグ・検証するための包括スキル。このファイルは人間のメンテナ向けで、設計意図・ファイル間の役割分担・実地検証で見つかった特記事項をまとめる。Claudeが実行時に読むのは[SKILL.md](SKILL.md)であり、こちらは参照しない。

## なぜこのスキルがあるか

- 既存の`claude-logs-investigate`・`claude-settings`は「ログの所在」「settingsの書き方」など個別トピックの参考資料としては使えるが、hookでの実ログ仕込み・OTelでの継続収集・CLI分離テスト・巨大ログの抽出まで一気通貫でカバーする場所がなかった
- 「Claude Codeが期待通り動かない」ときに毎回複数スキルを行き来しなくて済むよう、判断・手順を一箇所に集約する目的で新規作成した

## なぜ既存スキルと内容を意図的に重複させたか（DRY非優先の背景）

`claude-logs-investigate`・`claude-settings`はこのスキルの作成時に参考資料として使ったが、要約したりそちらへの参照で済ませたりせず、[logs-and-settings.md](logs-and-settings.md)・[hooks-logging.md](hooks-logging.md)・[otel-reference.md](otel-reference.md)側に内容を意図的に重複して書き切っている（ユーザー明示指示）。

- 理由: デバッグ中にAIが複数スキルを行き来して情報を継ぎ接ぎするのはコストが高い。一箇所で完結させる網羅性を、DRY（重複排除）よりも優先した
- 代償: 参考元スキル（`claude-logs-investigate`/`claude-settings`/`writing-hooks`）の内容が将来更新されても、このスキルには**自動反映されない**。一次情報（公式ドキュメント本文・CLIヘルプ文言）だけは`claude-code-docs`/`claude-cli-docs`への参照に留めているため、そちらは最新化の恩恵を受ける
- 既存3スキル自体は変更・削除していない

## 各ファイルの役割分担

| ファイル                            | 役割                                                                                          | 執筆元ステップ       |
| ----------------------------------- | --------------------------------------------------------------------------------------------- | -------------------- |
| `SKILL.md`                          | 「何をしたいか→どのファイルを見るか」の決定表のみ。詳細本文は持たない                         | Step2雛形→Step11結線 |
| `logs-and-settings.md`              | 既存ログの所在・デバッグフラグ/スラッシュコマンド・settingsスコープ切り分け                   | Step1実験→Step2執筆  |
| `hooks-logging.md`                  | hook機構の全節転記＋実際に動作確認済みのログ仕込みテンプレート                                | Step3実験→Step4執筆  |
| `otel-reference.md`                 | OTel環境変数/メトリクス/イベント名の全量リファレンス＋ローカル収集基盤(`otel-stack/`)の使い方 | Step5実験→Step6執筆  |
| `otel-stack/`（Docker Compose一式） | OTel Collector + Loki + Grafanaのローカル収集基盤本体                                         | Step6                |
| `scripts/query_otel_logs.py`        | `otel-stack/`のLoki HTTP APIに直接クエリするCLI                                               | Step6                |
| `testing.md`                        | サブエージェント検証／Claude CLI完全分離テストの手法と使い分け                                | Step7実験→Step8執筆  |
| `scripts/extract_log.py`            | 巨大なtranscript/hookログ/debugログから該当行だけ抜き出すCLI（`aim`への受け渡し前段）         | Step9実験→Step10実装 |

各ドキュメントは、対応する実験ステップで実際にこの環境（Windows 11 / Claude Code v2.1.215）を動かして検証した結果を含む。検証で得た挙動は本文中に `> 実地検証:` として埋め込んである。バージョンが進むと再度乖離しうるため、致命的に見える相違に当たったら`claude-code-docs`/`claude-cli-docs`で最新化されていないか確認すること。

## 実地検証でドキュメントと実際の挙動が食い違っていた主な点

網羅的な一覧は各ファイル中の `> 実地検証:` を参照。特に踏み外しやすいものだけここに抜粋する。

- **hookのexit code 1は失敗扱いされない**。ブロックしたいなら`exit 2`必須（[hooks-logging.md](hooks-logging.md)の「入出力と制御」）。唯一の例外は`WorktreeCreate`で、ここだけ0以外の全コードでworktree作成が中止される
- **PowerShellフックで`${CLAUDE_PROJECT_DIR}`が展開されるのは二重引用符内のみ**。単一引用符内はリテラルのまま、`$env:`を付けない裸の`$CLAUDE_PROJECT_DIR`は未定義変数として空文字列になる（[hooks-logging.md](hooks-logging.md)の「Windows特有の落とし穴」）
- **exec formでも`.cmd`/`.bat`シム（npm等）が実際には起動できた**。ドキュメント上の「exec formでは実行ファイルのみ」という制約は、この環境・Node.jsバージョンでは再現しなかった（Node.jsのspawn時`.cmd`自動ラップの影響と推測、断定はしていない）
- **`~/.claude/debug/<uuid>.txt`は`--debug-file`を指定しなくても毎回自動生成される**。「通常は空」という想定と異なり、起動時ログが最初から書き出されている（[logs-and-settings.md](logs-and-settings.md)の「既存ログの所在」）
- **`~/.claude.json`は大文字小文字違いの重複キーを含みうる**ため、PowerShellの`ConvertFrom-Json`がそのままでは失敗する。`-AsHashtable`が必要（同上）
- **OTelの実送信属性はドキュメント記載より多い**（`user.account_id`等）。Loki取り込み後は属性名のドット(`.`)がアンダースコア(`_`)に変換される（[otel-reference.md](otel-reference.md)の「標準属性・実際に確認できた属性」）

## `otel-stack/`と`tools/infra/ai-logs/`の関係（別物であることの明記）

`otel-stack/`は、既に恒常稼働している`tools/infra/ai-logs/`（さくらのクラウドVM上で複数AIツール横断のログを収集する個人基盤。Lokiのホットは14日保持で、それ以前はAzure Blobへ日次アーカイブする。詳細は`tools/infra/ai-logs/README.md`）とは**目的が異なる別物**として独立に新設した。

|            | `tools/infra/ai-logs/`                                                    | `otel-stack/`（本スキル）                                                                        |
| ---------- | ------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| 目的       | 実利用ログを恒常的に収集・保管する個人基盤（ホット14日 + Blobアーカイブ） | スキル動作確認用の実験的テレメトリを都度確認する使い捨て基盤                                     |
| 稼働場所   | さくらのクラウドVM（常時稼働）                                            | ローカルのDocker Desktop（`docker compose up -d`で必要な時だけ起動）                             |
| 公開範囲   | VMへの外部公開（Bearer Token認証）                                        | `127.0.0.1`へのループバック公開のみ                                                              |
| 認証       | OTLP受信に`bearertokenauth`拡張                                           | Grafana管理者パスワードのみ（`.env`）。OTLP受信・Loki HTTP APIへの認証は無し（外部非公開のため） |
| クエリ経路 | SSHトンネル越しに`docker exec`でLokiへ（`fetch_logs.py`）                 | ローカルの`http://localhost:3100`へ直接HTTP（`query_otel_logs.py`）                              |
| 対象信号   | ログ（v1スコープ）                                                        | ログのみ（メトリクス・トレースは対象外）                                                         |

Collector/Lokiの設定内容は`tools/infra/ai-logs/docker/`を参考にしたが、共有・依存関係は一切ない。`otel-stack/`単体で完結し、`ai-logs`側の変更が本スキルに影響することはない。

## 前提条件（重要）

- `otel-stack/`を使うにはDocker Desktopが必要（実験ステップではDocker Desktop on Windowsで検証済み）
- `otel-stack/.env`は`otel-stack/.env.example`をコピーして作成する。存在しない場合Grafanaコンテナが起動時に失敗する
- `scripts/extract_log.py`・`scripts/query_otel_logs.py`はどちらも追加の pip 依存なし（標準ライブラリのみ）で動く

## 情報源と保守

- 一次情報の細部（公式ドキュメント本文・CLIヘルプの正確な文言）は`claude-code-docs`/`claude-cli-docs`スキルが正本。そちらが更新されても本スキルの転記内容には自動反映されないため、致命的な相違に気づいたら該当ファイルを手動で更新すること
- `CATALOG.md`は`lefthook.yml`のpre-commitフックが自動再生成するため、手動編集しない
- 既存の`claude-logs-investigate`/`claude-settings`との今後の統合可否は、このスキルの初版完成時点では検討していない（別タスクの対象）
