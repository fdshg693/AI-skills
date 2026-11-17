---
name: cline-logs
description: >-
  Cline（VS Code 拡張・Cline CLI）のローカルに残るタスク・セッション履歴の所在と形式を説明する。
  SDK セッション形式（~/.cline/data/sessions/<sid>/ の JSON と索引 data/db/sessions.db、CLINE_DATA_DIR で上書き可）と、
  レガシーのタスク形式（VS Code globalStorage の saoudrizwan.claude-dev/tasks/<id>/ と旧 CLI の ~/.cline/data/tasks/）の
  2 系統について、レコード構造・トークンとコストの位置・プロジェクトとの対応・安全な読み方・読まない秘密ファイルを扱う。
  「Cline の過去のタスクを探したい」「Cline のトークン・コストを集計したい」「Cline の履歴の保存先を知りたい」
  「ui_messages.json や sessions.db の中身を読みたい」ときに使う。Cline の機能全般は cline-docs を使う。
meta:
  tag: []
  requires_repo_tools: none
  requires_env: none
  dependencies: none
  requires_install: none
  requires_hooks: none
  requires_skills: cline-docs
  status: experimental
  description: Clineのローカル履歴（SDKセッション形式・レガシータスク形式）の所在と形式
  version: 1.0.0
---

# Cline のローカル履歴（タスク・セッション）

Cline がローカルに残す会話履歴の所在・形式・読み方の注意をまとめる。保存形式は 2 系統ある。

- **A. SDK セッション形式**: Cline CLI と新しい VS Code 拡張が使う。共通 SDK（`@cline/core`）が `~/.cline/data/sessions/` に書く。
- **B. レガシーのタスク形式**: 古い VS Code 拡張が globalStorage に、旧 CLI・JetBrains が `~/.cline/data/tasks/` に書く。旧 Kilo Code（v4 系、Cline フォーク）のタスクも同じ形。

非公開形式を含むので、各項目が公式記載か実データからの推定かは [公式記載と実データ推定の区別](#公式記載と実データ推定の区別確認バージョン) を見る。以下の例の値はすべて架空。

## 所在

| 系統                              | Windows                                                                                                                    | POSIX / macOS                                                                                                                                  |
| --------------------------------- | -------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| A. SDK セッション                 | `%USERPROFILE%\.cline\data\sessions\<sid>\`、索引 `%USERPROFILE%\.cline\data\db\sessions.db`                               | `~/.cline/data/sessions/<sid>/`、`~/.cline/data/db/sessions.db`                                                                                |
| B. レガシー（拡張）               | `%APPDATA%\Code\User\globalStorage\saoudrizwan.claude-dev\` の `state\taskHistory.json`・`tasks\<taskId>\`・`checkpoints\` | macOS: `~/Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/`、Linux: `~/.config/Code/User/globalStorage/...`（推定） |
| B'. レガシー（旧 CLI・JetBrains） | `%USERPROFILE%\.cline\data\tasks\<taskId>\`、`tasks\taskHistory.json`                                                      | `~/.cline/data/tasks/<taskId>/`                                                                                                                |

- **環境変数での上書き**: `CLINE_DATA_DIR` を設定すると `~/.cline/data` が丸ごと差し替わる（公式）。A・B' の探索は「`CLINE_DATA_DIR` → `~/.cline/data`」の順に解決する。
- **VS Code の系列**: B の `Code` の部分は Insiders（`Code - Insiders`）・VSCodium・Cursor などの派生エディタで変わる。複数候補を列挙して探す。
- **`sessions.db` の位置**: 公式文書（hub-spoke ページ）は `sessions/` の直下と書いているが、実際は `data/db/sessions.db`。SDK のソース（`resolveDbDataDir()` が `<data>/db`）もこちら。文書の方が古い。

`~/.cline/data/` にある会話ログ以外のファイル:

| パス                                        | 中身                                                                  |
| ------------------------------------------- | --------------------------------------------------------------------- |
| `logs/cline.log`                            | pino 形式の JSON 行。ホスト名を含む                                   |
| `logs/hooks.jsonl`                          | フック実行記録。キーは `hookName, pid, reason, sessionId, source, ts` |
| `logs/hub-daemon.log`                       | 数百 MB に育つことがある。調査では読まない                            |
| `cache/user_input_history.jsonl`            | 入力履歴。キーは `{prompt, ts}`（本文を含む）                         |
| `workspaces/<8 桁 hex>/workspaceState.json` | トグルとマイグレーション版だけ。会話は無い                            |
| `db/cron.db`・`db/teams.db`                 | スケジュール・チーム機能の DB                                         |
| `secrets.json`・`settings/providers.json`   | API キー。読まない（[秘密情報](#秘密情報)）                           |

## 保存系統と正本

- **A の正本は JSON**。`sessions/<sid>/*.json` が正本で、`sessions.db` はその索引（公式: hub-spoke ページ）。`<sid>.messages.json` は公式の契約文書（`messages-contract-v1.md`）で「再生・エクスポート用の正規の成果物」とされる。
- **B の正本は `tasks/<id>/` の JSON 群**。`taskHistory.json` は一覧（集計値付き）。
- **移行後の重複**: 拡張から `~/.cline/data` へのマイグレーションは VS Code 側のデータを消さない（ソースのコメント）。新しい拡張は A に `source: "vscode"` で書くので、同じタスクが A と B の両方に現れうる。重複を除くには B の id と、A の id や `metadata` の `legacyTask`・`migratedFromLegacyTask` を突き合わせる（ソースからの推定）。
- **A の一覧の取り方**: `sessions.db` があればそれを使い、無いか開けなければ `sessions/*/*.json` を走査する。両者は一致するが、フィールドは JSON の方が豊富。

## A. SDK セッション形式のレコード構造

`sessions/<sid>/` には `<sid>.json`（メタデータ）と `<sid>.messages.json`（会話）が必ずある。どちらも 1 ファイル 1 JSON（JSONL ではない）で、全体を読み込む。`<sid>` は `<epoch ミリ秒>_<英数 5 文字>`（例: `1780000000000_ab12c`）。

### `<sid>.json`（`version: 1`）

| フィールド                                                                        | 型・値                                                                      | 備考                                                                            |
| --------------------------------------------------------------------------------- | --------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| `session_id`                                                                      | str                                                                         | ディレクトリ名と同じ                                                            |
| `source`                                                                          | `cli` など                                                                  | SDK の enum: `core/cli/subagent/desktop/kanban/vscode/jetbrains/neovim/unknown` |
| `started_at`, `ended_at`                                                          | ISO8601（末尾 `Z`）                                                         | 実行中・異常終了では `ended_at` が無いか古い                                    |
| `status`, `exit_code`                                                             | `completed` / `failed` / `cancelled` など                                   |                                                                                 |
| `provider`, `model`                                                               | str                                                                         |                                                                                 |
| `cwd`, `workspace_root`                                                           | 絶対パス                                                                    | 一致しないことがある                                                            |
| `prompt`                                                                          | 最初の依頼の本文                                                            | 機密                                                                            |
| `interactive`, `enable_tools`, `enable_spawn`, `enable_teams`, `team_name`, `pid` |                                                                             |                                                                                 |
| `messages_path`                                                                   | 絶対パス                                                                    | `<sid>.messages.json` を指す                                                    |
| `metadata.title`                                                                  | str                                                                         | 無ければ `prompt` の先頭で代用                                                  |
| `metadata.usage` / `metadata.aggregateUsage`                                      | `{inputTokens, outputTokens, cacheReadTokens, cacheWriteTokens, totalCost}` | `aggregateUsage` はサブエージェント込み（推定）                                 |
| `metadata.totalCost`, `metadata.aggregatedAgentsCost`                             | float                                                                       | セッション合計                                                                  |
| `metadata.git`                                                                    | `{url, branch}`                                                             |                                                                                 |
| `metadata.checkpoint`                                                             | `{latest, history[]}`                                                       |                                                                                 |
| `metadata.systemPrompt`, `metadata.terminal_marker*`, `metadata.mode`             |                                                                             | 一部のレコードにだけある                                                        |

`metadata` のキー構成は版ごとに大きく違う。どのキーも欠落を許容して読む。

### `<sid>.messages.json`

形は `{version: 1, updated_at, agent: "lead", sessionId, system_prompt, messages: [...]}`。`messages[]` は Anthropic の MessageParam 形式を拡張したもの。

| role        | キー                                                                                                                                                             | content のブロック                                                       |
| ----------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| `user`      | `{id, role, ts(ms), content[]}`                                                                                                                                  | `text`、`tool_result{tool_use_id, name, content(str か配列), is_error?}` |
| `assistant` | `{id, role, ts, content[], metrics{inputTokens, outputTokens, cacheReadTokens, cacheWriteTokens, cost}, modelInfo{id, provider}, metadata?{invalidToolCalls[]}}` | `thinking`・`text`・`tool_use{id, name, input}`                          |

- **トークン・コストの位置**: assistant メッセージの `metrics`（リクエストごと）。セッション合計は `<sid>.json` の `metadata.usage`・`metadata.totalCost`。
- ツール名の例: `run_commands`, `editor`, `read_files`, `search_codebase`, `fetch_web_content`, `ask_question`, `skills`。
- 読むときの注意: `content` が配列でなく文字列のメッセージ、`ts` の無いメッセージがまれにある。`tool_result.content` は文字列か配列。
- サブエージェントの messages は同じディレクトリに別の stem（`childArtifactFileStem`）で出る可能性がある（ソースからの推定）。`*.messages.json` をすべて拾い、`agent` フィールドで区別する。

最小の例（`messages[]` の 2 要素。値は架空）:

```json
{"id":"m2","role":"assistant","ts":1780000000000,
 "modelInfo":{"id":"example-model","provider":"example-provider"},
 "metrics":{"inputTokens":10,"outputTokens":5,"cacheReadTokens":0,"cacheWriteTokens":0,"cost":0.001},
 "content":[{"type":"thinking","thinking":"..."},
            {"type":"tool_use","id":"t1","name":"read_files","input":{"files":[{"path":"src/app.ts"}]}}]}
{"id":"m3","role":"user","ts":1780000000500,
 "content":[{"type":"tool_result","tool_use_id":"t1","name":"read_files","content":"..."}]}
```

### `sessions.db`（SQLite 索引）

`sessions` テーブルの列:

- JSON と同じ値: `session_id, source, started_at, ended_at, status, provider, model, cwd, workspace_root, prompt, metadata_json, messages_path, updated_at`
- 親子関係: `parent_session_id, parent_agent_id, agent_id, conversation_id, is_subagent`（サブエージェントの親子はここにしか無い）
- その他: `transcript_path, hook_path`

ほかに `subagent_spawn_queue`・`schedules`・`schedule_executions(tokens_used, cost_usd)` テーブルがある。

## レガシー形式（タスク形式）

古い VS Code 拡張（globalStorage `saoudrizwan.claude-dev/`）、旧 Cline CLI・JetBrains（`~/.cline/data/tasks/`）、旧 Kilo Code 拡張（v4 系、Cline フォーク）が使う形式。所在は [所在](#所在) の B・B' 行。どれも JSON 配列・オブジェクトで、全体を読み込む。

### ファイル構成

```text
<root>/
├── state/taskHistory.json        # 拡張の場合。旧 CLI は tasks/taskHistory.json
├── tasks/<taskId>/               # <taskId> は epoch ミリ秒
│   ├── api_conversation_history.json
│   ├── ui_messages.json
│   ├── task_metadata.json
│   └── focus_chain_taskid_<taskId>.md
└── checkpoints/<数字>/.git       # shadow git。会話は無い
```

### `taskHistory.json`（一覧）

配列。要素の主なフィールド:

| フィールド                                                        | 内容                                       |
| ----------------------------------------------------------------- | ------------------------------------------ |
| `id`, `ulid`                                                      | `id` はディレクトリ名と同じ                |
| `ts`                                                              | 作成時刻（epoch ms）                       |
| `task`                                                            | 最初の依頼の本文（タイトルの代わり。機密） |
| `tokensIn`, `tokensOut`, `cacheWrites`, `cacheReads`, `totalCost` | タスク合計                                 |
| `size`                                                            | ディスク使用量                             |
| `cwdOnTaskInitialization`                                         | 開始時の作業ディレクトリ（絶対パス）       |
| `modelId`, `isFavorited`                                          |                                            |

### `api_conversation_history.json`（モデルに送った会話）

MessageParam の配列（公式: Prompt Storage 文書）。各要素は `{role, content[], ts}`。assistant には `modelInfo{providerId, modelId, mode}` と `metrics{tokens{prompt, completion, cached}, cost}` が付く。ブロックは `text`（`call_id`・`reasoning_details` が付くことがある）、`thinking{thinking, signature, summary}`。確認した版では `tool_use` ブロックが無く、ツール呼び出しは text 内の XML 形式か `call_id` 付きの text だった（推定）。公式の例には `tool_use` がある。

### `ui_messages.json`（画面に出たメッセージ）

配列。要素は `{ts, type: "say"|"ask", say|ask, text?, partial?, conversationHistoryIndex, modelInfo?, images?, files?, lastCheckpointHash?, isCheckpointCheckedOut?}`。

| 種別                     | `text` の中身                                                                                                           |
| ------------------------ | ----------------------------------------------------------------------------------------------------------------------- |
| `say: "task"`            | 最初の依頼                                                                                                              |
| `say: "text"`            | アシスタントの応答                                                                                                      |
| `say: "api_req_started"` | JSON 文字列 `{request, tokensIn, tokensOut, cacheWrites, cacheReads, cost}`。**リクエストごとのトークンとコストはここ** |
| `say: "tool"`            | JSON 文字列 `{tool: "readFile"/"listFilesTopLevel"/"listFilesRecursive"/"searchFiles"/..., path, content, ...}`         |
| その他の `say`           | `task_progress`, `checkpoint_created`, `conditional_rules_applied`, `error` など                                        |
| `ask`                    | `resume_task` など                                                                                                      |

- `text` が JSON 文字列の種別は二重エンコードなので、もう一度パースする。
- `partial: true` は表示途中の状態。同じ内容の確定版が後に来るので重複として扱う。
- 確認した版では `cost` が整数の 0 のことがあり、コストの集計に使えない場合がある。

最小の例（値は架空）:

```json
{
  "ts": 1780000000000,
  "type": "say",
  "say": "api_req_started",
  "conversationHistoryIndex": 0,
  "text": "{\"request\":\"...\",\"tokensIn\":100,\"tokensOut\":20,\"cacheWrites\":0,\"cacheReads\":0,\"cost\":0.0}"
}
```

### `task_metadata.json`

`{files_in_context[], model_usage[], environment_history[]}`。

- `files_in_context[]`: `{path, record_state, record_source, cline_read_date, cline_edit_date, user_edit_date}`
- `model_usage[]`: `{ts, model_id, model_provider_id, mode}`。最後の要素が直近のモデル
- `environment_history[]`: `{ts, os_name, os_version, os_arch, host_name, host_version, cline_version}`。拡張の版の確認に使える（ホスト名を含む）

### レガシー形式で取れないもの

- 終了時刻とタイトルの明示的なフィールドは無い。終了は `ui_messages` の最後の `ts`、タイトルは `task` の先頭で代用する。開始は最初の `ui_messages` の `ts` が確実。
- ツール呼び出しと結果の ID による厳密な対応は取りにくい。ツール名は `ui_messages` の `say: "tool"` から取る。

## セッション⇔プロジェクト対応

- **A**: `cwd` と `workspace_root` に絶対パスが直接入る（パスのエンコード規則は無い）。両者は一致しないことがあるので、目的に応じて選ぶ。`metadata.git.url`・`branch` も手がかりになる。
- **B**: `taskHistory.json` の `cwdOnTaskInitialization`。SDK はこれを `cwd` と `workspaceRoot` の両方に写している（ソース）。
- **使えないもの**: `data/workspaces/<8 桁 hex>/`（トグルだけ）と `checkpoints/<数字>/`（パスのハッシュと推定。中身は shadow git）。
- Windows ではドライブレターの大小（`c:\` と `C:\`）が混在する。比較の前に正規化する。

## 読み取り安全性・保持期間

- **SQLite は読み取り専用で開く**: `sessions.db` は WAL モード。`file:<path>?mode=ro` の URI で開く。`immutable=1` でも開けるが WAL を読まないので最新を取りこぼす（`cron.db` などは未チェックポイントの WAL が大きいことがある）。`mode=ro` を優先し、失敗したときだけ `immutable=1` に落として「不完全かもしれない」と明示する。書き込み接続は使わない。
- **JSON は書き込み中に丸ごと書き換わる**（推定）。パースに失敗したら 1 回だけ再試行し、だめならそのファイルを飛ばす。実行中のセッションは `ended_at` が無いか古い。
- **サイズ**: セッション JSON は数百 KB 程度で全体読み込みで足りる。`logs/hub-daemon.log` のような巨大ログは対象にしない。
- **保持期間**: 自動ローテーション・保持期間の公式記載は見つかっていない。手動の削除は CLI の `cline history`、拡張は UI のタスク削除。SDK にはコンパクション成果物のパス（`sessionCompactionPath`）があるが、ファイルの実物は未確認。

## 秘密情報

次のファイルは開かない。履歴を glob で走査するときも明示的に除外する。

- `~/.cline/data/secrets.json`（API キー）
- `~/.cline/data/settings/providers.json`（プロバイダの API キー）
- `globalState.json` の `openAiHeaders`（認証ヘッダが入りうる）

履歴そのものにも機密が含まれる。外部に出すときは次を伏せる。

- 会話本文、`prompt`、`system_prompt`、`task`、`tool_result`（ファイル内容・コマンド出力）、`ui_messages` の `request`・`content`
- `cache/user_input_history.jsonl`、`files_in_context[].path`、`metadata.git.url`
- ホスト名（`logs/cline.log`、`environment_history[].host_name`）

## 公式記載と実データ推定の区別・確認バージョン

確認日: 2026-11-17。確認した版: Cline CLI 3.0（3.0.46）、VS Code 拡張 4.0（4.0.11、VS Code 1.130.0）。

**公式に記載あり**（docs.cline.bot と cline/cline リポジトリ）

- `~/.cline/data` のレイアウトと `CLINE_DATA_DIR`（Getting Started の config ページ）
- `sessions.db` は SQLite の索引で JSON が正本（SDK hub-spoke ページ。ただし DB の位置は古い記載）
- `<sid>.messages.json` が正規の再生・エクスポート成果物（`sdk/packages/core/docs/messages-contract-v1.md`）
- `SessionSource` の enum（`sdk/packages/core/src/types/common.ts`）、データディレクトリの解決（`sdk/packages/shared/src/storage/paths.ts`）
- 旧形式 `~/.cline/data/tasks/<id>/api_conversation_history.json` が MessageParam 形式（Prompt Storage ページ、`.clinerules/storage.md`）
- マイグレーションで VS Code 側の taskHistory を消さないこと、`cwdOnTaskInitialization` を cwd に写すこと（`apps/vscode/src/hosts/vscode/vscode-to-file-migration.ts`、`apps/vscode/src/sdk/sdk-task-history.ts`）
- `cline history` サブコマンド

**実データからの推定（バージョン依存・未保証）**

- 各フィールド表の具体的なキー、`metadata` のキー構成の揺れ
- `metrics` の形（A・B とも）、`api_req_started` の `text` の中身、`say`・`ask` の種別一覧
- `sessions.db` の実際の位置（`data/db/`）、列、WAL の挙動
- `workspaces/`・`checkpoints/` の中身、ログファイルのキー
- macOS・Linux の globalStorage のパス（VS Code の慣例からの推定）
- 移行時の重複除去に使う `legacyTask`・`migratedFromLegacyTask`、サブエージェントの `childArtifactFileStem`（ソースからの推定）

## 未確認事項

- 新しい拡張（SDK 版）が書く `source: "vscode"` のセッションの実物と、どの拡張バージョンから A に書くか
- サブエージェント・チームの実データ（子の `.messages.json` の命名、`parent_session_id` の値、`aggregateUsage` との関係）
- コンパクション成果物（`sessionCompactionPath`）のファイル名・形式と、`messages.json` 内での要約の表現
- レガシーの `ui_messages` で今回見ていない種別（`deleted_api_reqs`、`completion_result`、`command` など）と、`conversationHistoryDeletedRange`（コンテキスト切り詰め）の扱い
- レガシー版で native tool calling を有効にしたとき `api_conversation_history` に `tool_use` ブロックが出るか
- 保持期間・自動削除の公式仕様。`cline history` の削除が JSON と DB の両方を消すか
- macOS・Linux の globalStorage の実パス

公式仕様の最新を確かめるときは **cline-docs スキル**を使う。
