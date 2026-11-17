---
name: kilo-logs
description: Kilo Code（CLI/TUI・VS Code 拡張、opencode 由来の v7 系）がローカルに残すセッション履歴（~/.local/share/kilo/kilo.db の session/message/part/project 表）の所在・スキーマ・読み取り時の注意と、読んではいけない秘密情報の表を説明する。「Kilo の過去のセッションを探したい」「Kilo のトークン・コストを集計したい」「kilo.db の中身を知りたい」ときに使う。Kilo の一般的な機能・設定は kilo-code-docs を使う。
meta:
  tag: []
  requires_repo_tools: none
  requires_env: none
  dependencies: none
  requires_install: none
  requires_hooks: none
  requires_skills: kilo-code-docs, cline-logs
  status: experimental
  description: Kilo Codeのローカル履歴（kilo.db）の所在とスキーマ
  version: 1.0.0
---

# Kilo Code のローカル履歴（kilo.db）

現行の Kilo Code（CLI/TUI と VS Code 拡張の両方、v7 系）は、セッション履歴を SQLite の `kilo.db` 1 つに保存する。VS Code 拡張は同梱の `kilo serve` を起動し、その経由で同じ DB に書く。

旧 Kilo Code 拡張（v4 系、Cline フォーク）の tasks 形式は `cline-logs` スキルの「レガシー形式（タスク形式）」節を参照。

各項目の根拠（公式記載か実データからの推定か）は「公式記載と推定の区別」節にまとめる。推定の項目はバージョン依存で、予告なく変わりうる。

## 所在

| 対象                      | Windows                                                          | macOS/Linux                   |
| ------------------------- | ---------------------------------------------------------------- | ----------------------------- |
| DB（正本）                | `%USERPROFILE%\.local\share\kilo\kilo.db`（`-wal`・`-shm` 付き） | `~/.local/share/kilo/kilo.db` |
| VS Code Remote SSH 利用時 | リモート側の `~/.local/share/kilo/kilo.db`                       | 同じ                          |

- 上書き: `KILO_DB`（相対パスはデータディレクトリ基準、`:memory:` も可）、`XDG_DATA_HOME`（`$XDG_DATA_HOME/kilo` がデータディレクトリ）、dev チャネル。実際のパスは `kilo db path` で確かめるのが確実。
- 同じデータディレクトリの下にある補助的なもの:
  - `storage/session_diff/<sessionID>.json` — セッションの差分（JSON のまま残っている）
  - `storage/session_diff_base/`・`session_pr_link_recorded/`・`wakeup/`・`migration`
  - `log/` — 起動ごとの `YYYY-MM-DDTHHMMSS.log`、`daemon.log`、`opencode.log`、`background-process/`
  - `tool-output/` — 長すぎて切り詰めたツール出力の退避先
  - `snapshot/<project-id>/<worktree-hash>/` — チェックポイント用の bare git
  - `worktree-pool/`・`repos/` — Agent Manager の worktree、管理対象 repo のキャッシュ
  - `auth.json`・`telemetry-id`・`daemon.json` — **読まない**（「秘密情報」節）
- VS Code 拡張の globalStorage（`%APPDATA%\Code\User\globalStorage\kilocode.kilo-code\` 等）は、現行版では空。履歴はここには無い。

## 保存系統と正本

- 正本は `kilo.db` の `session`・`message`・`part` 表（と、対応づけ用の `project` 表）。
- `event` 表は同期・イベントソーシング用のログで、更新のたびに積み上がる。**正本ではないので使わない**。件数は本体の数倍〜十数倍になる。
- `storage/*.json` は補助データで、会話本体は入っていない。
- opencode の旧 JSON ストレージ（`storage/session/...`）は一回限りの移行で SQLite に移されている。古い環境では残っている可能性がある。

## レコード構造

スキーマは opencode 由来の Drizzle migration で管理され、頻繁に変わる（kilocode 独自の表もある）。時刻はすべて **epoch ミリ秒**の integer。列を使う前に `PRAGMA table_info(<table>)` で有無を確かめ、未知の列・未知の part type は無視する。

### session（列で持つ。JSON ではない）

| 列                                                                                             | 内容                                                            |
| ---------------------------------------------------------------------------------------------- | --------------------------------------------------------------- |
| `id`                                                                                           | `ses_` + 26 文字。新しいものほど辞書順で小さい（降順 ID）       |
| `project_id`                                                                                   | `project.id` への参照                                           |
| `parent_id`                                                                                    | サブエージェントのセッションなら親セッションの ID               |
| `directory`                                                                                    | 作業ディレクトリ。`C:/x/y` 形式（スラッシュ区切り）             |
| `path`                                                                                         | ワークツリー内の相対パス（空のこともある）                      |
| `slug`・`title`・`version`・`agent`                                                            | `version` は書いた Kilo のバージョン。`agent` は `code` 等      |
| `model`                                                                                        | JSON 文字列 `{"id","providerID","variant"}`                     |
| `cost`（REAL）                                                                                 | セッション累計のコスト                                          |
| `tokens_input`・`tokens_output`・`tokens_reasoning`・`tokens_cache_read`・`tokens_cache_write` | セッション累計のトークン                                        |
| `summary_additions`・`summary_deletions`・`summary_files`・`summary_diffs`                     | 変更行数・ファイル数・差分                                      |
| `metadata`                                                                                     | JSON。キーにドットを含むもの（`kilocode.sandbox`）がある        |
| `permission`                                                                                   | JSON 配列 `[{permission, pattern, action}]`。子セッションに付く |
| `revert`・`share_url`                                                                          |                                                                 |
| `time_created`・`time_updated`・`time_compacting`・`time_archived`                             | 終了時刻の列は無い                                              |

### message

列は `id`（`msg_`、昇順）、`session_id`、`time_created`、`time_updated`、`data`（JSON 文字列）。`data` の中に `id` と `sessionID` は**含まれない**ので、ID は列の方を使う。

| `data` のキー                                                         | user                                                        | assistant                                          |
| --------------------------------------------------------------------- | ----------------------------------------------------------- | -------------------------------------------------- |
| `role`                                                                | `"user"`                                                    | `"assistant"`                                      |
| `time.created` / `time.completed`                                     | ○ / -                                                       | ○ / ○                                              |
| モデル                                                                | `model{providerID, modelID, variant}`                       | `providerID`・`modelID`・`variant`（トップレベル） |
| `agent` / `mode`                                                      | ○                                                           | ○                                                  |
| `parentID`                                                            | -                                                           | 対応する user メッセージの ID                      |
| `path{cwd, root}`                                                     | -                                                           | ○                                                  |
| `tokens{input, output, reasoning, total, cache{read, write}}`・`cost` | -                                                           | ○                                                  |
| `finish`                                                              | -                                                           | `tool-calls` / `stop`                              |
| `error{name, data}`                                                   | -                                                           | 任意（`APIError`・`MessageAbortedError` 等）       |
| `summary{diffs[]}`                                                    | 任意（`file`・`patch`・`additions`・`deletions`・`status`） | -                                                  |
| `editorContext{...}`・`tools{...}`                                    | 任意（VS Code 経由のとき）                                  | -                                                  |

- トークンとコストは **assistant メッセージ**に付く（user メッセージ単位のトークンは無い）。assistant の値は、その配下の `step-finish` part の合計とほぼ一致する。セッション合計は `session` の集計列を使う。
- `cost` は int の `0` か real。`0` は「無料」か「未計測」のどちらもありうる（サブスクリプション経路では 0 になることがある）。

### part

列は `id`（`prt_`、昇順）、`message_id`、`session_id`、`time_created`・`time_updated`、`data`（JSON 文字列）。種類は `data.type` で分かれる。並び順は `ORDER BY message_id, id`（`time_created` と組み合わせると安全）。

| `type`        | 主なフィールド                                                                                                                      |
| ------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| `text`        | `text`・`synthetic?`・`ignored?`・`time{start, end}`・`metadata`                                                                    |
| `reasoning`   | `text`・`time`・`metadata`（プロバイダ固有のキー。暗号化された推論が入る可能性）                                                    |
| `tool`        | `tool`（read/bash/grep/edit/task 等）・`callID`・`state{status, input{...}, output, title, error, metadata{...}, time{start, end}}` |
| `step-start`  | `snapshot?`・`time.start`                                                                                                           |
| `step-finish` | `reason`・`cost`・`tokens{...}`・`time{start, end, elapsed}`・`metrics`・`snapshot?`                                                |
| `patch`       | `hash`・`files[]`                                                                                                                   |
| `file`        | `filename`・`mime`・`url`（data URL がありうる）                                                                                    |

- `tool` part は**呼び出しと結果を 1 レコードに同居**させる（`state.input` と `state.output` が同じ part にある）。呼び出しと結果の別時刻は無く、`state.time.start` / `end` で代用する。
- `state.status` は `completed` / `error` / `running`。中断されたセッションでは `running` のまま残る。
- `task` ツールの `state.metadata.sessionId` は子セッションの ID を指す（子の `session.parent_id` と対応する）。
- 切り詰めた出力は `state.metadata.outputPath`（`tool-output/` 配下を指すパス）に退避される。
- part 1 件が 1MB 近くになることがある。本文（`text`・`output`）は必要なときだけ取り出す。

### 最小の例（値はすべて架空）

```json
// message.data (assistant)
{"role":"assistant","parentID":"msg_0000example","agent":"code","mode":"code","providerID":"example-provider","modelID":"example-model","variant":"high","path":{"cwd":"C:/work/demo","root":"C:/work/demo"},"time":{"created":1790000000000,"completed":1790000005000},"tokens":{"input":1000,"output":50,"reasoning":10,"total":1060,"cache":{"read":0,"write":0}},"cost":0,"finish":"tool-calls"}
// part.data (tool)
{"type":"tool","tool":"read","callID":"call_example","state":{"status":"completed","input":{"filePath":"C:/work/demo/README.md"},"output":"(file text)","title":"README.md","metadata":{"truncated":false},"time":{"start":1790000001000,"end":1790000001200}}}
// part.data (step-finish)
{"type":"step-finish","reason":"stop","cost":0.0012,"tokens":{"input":1000,"output":50,"reasoning":0,"total":1050,"cache":{"read":800,"write":0}},"time":{"start":1790000000000,"end":1790000005000,"elapsed":5000}}
```

## セッション⇔プロジェクト対応

- `session.project_id` → `project.id`。
  - git 管理下では `project.id` が 40 桁の hex（opencode の実装ではルートコミットの SHA と推定）。
  - git 管理外では `id='global'`、`worktree='/'`。
- `project.worktree` はリポジトリのルート。実際の cwd は **`session.directory`** を使う（サブディレクトリや global の場合に worktree と一致しない）。`message.data.path.cwd` / `path.root` でも取れる。
- `project_directory(project_id, directory, strategy)` には worktree の別ディレクトリが入る（読む必要があるのは対応づけのときだけ）。
- パスはエンコードやハッシュ化をされず生で入る。区切りは `/`、ドライブ文字付き。照合するときは大文字小文字と区切りを正規化する。
- **session の ID は降順**なので、ID でソートすると新しい順になる。時系列で並べるときは `time_created` / `time_updated` を使う。
- 終了時刻の列は無い。`time_updated` は近似値で、`max(message.data.time.completed)` の方が正確。

## 読み取り安全性・保持期間

### 開き方

- DB は WAL モード（`synchronous=normal`、`busy_timeout` 5 秒、passive checkpoint）。Kilo の起動中でも読み取り専用で開ける。
- `sqlite3 -readonly`、または URI の `mode=ro` で開く。
  - Python: `sqlite3.connect("file:///C:/Users/<user>/.local/share/kilo/kilo.db?mode=ro", uri=True)`
  - Windows のパスは `file:///C:/...` とスラッシュに直す。`%`・`?` を含むパスは URL エンコードする。
- `immutable=1` は使わない。WAL 内の未チェックポイント分が見えなくなる。
- `kilo db` サブコマンドは書き込みもできるため、調査では使わない。

### クエリの注意

- DB は数 GB になることがある。`json_extract` での全件走査は重い。
- `session_id` で絞り、既存インデックス（`message_session_time_created_id_idx`・`part_session_idx`・`part_session_step_finish_idx`）に乗るクエリにする。

以下は実データのスキーマから組み立てた例（公式ドキュメントの例ではない）。

```sql
-- 直近のセッション（集計列だけ）
SELECT id, title, directory, time_created, cost, tokens_input, tokens_output
FROM session ORDER BY time_created DESC LIMIT 20;

-- 1 セッションの part を順に（本文は必要な type だけ）
SELECT message_id, id, json_extract(data, '$.type') AS type
FROM part WHERE session_id = 'ses_0000example' ORDER BY message_id, id;
```

### 保持期間

- DB の自動削除は確認できていない。削除は UI か `kilo session delete` で行い、FK の CASCADE で message・part・todo も消える。
- revert 後に新しいメッセージを送ると、巻き戻した分は物理削除される。
- snapshot は毎時 `git gc --prune=7.days`。
- `log/` は直近 10 件前後の起動ログだけが残り、`tool-output/` も掃除されると推定。

## 秘密情報

同じ `kilo.db` に認証情報の表がある。**`session`・`message`・`part`・`project` 以外の表は SELECT しない**。

- 読まない表: `account` / `control_account`（`access_token`・`refresh_token`・`email`）、`credential`（`value`）、`session_share`（`secret`）など
- 読まないファイル: `auth.json`・`daemon.json`・`log/daemon.log`・`telemetry-id`
- 会話本文や個人情報を含みうるフィールド（出力・共有するときは伏せる）:
  - `part.data.text`、`tool` の `state.input`（`command`・`body`・`prompt` 等）・`state.output`・`state.metadata`（`output`・`diff`・`preview`）
  - `file` part の `url`（data URL で中身が丸ごと入る）
  - `message.data.summary.diffs[].patch`・`editorContext`
  - `session.title`・`session.directory`（ユーザー名を含むパス）
- 他の表（`todo.content`、マルチエージェント掲示板の `kilo_board_message.body` 等）も平文の本文を含む。

## 公式記載と推定の区別

確認したバージョン: Kilo 7.8（VS Code 拡張 7.8.27、CLI 7.6.2、DB 内の `session.version` は 7.5〜7.8 系が混在）、2026-11-17。

### 公式に記載あり（kilo.ai/docs）

- `/code-with-ai/agents/session-history`: DB の所在、`KILO_DB` / `XDG_DATA_HOME`、`kilo db path`、session / message / part を読む SQL 例、読み取り専用（`sqlite3 -readonly`）の推奨、WAL / shm の注意、Remote SSH ではリモート側にあること
- `/contributing/architecture/cli-runtime`: `kilo.db` の位置、WAL 等の pragma、JSON から SQLite への一回限りの移行、`session_diff` は JSON のまま、`daemon.json` / `daemon.log`、snapshot のパス
- `/code-with-ai/features/checkpoints`: snapshot の場所、`git gc --prune=7.days`、revert 後の削除
- `$XDG_DATA_HOME/kilo` にセッションデータ・ログ・`repos/` が入ること

### 実データからの推定（バージョン依存・未保証）

- 表の列構成、`message.data` / `part.data` の JSON キー、part type の種類
- assistant の tokens / cost と step-finish の合計の整合
- ID の順序（session は降順、message・part は昇順）
- `project.id` が 40 桁 hex または `global` であること
- `task` ツールの `metadata.sessionId` と子セッションの対応
- `event` 表を正本としないこと
- `storage/` の補助ディレクトリ、`log/`・`tool-output/` の保持
- VS Code 拡張の globalStorage が空であること

## 未確認事項

- compaction / 要約の表現。opencode では `compaction` part や `summary: true` の assistant メッセージで表すが、確認したデータには無かった（`time_compacting` もすべて NULL）。
- DB 本体の保持期間、自動 prune・アーカイブ（`time_archived`）の動作。
- `reasoning` part の `metadata` に暗号化された推論が入っているか（キー名だけ確認）。
- `session_message` / `session_input` 表（確認時は 0 件）が今後の正本に変わる可能性。
- macOS で `XDG_DATA_HOME` を設定しない場合に本当に `~/.local/share/kilo` になるか（公式記載はあるが実機未確認）。
- 旧 Kilo Code 拡張（v4 系）の tasks 形式が残っている環境での実データ（`cline-logs` 側を参照）。
