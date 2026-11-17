---
# 同梱ファイル: format.md（B: CLI store.db と C: IDE state.vscdb の詳細）
name: cursor-logs
description: >-
  Cursor（IDE と CLI の cursor-agent/agent）のローカルに残るチャット・エージェント会話ログ
  （projects/*/agent-transcripts の JSONL、CLI の chats/store.db、IDE の state.vscdb）の
  所在・保存系統・レコード構造・プロジェクトとの対応・安全な読み方・秘密情報の扱いを説明する。
  「Cursor の過去の会話を探したい」「Cursor のログを集計・解析したい」「Cursor の会話履歴が
  どこに保存されるか知りたい」「transcript に時刻やモデルが無い理由を知りたい」ときに使う。
  ルールやエージェント機能など Cursor の機能全般は対象外（cursor-docs を使う）。
meta:
  tag: []
  requires_repo_tools: none
  requires_env: none
  dependencies: none
  requires_install: none
  requires_hooks: none
  requires_skills: cursor-docs
  status: experimental
  description: Cursorのローカルログ（3系統）の所在と形式
  version: 1.0.0
---

# Cursor のローカルログ（3 系統）

Cursor IDE と CLI（`cursor-agent`／`agent`）がローカルに残す会話ログの所在と形式をまとめる。保存先は 3 系統あり、**A（agent-transcripts の JSONL）を正本**、B（CLI の `store.db`）と C（IDE の `state.vscdb`）を補完として扱う。B・C の内部構造は同梱の [format.md](format.md) にある。

> Cursor の公式文書にはローカル保存形式の記載が見つからない。本スキルの内容は**ほぼすべて実データからの推定で、バージョン依存・未保証**（確認した版と日付は「公式記載と推定の区別」を参照）。

## 所在

| 系統                           | Windows                                                                                                       | macOS / Linux                                                                            |
| ------------------------------ | ------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| A. transcript（IDE・CLI 共通） | `%USERPROFILE%\.cursor\projects\<enc-cwd>\agent-transcripts\<sessionId>\<sessionId>.jsonl`                    | `${CURSOR_CONFIG_DIR:-~/.cursor}/projects/<enc-cwd>/agent-transcripts/...`               |
| A'. サブエージェント           | 同じ `<sessionId>\` の下の `subagents\<id>.jsonl`                                                             | 同左                                                                                     |
| B. CLI chats                   | `%USERPROFILE%\.cursor\chats\<md5(cwd)>\<chatId>\{meta.json, store.db[-wal,-shm], prompt_history.json}`       | `~/.cursor/chats/`（新しい版では `~/.config/cursor/chats/` という報告もある）            |
| C. IDE SQLite                  | `%APPDATA%\Cursor\User\globalStorage\state.vscdb` と `workspaceStorage\<32hex>\{state.vscdb, workspace.json}` | mac: `~/Library/Application Support/Cursor/User/...`、Linux: `~/.config/Cursor/User/...` |

- 環境変数 `CURSOR_CONFIG_DIR` で `~/.cursor` を上書きできるという情報がある（サードパーティ文書。未検証）。探索時は既定パスと併せて候補に入れる。
- `projects\<enc-cwd>\` の下にはほかに `terminals/`、`agent-tools/*.txt`、`uploads/`、`canvases/`、`mcps/`、`repo.json`（`{id}`）がある。
- 補助データ: `~/.cursor/ai-tracking/ai-code-tracking.db`（SQLite。`ai_code_hashes` に model・conversationId・timestamp など）。`ide_state.json`・`agent-cli-state.json` は状態フラグだけでログではない。

## 保存系統と正本

| 系統 | 中身                                                 | 位置づけ                                                                                |
| ---- | ---------------------------------------------------- | --------------------------------------------------------------------------------------- |
| A    | 会話本文とツール呼び出しの入力（JSONL）              | **正本**。IDE と CLI の両方が同じ形式で書く。標準ライブラリの JSON 読み込みだけで扱える |
| B    | CLI セッションの完全な状態（ツール結果・推論を含む） | 補完。cwd・タイトル・モデル・作成／更新時刻・tool-result を補う                         |
| C    | IDE Composer/Agent の完全な状態（時刻・ツール結果）  | 補完。セッション一覧・cwd・タイトル・モデル・メッセージ単位の時刻・ツール結果を補う     |

**A の最大の注意点**: A には**時刻・モデル・usage・ツール結果（tool_result）・メッセージ id・親子リンクが無い**。

- 時刻は user 行に埋め込まれた `<timestamp>` タグから復元する（後述）。assistant 行は直前の user 行の時刻を引き継ぐしかない。タグが無ければファイルの mtime で代用する。
- モデル・タイトル・正確な開始／終了時刻は B（`meta.json`・`store.db` の meta）か C（`composerHeaders`・`composerData`）から取る。
- ツール結果は B の `tool-result` か C の `toolFormerData.result` にしかない。A のツール呼び出しとの対応は「同じツール名と引数の出現順」で突き合わせるしかない。
- トークン数・コストはどの系統からもローカルでは実質取れない（C の `tokenCount` は確認した全件で 0）。

## レコード構造（A: transcript JSONL）

1 行 1 JSON。レコード種別は次の 2 つだけ。

| 種別       | フィールド                                                                              | 備考                                                                     |
| ---------- | --------------------------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| メッセージ | `role`（`user`／`assistant`）、`message.content[]`                                      | content 要素は `{type:"text", text}` か `{type:"tool_use", name, input}` |
| ターン終端 | `type:"turn_ended"`、`status`（`success`／`error`／`aborted`）、`error`（任意の文字列） | ファイル末尾に来ることが多い                                             |

最小例（架空値）:

```json
{"role":"user","message":{"content":[{"type":"text","text":"<timestamp>Monday, Nov 16, 2026, 9:00 AM (UTC+9)</timestamp>\n<user_query>\nREADME を要約して\n</user_query>"}]}}
{"role":"assistant","message":{"content":[{"type":"tool_use","name":"Read","input":{"path":"/home/example/proj/README.md"}}]}}
{"role":"assistant","message":{"content":[{"type":"text","text":"要約です。"}]}}
{"type":"turn_ended","status":"success"}
```

### user テキストの埋め込みタグ

- 本文は `<user_query>…</user_query>` で包まれる。
- `<timestamp>Weekday, Mon D, YYYY, H:MM AM (UTC+N)</timestamp>` が user 行のおよそ 9 割に入っている。分単位・UTC オフセット付きのローカル時刻。
  - 曜日・月名は英語固定。ロケールに依存しない解析にする（`strptime` の `%a`/`%b` はロケール依存なので注意）。
  - 日は 1 桁と 2 桁の両方がある。オフセットは `UTC+9` のような形。
- ほかに `<attached_files>`、`<code_selection>`、`<manually_attached_skills>`、`<external_links>`、`<uploaded_documents>` などのタグがある。集計時は本文とタグを分けて扱う。

### tool_use

- `name` の例: `Read`、`Grep`、`Glob`、`StrReplace`、`Write`、`ApplyPatch`、`Shell`、`ReadFile`、`CallDynamicTool`（MCP）、`Task`、`Subagent`、`TodoWrite`、`WebFetch`、`CreatePlan`。版によって増減する前提で、未知の名前を許容する。
- サブエージェントは `Task`／`Subagent` の input `{description, prompt, subagent_type, model?, readonly?, run_in_background?}` で起動される。子の transcript は `subagents/<id>.jsonl` に出るが、**どの呼び出しがどの子かは A だけでは対応付けられない**（`input.model` が A で唯一取れるモデル情報）。

## セッション⇔プロジェクト対応

- **`<enc-cwd>`**: cwd の英数字以外の連続を `-` に置き換え、両端の `-` を落としたものと推定される（例: `C:\work\demo` → `C-work-demo`）。
  - Windows ではドライブ文字の大小が揃わないことがある（`c-work-demo` と `C-work-demo`）。**大文字小文字を無視して照合する。**
  - 変換は可逆ではない（元の `-`・`.`・区切り文字を区別できない）。cwd → enc の方向でだけ使い、正確な cwd は B（`meta.json.cwd`）か C（`workspaceIdentifier.uri.fsPath`・`workspace.json`）から取る。
- 13 桁の数字（エポックミリ秒）や `empty-window` という名前のフォルダは、フォルダを開いていない IDE ウィンドウのもの。C の `composerHeaders.workspaceId` と同じ値になる。
- **セッション ID の共通性**: A の `<sessionId>` は、IDE なら C の `composerId`、CLI なら B の `chatId` と一致する（どちらにも無いものも少数ある）。どちらに id があるかで IDE／CLI を判別できる。A を軸に B・C で補完する。
- B のフォルダ名は `md5(cwd の UTF-8 バイト列)` の hex。C の対応は [format.md](format.md) を参照。

## 読み取り安全性・保持期間

- **SQLite（B・C・ai-tracking）は読み取り専用 URI で開く**: `file:<path>?mode=ro`（`uri=True`）。Cursor 起動中でも開ける。journal_mode は WAL。
  - `immutable=1` でも開けるが WAL を読まないため**直近の書き込みが欠ける**。ロックで開けないときのフォールバックに限り、欠けうることを利用者に伝える。
  - DB ファイルをコピーして読むなら `-wal`・`-shm` も一緒にコピーする。
  - IDE の `globalStorage/state.vscdb` は GB 単位になりうる。`json_extract` で SQL 側で絞り込み、`LIMIT`／`rowid` でページングする。全件を一度にメモリへ載せない。
- **追記中の JSONL**: A は会話中に追記される。最終行が壊れた JSON なら捨てる。
- **保持期間**: 公式の記載は無い。`projects/.agent-data-cleanup-YYYY-MM-DD`（空ファイル）がほぼ毎日作られており、Cursor が自動クリーンアップしていると推定される。基準・日数・対象系統は不明。古いセッションが欠けていても異常とは限らない。逆に、サイドバーから消えても transcript がディスクに残っていたという報告もある。

## 秘密情報

次は読まない、または出力・索引・要約から必ず除外する。

| 対象                                                                             | 扱い                                                         |
| -------------------------------------------------------------------------------- | ------------------------------------------------------------ |
| `blobEncryptionKey`、`speculativeSummarizationEncryptionKey`（`*EncryptionKey`） | B の meta、C の `composerData` にある。必ず除外する          |
| C の `ItemTable` の `secret:*` キー                                              | 読まない                                                     |
| ツール結果（B の `tool-result`、C の `toolFormerData.result`）、C の bubble 本文 | シェル出力・ファイル内容・環境変数が入りうる。原文を出さない |
| B の blobs に混ざるファイル内容キャッシュ                                        | 会話として扱わない                                           |
| `prompt_history.json`、C の `aiService.prompts`、`uploads/`、`terminals/`        | 既定では読まない                                             |
| cwd・URI・パスに含まれるユーザー名                                               | 共有用の出力では伏せる                                       |

A の本文自体も機密を含みうる。会話本文をそのまま外部へ送らない。

## 公式記載と推定の区別

- **公式に記載あり**: なし。cursor.com/docs にはローカル保存先・形式の記述が見つからない（関連は shared transcripts と privacy のページ程度）。CLI の help に `--resume [chatId]`・`ls`・`resume`・`create-chat` があることだけは確認できる（保存先の記述は無い）。
- **実データからの推定（バージョン依存・未保証）**: 本スキルのパス・フィールド・エンコード規則・ID の対応・件数に関する記述すべて。
  - 確認した版: **Cursor IDE 3.30 系 / CLI（cursor-agent）2026.10 系、2026-11-17**、Windows 上で読み取り専用で確認。
  - macOS/Linux のパスと `CURSOR_CONFIG_DIR`、`~/.config/cursor/chats` は forum とサードパーティ文書による傍証のみ。
- 形式は予告なく変わる。読み取りが壊れたら、まず版の違い（C の `composerData._v`、B の `meta.json.schemaVersion`）を確認する。

## 未確認事項

- 自動クリーンアップ（`.agent-data-cleanup-*`）の基準・日数・対象系統（A/B/C）。
- A の `subagents/<id>` と親の `Task`／`Subagent` 呼び出しの対応付け（B の `subagentInfo.toolCallId`、C の `subagentComposerIds` で取れる見込みだが未検証）。
- C の `tokenCount` が常に 0 なのは仕様か。ローカルで usage・cost を取れる場所は ai-tracking.db の model 列以外に見つかっていない。
- macOS/Linux での実パス（`~/.cursor` か `~/.config/cursor` か）と、CLI の版ごとの移行。
- `blobEncryptionKey` がある `store.db` で一部の blob が暗号化されるか（確認範囲ではメッセージは平文 JSON）。
- C の `agentKv:blob:*` の中身と、4 分割 `bubbleId` キーの第 3 要素の意味（[format.md](format.md)）。

## 関連

- B・C の内部構造: [format.md](format.md)
- Cursor の機能全般・公式ドキュメント: **cursor-docs** スキル
