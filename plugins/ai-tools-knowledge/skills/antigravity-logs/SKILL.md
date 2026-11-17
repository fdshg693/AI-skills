---
# 同梱ファイル: format.md（protobuf の enum 表・フィールド番号、SQLite スキーマ、補助ファイルの詳細）
name: antigravity-logs
description: >-
  Google Antigravity（IDE・CLI agy）がローカルに残す会話ログの所在と形式を説明する。
  3 つのルート（~/.gemini/antigravity・antigravity-cli・antigravity-ide）、索引の
  conversation_summaries.db、本文の brain/<id>/.system_generated/logs/transcript_full.jsonl、
  会話ごとの protobuf を収めた conversations/<id>.db を扱う。「Antigravity の過去の会話を探したい」
  「トークンを集計したい」「会話履歴の保存先を知りたい」「ログの読み方や SQLite の安全な開き方を知りたい」
  ときに使う。Antigravity の一般的な機能の質問には antigravity-docs、CLI の使い方には agy-cli-docs を使う。
meta:
  tag: []
  requires_repo_tools: none
  requires_env: none
  dependencies: none
  requires_install: none
  requires_hooks: none
  requires_skills: antigravity-docs, agy-cli-docs
  status: experimental
  description: Antigravityのローカル会話ログ（3ルート）の所在と形式
  version: 1.0.0
---

# Antigravity のローカル会話ログ

Google Antigravity（IDE と CLI `agy`）は、会話を `~/.gemini/` の下に残す。**会話本文は平文で読める。暗号化されているのは思考署名だけ。** 読みやすい順に次の 3 つがある。

| 対象                                                      | 形式             | 範囲                                   |
| --------------------------------------------------------- | ---------------- | -------------------------------------- |
| `brain/<id>/.system_generated/logs/transcript_full.jsonl` | JSONL（平文）    | 2026-10-29 以降の会話だけ              |
| `conversations/<id>.db`                                   | SQLite＋protobuf | 全期間。スキーマは非公開               |
| `conversation_summaries.db`                               | SQLite（索引）   | 全会話の一覧・タイトル・ワークスペース |

公式ドキュメントに保存形式の説明は無い。この先の内容の大半は実データからの推定で、バージョンが変われば崩れうる（区別は「公式記載と推定の区別」の節）。protobuf の enum 表・フィールド番号、SQLite の全テーブルは [format.md](format.md) にまとめた。

## 所在

ルートは 3 つある。Windows では `C:\Users\<user>\.gemini\...`、POSIX/macOS も `~/.gemini/...` に同じ構造があると推定する（未確認）。保存先を変える環境変数は見つかっていない。

| ルート                       | 状態                                                                                          |
| ---------------------------- | --------------------------------------------------------------------------------------------- |
| `~/.gemini/antigravity/`     | 現行のメイン。Antigravity 2.0（エージェントマネージャ）、IDE（2026-10-29 に移行）、CLI が共用 |
| `~/.gemini/antigravity-cli/` | 旧 CLI。構成はメインと同じ。2026-10-28 以降は更新されていない                                 |
| `~/.gemini/antigravity-ide/` | 旧 IDE。`.ide_migration`（2026-10-29）があり凍結状態。多くの会話がメインへコピー済み          |

各ルートの主なファイル：

| パス（ルート相対）                                        | 内容                                                           |
| --------------------------------------------------------- | -------------------------------------------------------------- |
| `conversation_summaries.db`                               | 全会話の索引（SQLite＋FTS5）                                   |
| `conversations/<id>.db`                                   | 1 会話＝1 SQLite。step ごとの protobuf blob                    |
| `brain/<id>/`                                             | アーティファクト（`task.md` など）と `.system_generated/` 一式 |
| `brain/<id>/.system_generated/logs/transcript_full.jsonl` | 本文の全文版 JSONL（`transcript.jsonl` は切り詰め版）          |
| `annotations/<id>.pbtxt`                                  | ユーザーによるリネーム（`title`）と最終閲覧時刻                |
| `presence/<id>.lock`                                      | 0 バイトのロックファイル                                       |
| `log/cli-YYYYMMDD_HHMMSS.log`                             | Language Server の glog 形式ログ。本文ソースではない           |
| `daemon/hub_<port>.json`                                  | 起動中プロセスの情報（`csrfToken` を含む。読まない）           |

ほかに CLI 向けの `antigravity-cli/cache/last_conversations.json`（公式記載）と `antigravity-cli/history.jsonl` がある。`%APPDATA%\Antigravity IDE\User\` は VS Code 系の UI 状態だけで、会話本文は無い。詳細は [format.md](format.md)。

## 保存系統と正本

- **一覧・メタデータの正本**は `conversation_summaries.db`。会話ごとの db を開かずにタイトル・ステップ数・更新時刻・ワークスペースが分かる。
- **本文**は `transcript_full.jsonl` が最も扱いやすい。ただし 2026-10-29 以降の会話にしか無い。生成条件（バージョン・設定・ソース）は不明。
- **それより古い会話の本文**は `conversations/<id>.db` の protobuf にしか無い。スキーマ非公開なので、フィールド番号を固定で読む最小限のデコードになる（[format.md](format.md)）。
- 3 ルートに**同じ会話 ID が重複**する（旧 IDE からメインへの移行コピーなど）。全ルートを走査して会話 ID で重複を除き、更新時刻が新しい方を採る。
- `transcript.jsonl` は長いフィールドを切り詰めた版。`transcript_full.jsonl` を優先する。`logs/chunks/` は同じ内容をチャンクに分けたもの。

## レコード構造

### transcript_full.jsonl

1 行＝1 step。

| フィールド                                             | 型と値                                                                                         |
| ------------------------------------------------------ | ---------------------------------------------------------------------------------------------- |
| `step_index`                                           | int。db の `steps.idx` と一致                                                                  |
| `type`                                                 | `USER_INPUT`、`PLANNER_RESPONSE`、`GENERIC`（ツール結果）、`SYSTEM_MESSAGE` など               |
| `source`                                               | `USER_EXPLICIT`、`MODEL`、`SYSTEM`                                                             |
| `status`                                               | `DONE`、`RUNNING`（`ERROR`、`CANCELED` もあると推定）                                          |
| `created_at`                                           | ISO8601 UTC（`YYYY-MM-DDThh:mm:ssZ`）                                                          |
| `content`                                              | str。本文。無い step もある                                                                    |
| `thinking`                                             | str。思考の要約（`PLANNER_RESPONSE` のみ）                                                     |
| `tool_calls[]`                                         | `{name, args}`。`name` は `read_file`、`run_command`、`edit_file` など。**呼び出し ID は無い** |
| `model`                                                | モデル名（`PLANNER_RESPONSE` のみ）                                                            |
| `input_tokens` / `output_tokens` / `cache_read_tokens` | int（`PLANNER_RESPONSE` のみ）                                                                 |
| `truncated_fields`                                     | 切り詰めたフィールド名の配列（`transcript.jsonl` のみ）                                        |

架空値の最小例：

```json
{"step_index":0,"type":"USER_INPUT","source":"USER_EXPLICIT","status":"DONE","created_at":"2026-01-01T00:00:00Z","content":"README を要約して"}
{"step_index":1,"type":"PLANNER_RESPONSE","source":"MODEL","status":"DONE","created_at":"2026-01-01T00:00:02Z","model":"example-model","input_tokens":1200,"output_tokens":40,"cache_read_tokens":0,"thinking":"まずファイルを読む","tool_calls":[{"name":"read_file","args":{"path":"README.md"}}]}
{"step_index":2,"type":"GENERIC","source":"MODEL","status":"DONE","created_at":"2026-01-01T00:00:03Z","content":"# Example\n..."}
```

- トークンを集計するなら `PLANNER_RESPONSE` 行の `input_tokens`/`output_tokens`（必要なら `cache_read_tokens`）を足す。料金情報は無い。
- ツール結果（`GENERIC`）には tool 名も呼び出し ID も無い。直前の `PLANNER_RESPONSE.tool_calls` と出現順で対応付ける（推定）。
- ツール出力の全文は `brain/<id>/.system_generated/steps/<idx>/output.txt` にもある。

### conversation_summaries.db

テーブル `conversation_summaries` の主な列（全列は [format.md](format.md)）：

| 列                                                        | 内容                                                          |
| --------------------------------------------------------- | ------------------------------------------------------------- |
| `conversation_id`                                         | 会話 ID（UUID）                                               |
| `title` / `preview`                                       | タイトルと冒頭のプレビュー                                    |
| `step_count`                                              | step 数                                                       |
| `last_modified_time`                                      | `YYYY-MM-DD hh:mm:ss.fffffff+00:00`。未設定は `0001-01-01...` |
| `workspace_uris`                                          | JSON 配列（例 `["file:///c%3A/work/example"]`）。空もある     |
| `source`                                                  | `''` または `CORTEX_TRAJECTORY_SOURCE_CLI`                    |
| `project_id`                                              | Antigravity 内の「プロジェクト」の UUID                       |
| `parent_conversation_id` / `nesting_depth` / `agent_name` | サブエージェント会話の親子                                    |

開始時刻の列は無い。開始時刻は最初の step の `created_at`（transcript）か db の step metadata から取る。

### conversations/<id>.db

`steps` テーブルが 1 行＝1 step で、`step_type`・`status` は整数 enum、`step_payload` などは素の protobuf blob。トークン数・モデル名は `gen_metadata.data` の protobuf にある。enum の対応表とフィールド番号は [format.md](format.md)。

### タイムスタンプの書式が揃っていない

- transcript：`2026-01-01T00:00:00Z`
- summaries：7 桁小数＋`+00:00`。Python 3.11 未満の `datetime.fromisoformat` では読めない。`0001-01-01` は未設定値
- protobuf：`{seconds, nanos}`
- annotations：`last_user_view_time:{seconds,nanos}`

## セッション⇔プロジェクト対応

- ファイル名・ディレクトリ名の UUID がそのまま会話 ID。`conversations/<id>.db`、`brain/<id>/`、`annotations/<id>.pbtxt`、`presence/<id>.lock`、`conversation_summaries.conversation_id` が同じ ID でつながる（db の `trajectory_meta.cascade_id` も同じと推定）。
- すべての会話が `brain/` や `conversations/` を持つわけではない。summaries にあって db や brain が無い会話がある。
- ワークスペースは `conversation_summaries.workspace_uris` から取る。`file:///c%3A/work/example` の形なので URL デコードして `c:/work/example` に戻す。1 会話あたり 0〜1 件。
- ドライブレターは URI では小文字（`c%3A`）になっている。ほかのツールのパスと比べる前に、ドライブレターの大小とスラッシュの向きを正規化する。
- `project_id` は Antigravity 内のプロジェクト概念。プロジェクト名がどこにあるかは未確認。
- CLI では `antigravity-cli/cache/last_conversations.json` が `{絶対パス: 会話ID}` で、ワークスペースごとの最新の会話を持つ（公式記載）。
- `%APPDATA%\Antigravity IDE\User\workspaceStorage/<hash>` の hash は会話との対応には使わない。

## 読み取り安全性・保持期間

- すべての db は WAL モード。アプリの稼働中は `-wal`/`-shm` がある。
- **`mode=ro` で開いたあと、隣に 0 バイトの `-wal` と 32KB の `-shm` ができていた**ことがある（アプリ起動中だった可能性もあり、原因は未確定）。次のどちらかで開く。
  - URI 形式の `file:<path>?mode=ro&immutable=1`。ただし WAL 上の未チェックポイント分を見落とす
  - `.db`（あれば `-wal` も）を一時ディレクトリにコピーしてから開く。最新の内容が要るならこちら
- 会話 db は 1 本あたり 1〜2MB で数百本ある。一覧には db を開かず `conversation_summaries.db` を使う。
- 進行中の会話：`status` が `RUNNING` の step や `presence/<id>.lock` がある会話は書き込み中とみなせる（推定）。transcript は追記型なので、最終行が不完全なら捨てる。
- 保持期間：自動ローテーションの記述は見つかっていない。会話は CLI の picker や UI から削除できる（公式記載）が、削除でどのファイルが消えるかは未確認。`log/` はセッションごとに増え続ける。

## 秘密情報

次の場所にはコマンド・ファイル内容・トークン・ユーザー名を含むパスが入りうる。出力や共有の前に扱いを決める。

- 本文系：transcript の `content`・`thinking`・`tool_calls[].args`、`steps/*/output.txt`、`brain/<id>/scratch/`、`.system_generated/messages/*.json`
- 索引：`title`・`preview`、FTS5 の `user_body`/`agent_body`
- db：protobuf 内の utf8 文字列全般
- パス：`workspace_uris`、`last_conversations.json`、`history.jsonl` の `workspace`
- **読まない・出さない**：`daemon/hub_*.json` の `csrfToken`、`installation_id`
- `daemon/`・`log/`・`presence/` は本文ソースではないので、会話の調査では開く必要がない

## 公式記載と推定の区別

確認したバージョン：Antigravity CLI `agy` 1.5.9、Language Server 2.32（IDE 2.7.0）、Windows、2026-11-17。

**公式に記載あり**

- `~/.gemini/antigravity-cli/cache/last_conversations.json` の所在と、絶対パス→会話 ID の形式（https://antigravity.google/docs/cli/commands/resume.md）
- 会話履歴がワークスペース単位であること、fork できること（https://antigravity.google/docs/cli/conversations.md）
- 会話を picker や UI から削除できること
- アーティファクトの概念（保存形式の記載は無い）。`~/.gemini/antigravity/` がアーティファクトと Knowledge Items の置き場であることは antigravity-memory スキルの記述

**実データからの推定（バージョン依存・未保証）**

- 3 ルートの構成と移行日、ディレクトリ・ファイル名
- `conversation_summaries.db`・`conversations/<id>.db` のテーブルと列
- `transcript*.jsonl` のキーと値
- protobuf のフィールド番号と enum 対応表（`agy` 1.5.9 に埋め込まれた descriptor から抽出）
- 思考署名だけが暗号化されているという判断（エントロピーからの推定）

形式が変わって読めなくなったら、まず確認バージョンとの差を疑う。

## 未確認事項

- `transcript*.jsonl` が作られる条件（2.0 で導入されたのか、設定やソースによるのか）。古い会話に遡って作られるか
- `gen_metadata` のトークン値の正確な意味と、transcript の `input_tokens`/`output_tokens` との一致
- 会話を削除したとき db・brain・summaries・annotations のどれが消えるか。自動削除やサイズ上限の有無
- `project_id` からプロジェクト名を引ける場所
- macOS/Linux での実際のパス
- 旧 IDE の brain にある `*.resolved.<n>` の形式
- コンテキスト圧縮（compact）の表し方（`CHECKPOINT` step が候補）
- `mode=ro` で開いたあとにできた `-wal`/`-shm` が読み取り側の副作用か
