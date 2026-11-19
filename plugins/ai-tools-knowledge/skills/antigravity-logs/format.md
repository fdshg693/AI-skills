# Antigravity ログ形式の詳細

[SKILL.md](SKILL.md) の補足。この文書の内容は、特に断りが無い限り**実データからの推定**で、バージョンが変われば崩れうる（確認したバージョン：`agy` 1.5.9、Language Server 2.32、2026-11-17）。値はすべて架空。

## ルートごとのファイル構成

### `~/.gemini/antigravity/`（現行メイン）

| パス                               | 内容                                                                                     |
| ---------------------------------- | ---------------------------------------------------------------------------------------- |
| `conversations/<id>.db`            | 1 会話＝1 SQLite（WAL）                                                                  |
| `conversation_summaries.db`        | 全会話の索引（SQLite＋FTS5）                                                             |
| `agyhub_summaries_proto.pb`        | 会話サマリの protobuf スナップショット                                                   |
| `brain/<id>/`                      | アーティファクトと `.system_generated/`                                                  |
| `annotations/<id>.pbtxt`           | protobuf テキスト形式。`title:"..."`（リネーム）と `last_user_view_time:{seconds,nanos}` |
| `presence/<id>.lock`               | 0 バイトのロックファイル                                                                 |
| `log/cli-YYYYMMDD_HHMMSS.log`      | glog 形式（`I1117 hh:mm:ss.us pid file.go:line] ...`）。`cli.log` はシンボリックリンク   |
| `daemon/hub_<port>.json`           | pid・ポート・`lsVersion`・`csrfToken`                                                    |
| `antigravity_state.pbtxt`          | UI 状態と移行フラグ（`migrate_convos_into_projects` など）                               |
| `knowledge/`・`crashes/`・`cache/` | 会話本文は無い                                                                           |

### `~/.gemini/antigravity-cli/`（旧 CLI）

メインと同じ構成（`conversations/*.db`、`conversation_summaries.db`）に加えて、`jetbox_summaries_proto.pb`、`history.jsonl`、`cache/last_conversations.json`、`cache/conversation_metadata.json` がある。

### `~/.gemini/antigravity-ide/`（旧 IDE）

`conversations/*.db`（一部に `-wal`/`-shm` が残る）、`brain/`、`browser_recordings/`、`html_artifacts/`、`.ide_migration`。会話 db の多くはメインと同じ ID のコピー。

### ルート以外

| パス                              | 内容                                                                                                                               |
| --------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| `%APPDATA%\Antigravity IDE\User\` | `globalStorage/state.vscdb`（UI 状態のみ）、`workspaceStorage/<hash>/workspace.json`（`{"folder":"file:///..."}`）。会話本文は無い |
| `%APPDATA%\Antigravity\`          | 旧 Antigravity（2025〜2026-05）の Electron 領域                                                                                    |
| `~/.gemini/logs/install.log`      | インストーラのログ。会話とは無関係                                                                                                 |

## brain/<id>/ の中身

| パス                                                                        | 内容                                                                                |
| --------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| `.system_generated/logs/transcript_full.jsonl`                              | 全文版の step 列（キーは SKILL.md の表）                                            |
| `.system_generated/logs/transcript.jsonl`                                   | 切り詰め版。`truncated_fields` に切ったフィールド名                                 |
| `.system_generated/logs/chunks/{transcript,transcript_full}/0000000N.jsonl` | 同じ内容をチャンクに分けたもの                                                      |
| `.system_generated/steps/<idx>/output.txt`                                  | ツール出力の全文                                                                    |
| `.system_generated/messages/<uuid>.json`                                    | エージェント間メッセージ（下記）                                                    |
| `.system_generated/messages/read.json`                                      | `{<message-id>: true}`                                                              |
| `{task,implementation_plan,walkthrough}.md`                                 | アーティファクト。`task.md` は `# タイトル` の下に `- [x]`/`- [ ]` のチェックリスト |
| `*.md.metadata.json`                                                        | `{artifactType, summary, updatedAt}`                                                |
| `<name>_<epochms>.png` / `.webp`                                            | 画像                                                                                |
| `scratch/`                                                                  | エージェントが作った作業ファイル                                                    |

旧 IDE の brain には `*.resolved.<n>` もあると推定（形式は未確認）。

`messages/<uuid>.json` の構造：

```json
{
  "id": "00000000-0000-0000-0000-000000000001",
  "recipient": "<agent>",
  "sender": "<agent>",
  "priority": "<priority>",
  "timestamp": "2026-01-01T00:00:00Z",
  "renderDetails": { "messageTitle": "<title>" },
  "content": "<text>",
  "sourceMetadata": {
    "tool": {
      "conversationId": "00000000-0000-0000-0000-000000000002",
      "stepIndex": 5,
      "toolCall": {
        "id": "<id>",
        "name": "<tool>",
        "argumentsJson": "{}",
        "thinkingSignature": "<opaque>"
      }
    }
  }
}
```

## conversation_summaries.db

### `conversation_summaries` の全列

| 列                                                   | 内容                                                       |
| ---------------------------------------------------- | ---------------------------------------------------------- |
| `conversation_id`                                    | 会話 ID（UUID）                                            |
| `title`、`preview`                                   | タイトル、冒頭プレビュー                                   |
| `step_count`                                         | step 数                                                    |
| `last_modified_time`                                 | `YYYY-MM-DD hh:mm:ss.fffffff+00:00`。未設定は `0001-01-01` |
| `workspace_uris`                                     | JSON 配列（`["file:///c%3A/..."]`）。空もある              |
| `status`                                             | 観測値は `CASCADE_RUN_STATUS_IDLE` のみ                    |
| `source`                                             | `''` または `CORTEX_TRAJECTORY_SOURCE_CLI`                 |
| `project_id`                                         | プロジェクト UUID                                          |
| `agent_name`                                         | サブエージェント名（例 `research`）                        |
| `parent_conversation_id`、`nesting_depth`            | サブエージェント会話の親と深さ                             |
| `battle_id`、`winning_conversation_id`               | 複数案比較（battle mode）関連と推定                        |
| `not_fully_idle`、`killed`                           | 状態フラグ                                                 |
| `last_user_input_time`、`last_user_input_step_index` | 最後のユーザー入力                                         |
| `app_data_dir`                                       | 例 `antigravity`                                           |
| `raw_summary`                                        | protobuf blob                                              |
| `group_id`                                           | グループ ID                                                |

### 他のテーブル

- `conversation_parents(conversation_id, parent_id)`：観測時は 0 行
- `conversations_fts`（FTS5）：1 会話を最大 3 チャンクに分け、`user_body`/`agent_body` を平文で持つ

`agyhub_summaries_proto.pb` は `repeated 1 { 1: conv_id, 2: summary { 1: title, 2: step_count, ...timestamps, 4: uuid ... } }` の形で、`raw_summary` と同じ型の可能性が高い。

## conversations/<id>.db

### テーブル

| テーブル                   | 列                                                                                                                                                             |
| -------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `trajectory_meta`          | `trajectory_id` PK、`cascade_id`、`trajectory_type`、`source`                                                                                                  |
| `steps`                    | `idx` PK、`step_type`、`status`、`has_subtrajectory`、`metadata`、`error_details`、`permissions`、`task_details`、`render_info`、`step_payload`、`step_format` |
| `gen_metadata`             | `idx` PK、`data`、`size`                                                                                                                                       |
| `executor_metadata`        | `idx`、`data`                                                                                                                                                  |
| `parent_references`        | `idx`、`data`                                                                                                                                                  |
| `trajectory_metadata_blob` | `id`（`'main'`）、`data`                                                                                                                                       |
| `battle_mode_infos`        | —                                                                                                                                                              |

blob はすべて素の protobuf（観測した全行で `step_format` = 0）。`steps.idx` は transcript の `step_index` と一致する。

### enum（推定）

`agy` 1.5.9 に埋め込まれた protobuf descriptor から抽出した。名前は `CORTEX_STEP_TYPE_` などの接頭辞を除いたもの（transcript の `type` と同じ表記）。

`steps.step_type`（全 140 種のうち主なもの）：

| 値  | 名前              |
| --- | ----------------- |
| 5   | CODE_ACTION       |
| 7   | GREP_SEARCH       |
| 8   | VIEW_FILE         |
| 9   | LIST_DIRECTORY    |
| 14  | USER_INPUT        |
| 15  | PLANNER_RESPONSE  |
| 17  | ERROR_MESSAGE     |
| 21  | RUN_COMMAND       |
| 23  | CHECKPOINT        |
| 31  | READ_URL_CONTENT  |
| 33  | SEARCH_WEB        |
| 85  | BROWSER_SUBAGENT  |
| 90  | EPHEMERAL_MESSAGE |
| 101 | SYSTEM_MESSAGE    |
| 127 | INVOKE_SUBAGENT   |
| 132 | GENERIC           |
| 138 | ASK_QUESTION      |

`steps.status`：

| 値  | 名前     |
| --- | -------- |
| 2   | RUNNING  |
| 3   | DONE     |
| 6   | CANCELED |
| 7   | ERROR    |

`trajectory_meta.trajectory_type`：4 = CASCADE

`trajectory_meta.source`：

| 値  | 名前           |
| --- | -------------- |
| 1   | CASCADE_CLIENT |
| 17  | CLI            |
| 22  | VSCODE         |

### step_payload のフィールド番号（推定）

| フィールド     | 内容                              |
| -------------- | --------------------------------- |
| 1              | type（`step_type` と同じ enum）   |
| 4              | status                            |
| 5              | step metadata                     |
| 5.1            | 作成時刻 `{1: seconds, 2: nanos}` |
| 型ごとの oneof | 下表                              |

| step_type        | oneof のフィールド番号 |
| ---------------- | ---------------------- |
| CODE_ACTION      | 10                     |
| VIEW_FILE        | 14                     |
| USER_INPUT       | 19                     |
| PLANNER_RESPONSE | 20                     |
| RUN_COMMAND      | 28                     |
| SYSTEM_MESSAGE   | 114                    |
| GENERIC          | 140                    |

`PLANNER_RESPONSE`（20）の中：

| パス         | 内容                                                               |
| ------------ | ------------------------------------------------------------------ |
| `20.3`       | 応答本文（utf8）                                                   |
| `20.7`       | ツール呼び出し（繰り返し）                                         |
| `20.7.1`     | 呼び出し ID                                                        |
| `20.7.2`     | tool 名                                                            |
| `20.7.3`     | 引数 JSON（文字列）                                                |
| `20.7.7.2.1` | 高エントロピーの bytes。暗号化された思考署名とみられる。復号しない |

思考署名以外の文字列フィールドは utf8 平文。

### gen_metadata.data（推定）

| パス               | 内容                                       |
| ------------------ | ------------------------------------------ |
| `1.19`             | モデル名（文字列）                         |
| `1.4.1`            | モデル enum                                |
| `1.4.2` / `1.4.3`  | 入力 / 出力トークン（推定）                |
| `1.4.9` / `1.4.10` | キャッシュ系のトークンらしき値（意味不明） |

transcript の `input_tokens`/`output_tokens` との一致は未検証。

### デコードの注意

- スキーマは非公開。`.proto` なしで wire format を読み、上の番号を固定で拾う最小デコードになる。バージョンが変われば番号が変わりうる。
- 番号が想定と違う・型が合わないときは、そのフィールドを捨てて続行し、本文なしとして扱う方が安全。

## CLI の補助ファイル

| パス                                               | 内容                                                               |
| -------------------------------------------------- | ------------------------------------------------------------------ |
| `antigravity-cli/cache/last_conversations.json`    | `{"<絶対パス>": "<会話ID>"}`（公式記載）                           |
| `antigravity-cli/history.jsonl`                    | プロンプト履歴。キーは `display`、`timestamp`、`type`、`workspace` |
| `antigravity-cli/cache/conversation_metadata.json` | 中身は未確認（プロジェクト名の所在候補）                           |

`history.jsonl` の `timestamp` の単位と `type` の値は未確認。
