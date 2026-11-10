# ログなどを使ったデバッグ方法

出典: `docs/cli/reference/output-format.md`, `docs/cli/reference/slash-commands.md`, `docs/cli/using.md`, `docs/cli/headless.md`, `docs/agent/debug-mode.md`, `docs/agent/security/run-modes.md`, `docs/cli/reference/configuration.md`, `docs/cli/reference/parameters.md`

このトピックは2種類に分けて整理する必要がある。(A) **CLI/スクリプトの実行自体をデバッグする**方法と、(B) **エージェントに「コードのバグ」をデバッグさせる** Debug Mode 機能。

## A. CLI 実行のデバッグ

### 対話モードでの調査コマンド

| コマンド                                                   | 内容                                                                                                 |
| ---------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| `/logs`                                                    | デバッグログのパスを表示し、クリップボードにコピー                                                   |
| `/about`                                                   | CLI バージョン・システム・アカウント情報を表示（クリップボードにもコピー）                           |
| `/copy-request-id`                                         | 直近のリクエスト ID をコピー                                                                         |
| `/copy-conversation-id`                                    | 現在の会話 ID をコピー                                                                               |
| `agent status --format json` / `agent about --format json` | 認証状態・バージョン情報を JSON で取得（`status`, `about` コマンドのみ `--format` オプションを持つ） |

サポート問い合わせやバグ報告時は `/copy-request-id` と `/logs` のパスをセットで使うと良さそう。

### 非対話（headless / print）モードでの構造化ログ

`--print`（`-p`）と組み合わせる `--output-format` で3種類（`docs/cli/reference/output-format.md`）:

| フォーマット         | 用途                                                                                                                                         |
| -------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| `text`（デフォルト） | 最終応答のみ。スクリプトで「答えだけ」欲しい時                                                                                               |
| `json`               | 完了後に1つの JSON オブジェクト（`type/subtype/is_error/duration_ms/result/session_id/request_id`）。失敗時は非0終了 + stderr、JSON は出ない |
| `stream-json`        | NDJSON。`system(init)` → `user` → `assistant`（メッセージ単位）→ `tool_call(started/completed)` → 終端 `result` の順でイベントが流れる       |

`--stream-partial-output` を `stream-json` と併用すると文字単位のデルタが `assistant` イベントとして追加で流れる。`timestamp_ms` あり & `model_call_id` なし のイベントだけが新規テキスト（他はツール呼び出し前のバッファ flush か、ターン終了時の重複 flush なので無視する）。

`system` init イベントには `apiKeySource`（`env|flag|login`）、`cwd`、`model`（表示名）、`permissionMode` が入っており、「どの認証経路・どのモデル・どの権限モードで動いたか」をログから追える。`tool_call` イベントは `readToolCall` / `writeToolCall` / 汎用 `function` の3系統で、started/completed のペアを `call_id` で突き合わせられる。

CI 等でのデバッグには `stream-json` を `jq` でパースしてツール呼び出しと結果を逐次ログに残す、または `json` で `is_error` / `duration_ms` を見て pass/fail をゲートするパターンが `docs/cli/headless.md` のサンプルスクリプトに載っている。

### セッション履歴からのデバッグ

- `--resume [chatId]` / `--continue`（`--resume=-1` のエイリアス）/ `agent resume` / `agent ls`（過去チャット一覧から選んで再開）
- `/resume`, `/rewind`（過去メッセージまで巻き戻す）, `/fork`（現在のチャットを新セッションに分岐）
- 「さっき何が起きたか」を再現・追跡する際にまず履歴を辿る手段として使える。

### Sandbox / Worker 固有のデバッグフラグ

- `agent sandbox run --sb-debug`: サンドボックスのデバッグログを一時フォルダに書き出し、パスを表示。
- `agent worker debug`: プライベートクラウドワーカーの認証・プライバシー・ルーティングの preflight 診断（`--json` で JSON 出力可）。
- `agent worker --debug`: bridge モード開始前に診断情報を表示。`worker start --verbose` は起動ログを詳細化。
- `CURSOR_SANDBOX_LANDLOCK_STATUS`（Linux, サンドボックス内の環境変数）: `fully_enforced`（Landlock）か `bubblewrap`（フォールバック）かを報告 — サンドボックスがなぜ想定と違う動きをするかの診断に使える。

### 設定ファイルが壊れた場合

`cli-config.json` の JSON が壊れている場合、CLI は自動で欠損フィールドを自己修復するが、深刻な破損時は `.bad` にバックアップして再作成される。手動で直す場合は該当ファイルをどけて再起動:

```bash
mv ~/.cursor/cli-config.json ~/.cursor/cli-config.json.bad
```

## B. Debug Mode（エージェントによるコードのバグ調査支援機能）

出典: `docs/agent/debug-mode.md`。CLI でも `/debug [prompt]` で切り替え可能（エディタと共通機能）。

再現できるが原因不明のバグ、競合状態、パフォーマンス問題、リグレッションに強い。フロー:

1. 関連ファイルを探索し、複数の仮説を立てる
2. ログ出力（instrumentation）をコードに仕込む — Cursor 拡張内で動くローカル debug サーバーにデータを送る
3. ユーザーに再現手順を提示し、実際に再現してもらう
4. 収集したログを解析して実際の根本原因を特定
5. 根本原因にピンポイントで対応する最小限の修正
6. 再現手順で修正を検証し、仕込んだ instrumentation を全て除去

ユーザー側のコツ: エラーメッセージ・スタックトレース・再現手順を具体的に伝える、再現手順に忠実に従う、期待動作と実際の動作の差を明確に説明する。

`Shift+Tab` でモードローテーション、または `/debug` で切り替え。
