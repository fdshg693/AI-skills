# Cursor ログ形式の詳細（B: CLI store.db / C: IDE state.vscdb）

[SKILL.md](SKILL.md) の補足。ここに書く内容は**すべて実データからの推定で、バージョン依存・未保証**（Cursor IDE 3.30 系 / CLI 2026.10 系、2026-11-17 に Windows で確認）。値はすべて架空。

SQLite はどれも `file:<path>?mode=ro` の URI で読み取り専用に開く（理由は SKILL.md の「読み取り安全性」）。

## B. CLI chats（`~/.cursor/chats/<md5(cwd)>/<chatId>/`）

| ファイル               | 中身                                                                |
| ---------------------- | ------------------------------------------------------------------- |
| `meta.json`            | セッションのメタデータ（下表）                                      |
| `store.db`（+wal/shm） | SQLite。会話の完全な状態                                            |
| `prompt_history.json`  | 入力したプロンプト文字列の list。**秘密情報扱い（既定で読まない）** |

フォルダ名は `md5(meta.json.cwd の UTF-8)` の hex。`store.db` が無いチャットもある（作成だけされたもの）。

### meta.json

| フィールド        | 型      | 意味                                     |
| ----------------- | ------- | ---------------------------------------- |
| `schemaVersion`   | number  | 確認時は `1`                             |
| `createdAtMs`     | number  | 作成時刻（エポックミリ秒）               |
| `updatedAtMs`     | number  | 更新時刻（エポックミリ秒）               |
| `cwd`             | string  | 作業ディレクトリ（ユーザー名を含みうる） |
| `hasConversation` | boolean | 会話があるか                             |
| `title`           | string? | タイトル（任意）                         |

```json
{
  "schemaVersion": 1,
  "createdAtMs": 1763251200000,
  "updatedAtMs": 1763254800000,
  "cwd": "/home/example/proj",
  "hasConversation": true,
  "title": "README の要約"
}
```

### store.db のテーブル

| テーブル           | 内容                                                         |
| ------------------ | ------------------------------------------------------------ |
| `meta(key, value)` | key `'0'` の 1 行だけ。value は **hex エンコードした JSON**  |
| `blobs(id, data)`  | content-addressed。`id = sha256(data)`（確認した全件で一致） |

`meta` の値（hex → UTF-8 → JSON）:

| キー                                | 意味                                                                                 |
| ----------------------------------- | ------------------------------------------------------------------------------------ |
| `agentId`                           | エージェント ID                                                                      |
| `latestRootBlobId`                  | 最新の root blob の id                                                               |
| `name`                              | セッション名                                                                         |
| `mode`                              | `default`／`search`／`auto-run`／`plan`                                              |
| `approvalMode?`、`isRunEverything?` | 承認モード                                                                           |
| `createdAt`                         | 作成時刻                                                                             |
| `lastUsedModel?`                    | 最後に使ったモデル名                                                                 |
| `subagentInfo?`                     | `{parentAgentId, rootParentAgentId, toolCallId, typeName}`（サブエージェントのとき） |
| `blobEncryptionKey?`                | **秘密。読み出しても出力しない**                                                     |

### root blob（protobuf）

- `latestRootBlobId` が指す blob は protobuf。
- **field 1（wire type 2、長さ 32 バイト、repeated）がメッセージ blob の id（sha256 の生バイト）を会話順に並べた列**。hex にして `blobs.id` と突き合わせる。
- ほかのフィールドの意味は未確認。field 1 以外は読み飛ばせばよい。
- 外部ライブラリなしで読める。varint（7 ビットずつ、最上位ビットが継続フラグ）でタグと長さを読み、`tag >> 3 == 1` かつ `tag & 7 == 2` の要素だけ集め、他の wire type（0: varint、1: 64bit、2: 長さ付き、5: 32bit）は長さ分スキップする。
- **blobs を全件走査しない**。blobs にはファイル内容のキャッシュ（JSON や生テキスト）も混在するため、root blob から辿った id だけを会話として扱う。

### メッセージ blob（JSON、Vercel AI SDK に似た形）

| フィールド         | 意味                                                                             |
| ------------------ | -------------------------------------------------------------------------------- |
| `id?`              | メッセージ id                                                                    |
| `role`             | `system`／`user`／`assistant`／`tool`                                            |
| `content`          | 文字列、または要素の配列（下表）                                                 |
| `providerOptions?` | `{cursor:{requestId \| modelProviderMessageId \| highLevelToolCallResult \| …}}` |

| content 要素の `type` | フィールド                                                                       |
| --------------------- | -------------------------------------------------------------------------------- |
| `text`                | `text`                                                                           |
| `reasoning`           | `text`、`signature`                                                              |
| `redacted-reasoning`  | `data`                                                                           |
| `tool-call`           | `toolCallId`、`toolName`、`args`                                                 |
| `tool-result`         | `toolCallId`、`toolName`、`result`、`experimental_content`（**原文を出さない**） |

```json
{"role":"assistant","content":[{"type":"tool-call","toolCallId":"call_example01","toolName":"Read","args":{"path":"/home/example/proj/README.md"}}]}
{"role":"tool","content":[{"type":"tool-result","toolCallId":"call_example01","toolName":"Read","result":"(省略)"}]}
```

- メッセージ単位の時刻と usage は**無い**。時刻はセッション単位（`meta.json` の `createdAtMs`／`updatedAtMs`）だけ。
- `tool-call` と `tool-result` は `toolCallId` で結合する。

## C. IDE（`%APPDATA%\Cursor\User\`）

### globalStorage/state.vscdb のテーブル

| テーブル             | 内容                                                |
| -------------------- | --------------------------------------------------- |
| `ItemTable`          | VS Code 由来のキー値。**`secret:*` キーは読まない** |
| `cursorDiskKV`       | `key TEXT, value BLOB`。会話本体（下記の接頭辞）    |
| `composerHeaders`    | セッション一覧。**一覧を取る最良の入口**            |
| `remoteAgentHeaders` | リモートエージェントのヘッダ（中身は未確認）        |

古い版には `composerHeaders` テーブルが無い可能性がある。`ItemTable` の `composer.composerHeaders.migratedToTable` フラグで移行済みかを確認し、無ければ `cursorDiskKV` の `composerData:*` を一覧として使う。

### composerHeaders

| 列                           | 意味                                                       |
| ---------------------------- | ---------------------------------------------------------- |
| `composerId`                 | セッション ID（A の `<sessionId>` と一致）                 |
| `workspaceId`                | ワークスペース ID（`value.workspaceIdentifier.id` と一致） |
| `createdAt`、`lastUpdatedAt` | 作成・更新時刻                                             |
| `isArchived`、`isSubagent`   | アーカイブ済み／サブエージェントか                         |
| `recency`、`checkpointAt`    | 並び順・チェックポイント                                   |
| `value`                      | JSON（下記）                                               |
| `subagentTypeName`           | サブエージェントの種別名                                   |

`value` JSON の主なキー: `name`（タイトル）、`subtitle`、`unifiedMode`、`workspaceIdentifier{id, uri{fsPath, path, scheme}}`、`contextUsagePercent`、`totalLinesAdded`／`totalLinesRemoved`、`filesChangedCount`、`trackedGitRepos`。

### cursorDiskKV のキー接頭辞

| キーの形                                                                                                           | 内容                                                               |
| ------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------ |
| `composerData:<composerId>`                                                                                        | セッション本体のメタデータ（下記）                                 |
| `bubbleId:<composerId>:<bubbleId>`                                                                                 | メッセージ（旧形式、3 分割）                                       |
| `bubbleId:<composerId>:<x>:<bubbleId>`                                                                             | メッセージ（新しめの行の大半、4 分割。第 3 要素の意味は未確認）    |
| `composerConvHeaders:<composerId>:<chunk>`                                                                         | バブルの並び（新形式のチャンク）                                   |
| `agentKv:blob:<x>`                                                                                                 | 件数が最も多い。B と同じ blob 方式の会話状態の可能性があるが未確認 |
| `checkpointId:*`、`codeBlockPartialInlineDiffFates:*`、`ofsContent:*`、`inlineDiff:*`、`composer.content.<sha256>` | 差分・チェックポイント・内容キャッシュ。会話本文としては扱わない   |

value が NULL や非 JSON のこともある。デコードに失敗した行は飛ばす。

### composerData:<composerId>

`_v`（確認時は 13〜18）で形が変わる。主なキー:

| キー                                                                                                      | 意味                               |
| --------------------------------------------------------------------------------------------------------- | ---------------------------------- |
| `createdAt`、`lastUpdatedAt`、`name`、`status`、`unifiedMode`                                             | 基本情報                           |
| `modelConfig{modelName, maxMode, selectedModels}`                                                         | モデル                             |
| `usageData`                                                                                               | 空の `{}` が多い                   |
| `contextTokensUsed`、`contextTokensLimit`、`promptTokenBreakdown{totalUsedTokens, maxTokens, categories}` | セッション単位のコンテキスト使用量 |
| `subComposerIds`、`subagentComposerIds`、`subagentInfo`                                                   | 子セッション                       |
| `workspaceIdentifier`                                                                                     | ワークスペース                     |
| `fullConversationHeadersOnly`／`headerLog`                                                                | バブルの並び（下記）               |
| `blobEncryptionKey`、`speculativeSummarizationEncryptionKey`                                              | **秘密。必ず除外する**             |

### バブルの並び順（3 段フォールバック）

1. 旧形式: `composerData.fullConversationHeadersOnly[]` の各要素 `{bubbleId, type, grouping, createdAt(ISO), startedAtMs, completedAtMs}` の順。
2. 新形式（`_v` 18 の一部）: `composerData.headerLog{chunkSize, chunkCount, count, generation}` があれば、本体は `composerConvHeaders:<composerId>:<chunk>`（chunk 0 から順に、同じ要素の JSON 配列）。
3. どちらも無ければ `bubbleId:<composerId>:` の前方一致で集め、`createdAt` で並べる（3 分割と 4 分割の両方を拾う）。

### bubble JSON

| キー                                                                        | 意味                                                                                                                                                                                  |
| --------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `type`                                                                      | `1` = user、`2` = assistant                                                                                                                                                           |
| `text`                                                                      | 本文（機密を含みうる）                                                                                                                                                                |
| `createdAt`（ISO8601、Z）、`startedAtMs`、`completedAtMs`、`turnDurationMs` | **メッセージ単位の時刻**（A に無い時刻はここで取れる）                                                                                                                                |
| `thinking`                                                                  | 推論                                                                                                                                                                                  |
| `toolFormerData`                                                            | `{tool, name, toolCallId, status(completed/loading/error/cancelled), params, rawArgs, result, additionalData, modelCallId, toolIndex, toolCallBinary}`。`result` は**原文を出さない** |
| `tokenCount{inputTokens, outputTokens}`                                     | 確認した全件で 0。当てにしない                                                                                                                                                        |
| `modelInfo{modelName}`                                                      | ごく一部にだけある                                                                                                                                                                    |
| `requestId`、`checkpointId`                                                 | 関連 ID                                                                                                                                                                               |

ほかに空配列のフィールドが大量にある。未知のキーは無視する。

```json
{
  "type": 2,
  "text": "要約です。",
  "createdAt": "2026-11-16T00:00:05Z",
  "startedAtMs": 1763251201000,
  "completedAtMs": 1763251205000,
  "toolFormerData": {
    "name": "read_file",
    "toolCallId": "call_example01",
    "status": "completed",
    "params": "{}",
    "result": "(省略)"
  }
}
```

### セッション⇔プロジェクト（C）

- `composerHeaders.workspaceId` は `value.workspaceIdentifier.id` と一致する。
- フォルダは `workspaceIdentifier.uri.fsPath`（大半にある）か、`workspaceStorage/<workspaceId>/workspace.json` の `{folder}` または `{workspace}`（URI）で引く。
- workspaceId の一部は `workspaceStorage` に存在しない（削除済み、または 13 桁の数字 ID = フォルダ未オープンのウィンドウ）。

### workspaceStorage/<hash>/state.vscdb

`ItemTable` だけ。旧版の名残で、本文の正本ではない。

| キー                    | 中身                                                        |
| ----------------------- | ----------------------------------------------------------- |
| `composer.composerData` | `{selectedComposerIds, lastFocusedComposerIds}`             |
| `aiService.prompts`     | `[{text, commandType}]`。**プロンプト原文。既定で読まない** |
| `aiService.generations` | `[{unixMs, generationUUID, type, textDescription}]`         |

## 補助: ai-tracking.db

`~/.cursor/ai-tracking/ai-code-tracking.db`（SQLite）。`ai_code_hashes`（model・conversationId・timestamp など）、`scored_commits`、`conversation_summaries`（確認時は 0 件）。AI が生成したコードの追跡用で、会話ログではない。ローカルでモデル名が取れる数少ない場所。
