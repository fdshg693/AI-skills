---
name: codex-logs
description: >-
  OpenAI Codex（CLI・IDE 拡張・app-server）のローカルに残るセッションログ
  （~/.codex/sessions の rollout-*.jsonl、archived_sessions、history.jsonl、
  state_5.sqlite の threads 索引）の所在とレコード形式を説明する。「Codex の過去の
  セッションを探したい」「Codex のトークン使用量を集計したい」「rollout ファイルの
  形式・圧縮（.jsonl.zst）を知りたい」「セッションとプロジェクトを対応付けたい」
  ときに使う。Codex の機能全般・設定は対象外（codex-docs を使う）。
meta:
  tag: []
  requires_repo_tools: none
  requires_env: CODEX_HOME
  dependencies: none
  requires_install: none
  requires_hooks: none
  requires_skills: codex-docs
  status: experimental
  description: Codexのローカルセッションログ（rollout）の所在と形式。実データ未確認、公式とソースが根拠
  version: 1.0.0
---

# Codex のローカルセッションログ（rollout）

OpenAI Codex がローカルに残すセッションログの所在・形式・読み方の注意をまとめたスキル。CLI・IDE 拡張（VS Code 等）・app-server は同じ `CODEX_HOME` を共有する。

**このスキルは実データで確かめていない。** 内容は公式ドキュメントと openai/codex のソース（`main` のコミット `885a1df`）から読み取ったもので、各項目の根拠の種類は「[根拠と確認バージョン](#根拠と確認バージョン)」で区別している。公式ドキュメントに書かれていない形式はリリースで予告なく変わる。公式も hooks の `transcript_path` の形式は安定インターフェースではないとしている。

## 所在

ルートは `CODEX_HOME`（既定 `~/.codex`）。

| OS            | 既定のルート           |
| ------------- | ---------------------- |
| Windows       | `%USERPROFILE%\.codex` |
| macOS / Linux | `$HOME/.codex`         |

- `CODEX_HOME` で上書きできる。指定先のディレクトリは事前に作っておく必要がある。
- SQLite の置き場所は config の `sqlite_home` → 環境変数 `CODEX_SQLITE_HOME` → `CODEX_HOME` の順で決まる。相対パスはカレントディレクトリ基準。
- WSL 上で動かした場合は Linux 側の `~/.codex` になるはずだが未確認（[未確認事項](#未確認事項)）。

ルート配下の主なファイル（公式文書が挙げるのは `config.toml`・`auth.json`・`history.jsonl` だけで、残りはソース由来）:

| パス                                                                    | 内容                                                                 |
| ----------------------------------------------------------------------- | -------------------------------------------------------------------- |
| `sessions/YYYY/MM/DD/rollout-YYYY-MM-DDThh-mm-ss-<thread_uuid>.jsonl`   | セッション本体（rollout）                                            |
| 同上 `rollout-<ts>-<thread_uuid>_<rollout_uuid>.jsonl`                  | revert（巻き戻し）したスレッドの別 rollout                           |
| 同上 `*.jsonl.zst`                                                      | 7 日以上前の rollout を zstd 圧縮したもの                            |
| `archived_sessions/rollout-*.jsonl[.zst]`                               | アーカイブ済み。日付ディレクトリは無く平置き                         |
| `history.jsonl`                                                         | ユーザー入力だけの履歴                                               |
| `session_index.jsonl`（+`.lock`）                                       | スレッド名の索引                                                     |
| `state_5.sqlite`                                                        | スレッドのメタデータ索引（`threads` 表）                             |
| `thread_history_1.sqlite`                                               | paginated モードの turn/item の投影                                  |
| `logs_2.sqlite`                                                         | 診断ログ（tracing）                                                  |
| `log/codex-tui.log`                                                     | 平文の TUI ログ。`log_dir` を明示したときだけ書く opt-in（公式記載） |
| `thread-writer-locks/<thread_id>.lock`、`.tmp/rollout-compression.lock` | ロックファイル                                                       |
| `auth.json`                                                             | 認証情報。**読まない**                                               |

`codex exec --ephemeral` で動かしたセッションは rollout を書かない（公式記載）。

## 保存系統と正本

| 系統                                         | 中身                                        | 位置づけ                                     |
| -------------------------------------------- | ------------------------------------------- | -------------------------------------------- |
| rollout（`sessions/`・`archived_sessions/`） | 会話・ツール呼び出し・トークン数の全記録    | **正本**                                     |
| `state_5.sqlite` の `threads`                | cwd・タイトル・モデル・累計トークン等のメタ | 一覧用の索引。rollout から再構築できる派生物 |
| `session_index.jsonl`                        | スレッド名                                  | 索引                                         |
| `history.jsonl`                              | ユーザー入力の文字列だけ                    | 入力履歴。会話の再構成には使えない           |
| `thread_history_1.sqlite`                    | paginated モードの turn/item                | rollout の投影（派生物）                     |
| `logs_2.sqlite`・`log/`                      | 診断ログ                                    | 会話ログではない                             |

一覧はまず `state_5.sqlite` から作り、DB が無い・壊れているときは各 rollout の先頭行（`session_meta`）だけを読んで代わりにするのが速い。

### legacy モードと paginated モード

rollout の書き方には 2 つのモードがあり、`session_meta.payload.history_mode`（`legacy`／`paginated`、省略時は legacy）で分かる。

| 観点                     | legacy                                                                         | paginated                                                                 |
| ------------------------ | ------------------------------------------------------------------------------ | ------------------------------------------------------------------------- |
| 行の `ordinal`           | 省略されうる                                                                   | 付く                                                                      |
| 発話の記録               | `response_item.message` と `event_msg.user_message`/`agent_message` の**二重** | `response_item` だけ                                                      |
| コマンド実行・MCP の結果 | `event_msg`（`patch_apply_end`・`mcp_tool_call_end` 等）                       | `event_msg.item_completed`（`item` は TurnItem、出力は 64KiB で切り詰め） |

- legacy で発話を数えるときは `response_item` 側に寄せ、`event_msg.user_message`/`agent_message` は数えない。
- legacy から paginated への移行（起動時、または `codex migrate-rollouts --apply`）は rollout を書き直して差し替える。差し替え中は `.pending` ジャーナルが残る。
- 新規スレッドの既定がどちらか、自動移行がいつ走るかは未確認。

## レコード構造

### rollout の外枠

JSONL で 1 行 1 オブジェクト。

| フィールド  | 型                   | 説明                                        |
| ----------- | -------------------- | ------------------------------------------- |
| `timestamp` | 文字列               | UTC の ISO 8601、ミリ秒、`Z` 付き。常にある |
| `ordinal`   | 整数（任意）         | paginated モードで付く通し番号              |
| `type`      | 文字列（snake_case） | レコード種別。常にある                      |
| `payload`   | オブジェクト         | 種別ごとの中身。常にある                    |

### `type` の種類

| type                                                                                               | payload の要点                                                                                                                                                                                                                                                                                                                                                                                                                     |
| -------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `session_meta`                                                                                     | 先頭行。必須: `id`（thread UUID）・`timestamp`・`cwd`・`originator`・`cli_version`・`model_provider`（null 可）・`base_instructions`（null 可）。任意: `session_id`（無ければ `id`）・`source`・`thread_source`・`forked_from_id`・`parent_thread_id`・`agent_nickname`・`agent_role`（旧名 `agent_type`）・`agent_path`・`history_mode`・`git`（`commit_hash`/`branch`/`repository_url`）・`dynamic_tools`・`context_window` など |
| `turn_context`                                                                                     | ターンごと。必須: `cwd`・`approval_policy`・`model`、および `permission_profile` か旧形式の `sandbox_policy`。任意: `turn_id`・`root_turn_id`・`effort`・`summary`・`collaboration_mode` など。**モデル名はここから取る**（ターンごとに変わりうる）                                                                                                                                                                                |
| `response_item`                                                                                    | payload は Responses API の item そのもの（下記）。外枠に任意の `metadata`（`history_sequence` 等）が付く                                                                                                                                                                                                                                                                                                                          |
| `event_msg`                                                                                        | payload は `{"type": <イベント名>, ...}`（下記）                                                                                                                                                                                                                                                                                                                                                                                   |
| `compacted`                                                                                        | コンテキスト圧縮。`message`（要約本文）・`replacement_history`（任意）・`window_id`・`latest_token_usage_record` など                                                                                                                                                                                                                                                                                                              |
| `token_usage_record`                                                                               | 新しい形式のレスポンス単位の使用量。`thread_id`・`turn_id`・`session_id`・`root_turn_id`・`response_id`・`usage`・`turn_token_usage`・`thread_token_usage`                                                                                                                                                                                                                                                                         |
| `inter_agent_communication`、`inter_agent_communication_metadata`                                  | サブエージェント間のメッセージ                                                                                                                                                                                                                                                                                                                                                                                                     |
| `world_state`・`retained_context`・`security_risk_score`・`dynamic_tools_updated`・`realtime_item` | 補助情報（`realtime_item` は paginated のみ）                                                                                                                                                                                                                                                                                                                                                                                      |

未知の `type`・フィールドは無視して読み進める（ソース側も `#[serde(other)]` で未知値を許している）。

### `response_item.payload.type`

| type                                           | 主なフィールド                                                                                                                                                                       |
| ---------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `message`                                      | `role`（`user`/`assistant`/`developer`/`system`）、`content[]`（`{type:"input_text"\|"output_text", text}`・`input_image` 等）、任意の `phase`（`commentary`/`final_answer`）        |
| `reasoning`                                    | `summary[]`（`{type:"summary_text", text}`）、`encrypted_content`、任意の `content`                                                                                                  |
| `function_call`                                | `name`、任意の `namespace`、`arguments`（**JSON 文字列**。もう一度パースする）、`call_id`                                                                                            |
| `function_call_output`                         | `call_id`、`output`（文字列、または content item の配列）                                                                                                                            |
| `custom_tool_call` / `custom_tool_call_output` | `name`・`input`・`call_id` / `call_id`・`output`                                                                                                                                     |
| `local_shell_call`                             | `call_id`・`status`・`action`                                                                                                                                                        |
| その他                                         | `tool_search_call`/`tool_search_output`・`web_search_call`・`image_generation_call`・`agent_message`・`compaction`・`context_compaction`・`additional_tools`・`configuration_update` |

ツール呼び出しと結果は `call_id` で突き合わせる。`role=developer`/`system` のメッセージや、AGENTS.md・環境情報を差し込んだ user メッセージ（`<environment_context>` 等のタグで始まる。推定）は人間の発話ではない。

### rollout に書かれる `event_msg`

- 常に書かれる: `token_count`、`task_started`（別名 `turn_started`）、`task_complete`（別名 `turn_complete`）、`turn_aborted`、`thread_rolled_back`、`thread_goal_updated`、`thread_settings_applied`、`item_completed`（legacy では一部のみ）。
- legacy モードだけ: `user_message`（`message`・`images`）、`agent_message`（`message`・`phase`）、`agent_reasoning`、`agent_reasoning_raw_content`、`patch_apply_end`、`mcp_tool_call_end`、`web_search_end`、`image_generation_end`、`context_compacted`、`entered_review_mode`/`exited_review_mode`、`sub_agent_activity`。
- 書かれない: `exec_command_begin`/`exec_command_end`、ストリーミングの delta。
- `task_complete` のフィールド: `turn_id`、`last_agent_message`、任意で `started_at`/`completed_at`（epoch）・`duration_ms`・`error`。

### トークン使用量

TokenUsage は `{input_tokens, cached_input_tokens, cache_write_input_tokens（既定 0）, output_tokens, reasoning_output_tokens, total_tokens}`。

`event_msg` の `token_count`:

```text
{type:"token_count",
 info: null | {total_token_usage, last_token_usage, last_usage_includes_reasoning?, model_context_window},
 rate_limits: null | {limit_id, primary, secondary, credits, plan_type, ...}}
```

- **`total_token_usage` はスレッドの累積値。** セッションの合計は最後の `total_token_usage` を使う。`last_token_usage`（直前の 1 リクエスト分）や各行の `total_*` を足し上げると二重計上になる。
- `info` が null の行は飛ばす。同じ値の行が連続することもある。
- `token_usage_record` がある新しい形式では、そちらがレスポンス単位で正確。
- **金額（コスト）のフィールドは無い。** 料金表から自分で計算する。

### 架空値の最小例（legacy モード）

```jsonl
{"timestamp":"2026-01-02T03:04:05.678Z","type":"session_meta","payload":{"id":"00000000-0000-7000-8000-000000000001","timestamp":"2026-01-02T03:04:05.678Z","cwd":"C:\\work\\demo","originator":"codex_cli_rs","cli_version":"0.0.0","source":"cli","model_provider":"openai","base_instructions":null,"git":{"branch":"main"}}}
{"timestamp":"2026-01-02T03:04:06.000Z","type":"turn_context","payload":{"turn_id":"t1","cwd":"C:\\work\\demo","approval_policy":"on-request","sandbox_policy":{"type":"read-only"},"model":"<model>","effort":"medium"}}
{"timestamp":"2026-01-02T03:04:06.100Z","type":"event_msg","payload":{"type":"task_started","turn_id":"t1"}}
{"timestamp":"2026-01-02T03:04:06.200Z","type":"response_item","payload":{"type":"message","role":"user","content":[{"type":"input_text","text":"<text>"}]}}
{"timestamp":"2026-01-02T03:04:06.210Z","type":"event_msg","payload":{"type":"user_message","message":"<text>","images":[]}}
{"timestamp":"2026-01-02T03:04:07.000Z","type":"response_item","payload":{"type":"function_call","name":"shell","arguments":"{\"command\":[\"<cmd>\"]}","call_id":"call_1"}}
{"timestamp":"2026-01-02T03:04:08.000Z","type":"response_item","payload":{"type":"function_call_output","call_id":"call_1","output":"<output>"}}
{"timestamp":"2026-01-02T03:04:09.000Z","type":"response_item","payload":{"type":"message","role":"assistant","content":[{"type":"output_text","text":"<text>"}],"phase":"final_answer"}}
{"timestamp":"2026-01-02T03:04:09.100Z","type":"event_msg","payload":{"type":"token_count","info":{"total_token_usage":{"input_tokens":100,"cached_input_tokens":0,"output_tokens":20,"reasoning_output_tokens":5,"total_tokens":120},"last_token_usage":{"input_tokens":100,"cached_input_tokens":0,"output_tokens":20,"reasoning_output_tokens":5,"total_tokens":120},"model_context_window":200000},"rate_limits":null}}
{"timestamp":"2026-01-02T03:04:09.200Z","type":"event_msg","payload":{"type":"task_complete","turn_id":"t1","last_agent_message":"<text>"}}
```

4・5 行目が legacy モードの二重記録の例。`sandbox_policy`・`source`・`originator` の具体的な表現は推定（サブエージェントの `source` は `{"subagent":{"thread_spawn":{"parent_thread_id":"…","depth":1}}}` の形と推定）。

### 補助ファイル

- **`history.jsonl`**: 1 行 `{"session_id":"<uuid>","ts":<unix 秒>,"text":"<入力>"}`。ユーザー入力だけ。
- **`session_index.jsonl`**: 1 行 `{"id":"<thread uuid>","thread_name":"<名前>","updated_at":"<ISO>"}`。追記型なので同じ `id` の最後の行が有効。
- **`state_5.sqlite` の `threads` 表**: `id`、`rollout_path`、`created_at[_ms]`、`updated_at[_ms]`、`source`、`model_provider`、`cwd`、`title`、`sandbox_policy`、`approval_mode`、`tokens_used`、`has_user_event`、`archived`、`archived_at`、`git_sha`/`git_branch`/`git_origin_url`、`cli_version`、`first_user_message`、`agent_nickname`/`agent_role`/`agent_path`、`model`、`reasoning_effort`、`thread_source`、`preview`、`recency_at[_ms]`、`history_mode`、`name`、`project_id`。親子関係は `thread_spawn_edges(parent_thread_id, child_thread_id, status)`。ほかに `projects`・`project_roots(path)`。
- **`thread_history_1.sqlite`**: `thread_turns(thread_id, turn_id, rollout_ordinal, status, started_at, completed_at, duration_ms, …)`、`thread_items(thread_id, turn_id, item_id, rollout_ordinal, created_at_ms, item_json)`。
- **`logs_2.sqlite`**: `logs(ts, ts_nanos, level, target, message, module_path, file, line, thread_id, process_uuid, …)`。

## セッション⇔プロジェクト対応

- パスのエンコードやハッシュは使わない。cwd は `session_meta.payload.cwd` に絶対パスの生値で入る（Windows では `C:\\...`）。プロジェクト単位にまとめるときは大文字小文字と区切り文字を揃える。
- `turn_context.cwd` もターンごとに入り、セッション中に変わりうる。
- `state_5.sqlite` の `threads.cwd` と `threads.rollout_path` から一覧を高速に作れる（インデックス `idx_threads_archived_cwd_recency_at_ms` あり）。
- git 情報は `session_meta.payload.git` または `threads.git_*`。
- セッション ID は `session_meta.payload.id`。ファイル名の UUID と一致する（revert の rollout は `_` の前の部分）。
- タイトルは `session_index.jsonl` の `thread_name` → `threads.name`/`title` → 最初の user メッセージの順で探す。
- 親子関係は `parent_thread_id`、`source.subagent.thread_spawn.parent_thread_id`、`forked_from_id`、または `thread_spawn_edges`。
- **時刻の注意**: 日付ディレクトリとファイル名の時刻は**ローカル時刻**で、行の `timestamp` は UTC。ソース内のファイル名パーサーは UTC と仮定しているので、ファイル名を開始時刻の正本にせず `session_meta.payload.timestamp` を使う。

## 読み取り安全性・保持期間

- 読むだけにする。rollout・DB を書き換えたり消したりしない。
- rollout は実行中に追記される。末尾行が途中まで書かれた JSON になりうるので、最終行のパース失敗は読み飛ばす。各行が dict であることも確かめる。
- 書き込みは `thread-writer-locks/<id>.lock` で排他されている。読み取り側にロックは要らないと推定。
- **圧縮**: 圧縮ワーカーが 7 日以上前の rollout を `.jsonl.zst` に置き換え、元の `.jsonl` を消す（起動時、6 時間ごとのマーカー付き）。走査中に元ファイルが消えることがあるので、見つからなければ `.zst` 側を開き直す。
- **zstd の読み込み**: Python の標準ライブラリで zstd が読めるのは 3.14 の `compression.zstd` から。それより前は `zstandard` などの外部パッケージが要る。読めない環境では `.zst` をスキップして警告する。
- 走査は `sessions/` と `archived_sessions/` の両方。圧縮・移行の一時ファイル（`.tmp`・`.pending`・staged）は除外する。
- SQLite は Codex 側が WAL・`busy_timeout` 5 秒で開いている。読むときは `mode=ro` の URI で開き、失敗したら `immutable=1`。ただし immutable では WAL 内の未チェックポイント分が見えない。
- **保持期間**: rollout に自動削除は無く、圧縮されるだけ。削除は app-server の `thread/delete` などの明示操作のみ（公式記載: rollout ファイルと関連メタデータを消す）。`history.jsonl` は `history.max_bytes` を超えると古い行から落とされる（公式記載。ソースでは上限の 80% まで縮める）。`[history] persistence = "none"` で無効化できる。`logs_2.sqlite` には剪定があるが閾値は未確認。

## 秘密情報

次のファイルは読まない: `auth.json`（認証情報）。

出力・共有するときに伏せるべきフィールド:

| フィールド                                                                   | 入りうるもの                                   |
| ---------------------------------------------------------------------------- | ---------------------------------------------- |
| `function_call.arguments`・`*_output`・`custom_tool_call.input`              | コマンド、環境変数、ファイル内容               |
| `message.content[].text`、`history.jsonl` の `text`                          | 会話本文、貼り付けたキー                       |
| `session_meta.base_instructions`                                             | AGENTS.md 等の全文                             |
| `git.repository_url`・`threads.git_origin_url`                               | 認証情報入りの URL（読み込み時サニタイズあり） |
| `cwd`                                                                        | ユーザー名入りのパス                           |
| `reasoning.encrypted_content`                                                | 暗号化された推論                               |
| `rate_limits.plan_type`、`session_meta.creator_user_id`/`creator_account_id` | アカウント情報                                 |
| `threads.first_user_message`/`preview`                                       | 会話本文の抜粋                                 |

## 根拠と確認バージョン

- 確認日: 2026-11-17。**実データは確認していない**（調査した PC に Codex の実ログが無かった）。最小例の値はすべて架空。

### 公式ドキュメントに記載あり

https://developers.openai.com/codex/llms-full.txt（2026-08-29 取得のスナップショットを codex-docs スキルが同梱）。

- 状態の置き場所が `CODEX_HOME`（既定 `~/.codex`）で、`config.toml`・`auth.json`・`history.jsonl` があること（「Config and state locations」）
- `history.persistence = "none"` と `history.max_bytes`（「History persistence」）
- `CODEX_SQLITE_HOME` と `sqlite_home` の優先順位、`log_dir` と opt-in の `codex-tui.log`
- `--ephemeral` で rollout を書かないこと、`thread/delete`・`thread/unarchive`（app-server）
- hooks の `transcript_path` の形式は安定インターフェースではないこと（`codex-hooks` スキルの `references/hooks.md`）

### ソースコードから読み取った（SHA 885a1df 時点、未保証）

openai/codex `main` の `885a1df5ee5f18172233b12d6c94544a24e7b338`（2026-11-17）。最新リリースタグ `rust-v0.169.0` はこれより古く、型名やフィールドが一部違う可能性がある。URL は `https://github.com/openai/codex/blob/885a1df5ee5f18172233b12d6c94544a24e7b338/<path>`。

| 事項                                                                   | ファイル                                                                                                                    |
| ---------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| `sessions/`・`archived_sessions/`、行のデコード                        | `codex-rs/rollout/src/lib.rs`                                                                                               |
| ファイル名の規則                                                       | `codex-rs/rollout/src/rollout_file_name.rs`                                                                                 |
| 日付ディレクトリはローカル時刻、行は UTC                               | `codex-rs/rollout/src/recorder.rs:1701-1722`、`:975-980`                                                                    |
| `.zst` 圧縮・7 日・ロックマーカー                                      | `codex-rs/rollout/src/compression.rs:26,371-377`                                                                            |
| 永続化される item/event（legacy／paginated）                           | `codex-rs/rollout/src/policy.rs`                                                                                            |
| 外枠 `type`/`payload`                                                  | `codex-rs/history/src/lib.rs:295-`、`rollout_payload.rs:37-`                                                                |
| SessionMeta・TurnContextItem・TokenUsage・TokenCountEvent・EventMsg 等 | `codex-rs/protocol/src/protocol.rs`                                                                                         |
| ResponseItem・ContentItem                                              | `codex-rs/protocol/src/models.rs`                                                                                           |
| `history.jsonl`                                                        | `codex-rs/message-history/src/lib.rs:3-8,52-57`                                                                             |
| `session_index.jsonl`                                                  | `codex-rs/rollout/src/session_index.rs:23-31`                                                                               |
| SQLite のファイル名・WAL・表定義                                       | `codex-rs/state/src/sqlite.rs`、`codex-rs/state/migrations/*.sql`、`thread_history_migrations/0001`、`logs_migrations/0001` |
| legacy→paginated の書き換え、アーカイブ                                | `codex-rs/thread-store/src/local/rollout_migration.rs`、`archive_thread.rs:83-103`                                          |

## 未確認事項

- 新規スレッドの既定が legacy か paginated か（feature/config の切り替え条件）と、自動移行がいつ走るか。
- 圧縮ワーカーが既定で有効か（`compression_enabled` の出どころ）。main とリリース版の差。
- `SessionSource`・`sandbox_policy`・`originator` の JSON 上の実際の表現（実ログ、または `codex-rs/app-server-protocol/schema/json` の生成スキーマで確かめる）。
- 環境注入用の user メッセージを見分けるタグ名の一覧（`<environment_context>`、`<user_instructions>` 等）。
- `logs_2.sqlite` の保持期間と剪定の閾値。`log/` 配下に既定で書かれるもの（TUI ログ以外）。
- WSL 上で IDE 拡張が動く場合の所在（Linux 側の `~/.codex` か）。
- rollout ファイルが作られるタイミング（最初のユーザー入力まで遅延するか）。

Codex の機能・設定全般は **codex-docs** スキルを参照する。
