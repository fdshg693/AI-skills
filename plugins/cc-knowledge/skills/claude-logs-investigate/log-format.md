# Claude Code ローカルログのファイル形式

`~/.claude/` に残るセッショントランスクリプトと周辺ファイルの、ファイル別の形式・読み方の注意。所在の概要とデバッグ手段は [SKILL.md](SKILL.md) の「既存ログを見る」にあり、ここではそれに無い事項を中心に書く。

- 確認バージョン: Claude Code 2.1.325、2026-11-17。実データの `version` は 2.1.301〜2.1.325。
- 公式に書かれているのは所在・保持・平文保存・ディレクトリ名の規則まで。**レコードの構造は公式に記載が無く、ほぼすべて実データからの推定**（バージョン依存・未保証）。区別は「公式記載／実データ推定の区別」の節にまとめた。
- 例の値はすべて架空。

## 所在

- 基点は `~/.claude`（Windows は `%USERPROFILE%\.claude`、macOS/Linux は `~/.claude`）。`CLAUDE_CONFIG_DIR` を設定すると全体がそのディレクトリへ移る。
- 一時ディレクトリ（scratchpad）は基点の外: Windows は `%TEMP%\claude\<project>\<session>\scratchpad\`、Linux は `/tmp/claude-<uid>/...`、macOS は `/private/tmp/claude-<uid>/...`。

| パス（`~/.claude/` から）                                                              | 中身                                                                                  |
| -------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| `projects/<enc-cwd>/<sessionId>.jsonl`                                                 | メインのトランスクリプト（正本）                                                      |
| `projects/<enc-cwd>/<sessionId>/subagents/agent-<agentId>.jsonl`・`.meta.json`         | サブエージェントのトランスクリプト（メインと同じ形式）と、そのメタデータ              |
| `projects/<enc-cwd>/<sessionId>/subagents/workflows/wf_<id>/agent-*.jsonl`             | Workflow から起動したサブエージェント。同じフォルダに `journal.jsonl`（公式記載なし） |
| `projects/<enc-cwd>/<sessionId>/tool-results/<rand>.txt`                               | 大きいツール出力の退避先                                                              |
| `projects/<enc-cwd>/<sessionId>/mcp-tasks/`                                            | MCP タスクの再開用データ                                                              |
| `projects/<enc-cwd>/<sid>.orphaned-<ts>-<suffix>.jsonl`・`<sid>.jsonl.superseded-<ts>` | 退避された旧トランスクリプト。セッション一覧（`/resume`）には出ない                   |
| `projects/<enc-cwd>/memory/*.md`                                                       | auto memory。ログではない                                                             |
| `history.jsonl`                                                                        | 入力したプロンプトの履歴（プロジェクト横断）                                          |
| `sessions/<pid>.json`                                                                  | 実行中セッションの登録簿                                                              |
| `stats-cache.json`                                                                     | `/usage` 用の集計キャッシュ                                                           |
| `file-history/<sessionId>/<hash>@v<n>`                                                 | 編集前のファイルの写し（チェックポイント用）                                          |
| `debug/<sessionId>.txt`・`session-env/<sessionId>/`・`shell-snapshots/`                | [SKILL.md](SKILL.md) 参照                                                             |
| `plans/`・`tasks/`・`paste-cache/`・`image-cache/`・`teams/`                           | 公式に記載あり。中身の形式は未確認                                                    |
| `todos/`・`statsig/`・`logs/`                                                          | 旧版の名残。今の版では書かれない                                                      |

## 保存系統と正本

- **正本は `projects/<enc-cwd>/<sessionId>.jsonl`**（とその子の `subagents/**/agent-*.jsonl`）。会話・ツール呼び出し・ツール結果に加え、システムプロンプト・ツール定義・リクエストのパラメータまで入る（公式記載）。
- `history.jsonl`・`sessions/*.json`・`stats-cache.json` は補助。入力の履歴、実行中の一覧、集計キャッシュであって、会話の正本ではない。
- `tool-results/*.txt` はトランスクリプトから参照される本体の退避先。必要なときだけ開く。
- `*.orphaned-*`・`*.superseded-*` は退避された旧版。現行セッションとして数えない。`journal.jsonl`・`memory/` もトランスクリプトではない。
- **読まずに飛ばしてよいレコード**: `api-request`・`api-request-shape`・`api-request-blob` は API リクエストの重複保存で、大きく、会話本文やシステムプロンプトを含む。行の文字列に `"type":"api-request` が含まれるかで、パース前に判定して捨てると速い。

## レコード構造

形式は JSONL（1 行 1 JSON、基本は追記のみ）。1 行が数百 KB〜1MB 近くになることがあるので、全体を読み込まずに行ごとにストリームで読む。

### 種別（`type`）

| 種別                                                     | 内容                                                                                                                          |
| -------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| `user` / `assistant`                                     | 会話本体                                                                                                                      |
| `attachment`                                             | 注入された文脈（`attachment.type` が `environment`・`nested_memory`・`date`・`skill_listing`・`edited_text_file` など 27 種） |
| `system`                                                 | `subtype` が `stop_hook_summary`・`turn_duration`・`api_error`・`local_command` など                                          |
| `cost-state`                                             | セッションのコストとトークンの累積値                                                                                          |
| `ai-title` / `custom-title` / `last-prompt`              | 自動の題 `aiTitle` / `/rename` の題 `customTitle` / `lastPrompt`・`leafUuid`                                                  |
| `session-owner`                                          | `accountUuid`・`organizationUuid`。ファイル先頭行のことが多い                                                                 |
| `queue-operation`                                        | `operation`（`enqueue` / `dequeue` / `remove`）・`content`                                                                    |
| `file-history-snapshot` / `file-history-delta`           | `trackingPath`・`backup.backupFileName` など                                                                                  |
| `pr-link`                                                | `prNumber`・`prUrl`・`prRepository`                                                                                           |
| `mode` / `permission-mode` / `tools-used` / `atis-latch` | 種別名どおり。`tools-used.tools[]` は使ったツール名の一覧                                                                     |
| `api-request` / `api-request-shape` / `api-request-blob` | リクエストの `params`・`shape.system[]`/`shape.tools[]`・`message` の重複保存（上記のとおり飛ばす）                           |

ファイルの先頭行は `user` とは限らない（`session-owner`・`queue-operation` が多い）。版ごとに種別が増えるので、知らない `type` は無視して読み進める。

### 会話レコードの共通フィールド（`user` / `assistant` / `attachment` / `system`）

| フィールド                                   | 意味                                                                                                    |
| -------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| `uuid`・`parentUuid`                         | レコードの木構造。`parentUuid` が null なのはファイル先頭の `user`                                      |
| `isSidechain`                                | サブエージェントのファイルでは true、メインでは false                                                   |
| `sessionId`                                  | メインではファイル名と一致。サブエージェントでは親のセッション ID、Workflow 配下では祖先のセッション ID |
| `agentId`                                    | サブエージェントのレコードだけにある。ファイル名 `agent-<agentId>` と対応                               |
| `timestamp`                                  | ISO8601 の UTC、ミリ秒付き（`2026-01-01T00:00:00.000Z`）                                                |
| `cwd`・`gitBranch`・`version`・`userType`    | 起動環境。`cwd` はセッション途中で変わりうる                                                            |
| `entrypoint`                                 | `cli`・`claude-vscode`・`sdk-cli`・`sdk-py` など                                                        |
| `promptId`（user）・`requestId`（assistant） | ターン・API リクエストとの対応                                                                          |

### `assistant`

- `message` は API の Message をそのまま持つ（`id`・`model`・`role`・`content[]`・`stop_reason`・`usage`）。ほかに `requestedModel`・`effort`・`isApiErrorMessage`・`error`。
- **1 レコードに content ブロックは 1 個だけ。** 1 つの API 応答（`thinking`＋`text`＋`tool_use` など）が、同じ `message.id` を持つ複数のレコードに分かれて記録される。
- `usage` は同じ `message.id` のレコードにほぼ同じ値が繰り返し入る。**トークンを合計するときは `message.id`（または `requestId`）ごとに 1 回だけ数える**（同じ id の最後のレコードを採るのが無難）。そのまま足すと数倍に膨らむ。
- `usage` の中身: `input_tokens`・`output_tokens`・`cache_creation_input_tokens`・`cache_read_input_tokens`・`cache_creation{}`・`service_tier`・`server_tool_use`・`output_tokens_details` など。
- `message.model` が `<synthetic>` のものはエラーなどの合成応答で、実際のモデル呼び出しではない。

### `user`

- `message.content` は文字列（人の入力）か配列。配列の要素は `tool_result`・`text`・`image`。
- ツール結果のレコードには `toolUseResult` が付く。ツールごとの構造化データ（`stdout`・`stderr`、`filePath`・`originalFile`・`structuredPatch`、`oldString`・`newString`、`persistedOutputPath` など）。`sourceToolAssistantUUID` が呼び出し元の assistant レコードを指し、`tool_result.tool_use_id` が `tool_use.id` と対応する。
- `isMeta: true` はシステムが注入したもので、人の入力ではない。

### `cost-state`

`totalCostUSD`・`totalDuration`・`startTime`（epoch ms）・`totalLinesAdded`・`totalLinesRemoved`・`modelUsage{<model>: {inputTokens, outputTokens, thinkingTokens, cacheReadInputTokens, cacheCreationInputTokens, webSearchRequests, costUSD}}`。値は累積なので、**最後の `cost-state` がそのセッションの合計**になる（推定）。レコード単位のコストは無い。

### 最小例（値はすべて架空）

```json
{"type":"assistant","uuid":"22222222-0000-0000-0000-000000000002","parentUuid":"22222222-0000-0000-0000-000000000001","isSidechain":false,"sessionId":"11111111-1111-1111-1111-111111111111","timestamp":"2026-01-01T00:00:00.000Z","cwd":"C:\\Users\\alice\\proj","version":"2.1.325","requestId":"req_example","message":{"id":"msg_example","model":"claude-opus-5-5","role":"assistant","content":[{"type":"tool_use","id":"toolu_example","name":"Bash","input":{"command":"ls"}}],"usage":{"input_tokens":10,"output_tokens":20,"cache_read_input_tokens":30,"cache_creation_input_tokens":40}}}
{"type":"user","uuid":"22222222-0000-0000-0000-000000000003","parentUuid":"22222222-0000-0000-0000-000000000002","sessionId":"11111111-1111-1111-1111-111111111111","timestamp":"2026-01-01T00:00:01.000Z","sourceToolAssistantUUID":"22222222-0000-0000-0000-000000000002","message":{"role":"user","content":[{"type":"tool_result","tool_use_id":"toolu_example","content":"README.md"}]},"toolUseResult":{"stdout":"README.md","stderr":"","interrupted":false}}
{"type":"cost-state","sessionId":"11111111-1111-1111-1111-111111111111","totalCostUSD":0.12,"startTime":1700000000000,"modelUsage":{"claude-opus-5-5":{"inputTokens":10,"outputTokens":20,"costUSD":0.12}}}
```

### サブエージェントの `.meta.json` と `journal.jsonl`

- `.meta.json`: `agentType`・`description`・`toolUseId`（親の Agent 呼び出しの `tool_use.id`）・`spawnDepth`・`finished`・`isBuiltIn`、任意で `model`・`effort`・`workflowPhase`。
- `journal.jsonl`（Workflow 配下）: `type`・`agentId`・`key`・`label`・`phase`。

### 周辺ファイル

| ファイル              | フィールド                                                                                                                                     |
| --------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| `history.jsonl`       | `display`・`pastedContents{}`・`timestamp`（epoch ms の整数）・`project`（cwd の絶対パス）・`sessionId`                                        |
| `sessions/<pid>.json` | `pid`・`sessionId`・`cwd`・`startedAt`・`updatedAt`（epoch ms）・`version`・`kind`・`entrypoint`・`name`・`status`・`messagingSocketPath` など |
| `stats-cache.json`    | `version`・`dailyActivity[]`・`dailyModelTokens[]`・`modelUsage{}`・`totalSessions`・`longestSession`・`hourCounts`                            |

時刻の表し方がファイルで違う（トランスクリプトは ISO8601 文字列、`history.jsonl`・`sessions/`・`cost-state.startTime` は epoch ms）。

## セッション⇔プロジェクト対応

- `<enc-cwd>` は起動時の cwd の英数字以外をすべて `-` に置き換えたもの。例: `C:\Users\alice\proj` → `C--Users-alice-proj`。
- **変換は元に戻せない。** `proj/temp` と `proj-temp` はどちらも `proj-temp` になる。プロジェクトの判定は**各レコードの `cwd` を正**にし、ディレクトリ名は絞り込みの手掛かりにとどめる。
- **Windows ではドライブレターの大文字・小文字が起動元の書き方のまま残る。** VS Code から起動すると小文字になりやすく、同じフォルダが `c--Users-alice-proj` と `C--Users-alice-proj` の 2 ディレクトリに分かれる。パスで絞るときはディレクトリ名を大文字小文字を区別せずに比べ、レコードの `cwd` もドライブレターを正規化してから比べる。
- `cwd` はセッションの途中で変わりうる（サブディレクトリへの移動など）。プロジェクトは最初の `user` か `attachment` の `cwd` で決めるとよい。
- サブエージェントとの対応:
  - ファイルは親セッションのフォルダ `<sessionId>/subagents/` の下にあり、レコードの `sessionId` は親（Workflow 配下では祖先）のもの、`isSidechain` は true。
  - `.meta.json` の `toolUseId` が、親トランスクリプトの Agent 呼び出し（`tool_use.id`）を指す。
  - `projects/<enc-cwd>/*.jsonl` を列挙するときは直下だけを見る。再帰するとサブエージェントを別セッションとして数えてしまう。
- 公式 Agent SDK の `listSessions({dir})`（TS）／`list_sessions`（Python）は git worktree の別パスもまとめて返す（`includeWorktrees`）。`getSessionMessages` と合わせて、形式の参照先として使える。

## 読み取り安全性・保持期間

- **読み取り**: SQLite は使っておらず、ロックもかからない（推定）。書き込み中のファイルは最終行が途中で切れていることがあるので、JSON のパースエラーは行単位で読み飛ばす。文字コードは UTF-8 で、不正なバイトは置換して読む。
- **保持（公式記載）**: `settings.json` の `cleanupPeriodDays`（既定 30、最小 1。0 は検証エラー）を過ぎたものがスイープされる（いつ実行されるかは未確認）。
  - 対象: `projects/*/<session>.jsonl`、`subagents/`（親と一緒に消える）、`tool-results/`、`file-history/`（直近 100 チェックポイント分は残す）、`debug/`、`plans/`、`session-env/`、`tasks/`、`paste-cache/`、`shell-snapshots/`（正常終了時にも削除）。
  - **消えないもの**: `history.jsonl` と `stats-cache.json` は手で消すまで残る（HIPAA 構成のときだけ `history.jsonl` の古い行が消える）。`memory/` も対象外。古いセッションの痕跡はこの 2 つに残りうる。
  - `sessions/<pid>.json` はセッション終了時に消える。
  - Desktop・Cowork で始めたセッションは `desktopSessionCleanupPeriodDays` に従う（v2.1.248 以降）。`--bare` のときと設定が壊れているときはスイープが止まる。
  - 最後にスイープした時刻は `~/.claude/.last-cleanup` にある（公式記載なし）。

## 秘密情報

公式に「平文で保存し暗号化しない。`.env` を読めば値がトランスクリプトに残る」とある。

- **読まない**: `~/.claude/.credentials.json`。
- **本文として扱い、そのまま出力しない**:
  - 会話・出力: `message.content` の text、`tool_use.input`、`tool_result.content`、`toolUseResult`（`originalFile` はファイル全文）、`tool-results/*.txt`、`api-request-blob`、`api-request-shape`（システムプロンプト・CLAUDE.md の中身）
  - 入力・貼り付け: `attachment`、`queue-operation.content`、`last-prompt`、`history.jsonl` の `display`・`pastedContents`
  - 識別子: `session-owner` の `accountUuid`・`organizationUuid`、`pr-link`、`cwd`（ユーザー名を含む）
  - その他: `file-history/` の写し、`shell-snapshots/`（環境変数）
- 集計や一覧に使うのは `type`・`timestamp`・`message.model`・`usage`・ツール名（`tool_use.name`）・`cost-state` の数値など、本文を含まないフィールドにとどめるのが安全。

## 公式記載／実データ推定の区別

確認: Claude Code 2.1.325（2026-11-17）。

**公式に記載あり**（`code.claude.com/docs/en/claude-directory`、settings、Agent SDK。`claude-code-docs` スキルで最新版を確認できる）

- `~/.claude` の所在と `CLAUDE_CONFIG_DIR`、scratchpad の所在
- トランスクリプトに会話・ツール・システムプロンプト等が平文で入ること
- `subagents/`（メインと同じ形式）、`tool-results/`、`mcp-tasks/`、orphaned / superseded の扱い
- `<project>` のエンコード規則（非英数字を `-`）
- `cleanupPeriodDays`・`desktopSessionCleanupPeriodDays` とスイープの対象・対象外
- SDK の `listSessions` / `getSessionMessages` / `list_sessions`

**実データからの推定**（公式記載なし。バージョン依存・未保証）

- レコードの `type` 一覧と各フィールド
- assistant の 1 ブロック 1 行の分割と `usage` の重複
- `cost-state` の値が累積であること
- ドライブレターの大文字小文字によるディレクトリの分裂、`cwd` の途中変更
- `subagents/workflows/`・`.meta.json`・`journal.jsonl` の構造
- `.last-cleanup`

## 未確認事項

- compact の記録のされ方。SDK のストリームでは `system` / `compact_boundary` と `compact_metadata{trigger, pre_tokens}` だが、トランスクリプト側が同じ形か（`compactMetadata`・`logicalParentUuid`・`isCompactSummary` の有無）は未確認。
- 旧形式の `summary`・`progress` レコードが今の版で出るか。古いファイルに残っている可能性はあるので、未知の種別として読み飛ばせるようにしておく。
- サブエージェントのトークン・コストが親の `cost-state` に含まれるか。`/resume` や fork のあとで `cost-state` が累積し直されるか。
- 同じ `message.id` で `usage` の値が違うレコードがまれにある理由（ストリーミング途中の値か）。
- 長いパス（200 文字超など）でディレクトリ名が切り詰め・ハッシュ化されるか。
- CLI 単体で起動したときのドライブレターの大文字小文字。
- `teams/`・`debug/`・`session-env/`・`plans/`・`tasks/` などの中身の形式。
