# hookを使ったログの仕込み方

hook機構そのもの（`writing-hooks`スキルの`hooks.md`相当）の内容を要約せず全節転記した上で、実地検証（Windows 11 / Claude Code v2.1.215）で確認した実際の挙動を **> 実地検証:** として追記してある。加えて、実際に動作確認済みのログ仕込みテンプレートを末尾にまとめてある。

## 目次

- [基本構造](#基本構造)
  - [定義場所とスコープ](#定義場所とスコープ)
- [フックの種類（type）](#フックの種類type)
  - [command（コマンドフック）](#commandコマンドフック)
  - [http（HTTPフック）](#httphttpフック)
  - [mcp_tool（MCPツールフック）](#mcp_toolmcpツールフック)
  - [prompt / agent（判断が必要なフック）](#prompt--agent判断が必要なフック)
- [主なイベント一覧](#主なイベント一覧)
- [マッチャーの評価ルール](#マッチャーの評価ルール)
- [`if` フィールドによる絞り込み](#if-フィールドによる絞り込みツールイベント限定)
- [入出力と制御](#入出力と制御)
- [Windows特有の落とし穴](#windows特有の落とし穴)
- [シェルプロファイルが原因のJSONパースエラー](#シェルプロファイルが原因のjsonパースエラー)
- [async（バックグラウンド）フックの制約](#asyncバックグラウンドフックの制約)
- [セキュリティ上の注意](#セキュリティ上の注意)
- [デバッグ](#デバッグ)
- [実際に動作確認済みのログ仕込みテンプレート](#実際に動作確認済みのログ仕込みテンプレート)

## 基本構造

```json
{
  "hooks": {
    "EventName": [
      {
        // ツール呼び出しなどのパターン（マッチャー）
        "matcher": "ToolPattern",
        // パターンがマッチした場合に、実行するフックハンドラー（複数指定可）
        "hooks": [
          {
            "type": "command",
            "command": "your-command-here"
          }
        ]
      }
    ]
  }
}
```

設定は3階層になっている。

1. **イベント** (`PreToolUse` や `Stop` など) を選ぶ
2. **マッチャーグループ** (`matcher`) で発火条件を絞り込む
3. **ハンドラー** (`hooks` 配列の中身) で実際に実行する処理を定義する

> **実地検証**: `.claude/settings.local.json` にhookを追加/変更しても、**セッション再起動なしでhot reloadされ即座に発火する**ことを確認した。デバッグログに `Watching for changes in setting files C:\Users\xingw\.claude\settings.json, C:\CodeRoot\AI\.claude\settings.json, C:\CodeRoot\AI\.claude\settings.local.json...` という監視ログ行が出ており、この3ファイルが常時watchされている。テスト用hookを仕込んですぐ試したい場合、セッションを再起動する必要はない。

### 定義場所とスコープ

| 場所                            | スコープ                             | 共有可否                             |
| ------------------------------- | ------------------------------------ | ------------------------------------ |
| `~/.claude/settings.json`       | 全プロジェクト共通                   | 不可（マシンローカル）               |
| `.claude/settings.json`         | プロジェクト単位                     | 可（リポジトリにコミット可）         |
| `.claude/settings.local.json`   | プロジェクト単位                     | 不可（gitignore対象）                |
| managed policy settings         | 組織全体                             | 可（管理者制御）                     |
| プラグインの `hooks/hooks.json` | プラグイン有効時のみ                 | 可（プラグインに同梱）               |
| skill / subagentのfrontmatter   | そのコンポーネントが動いている間のみ | 可（コンポーネントファイル内に定義） |

`/hooks` コマンドで現在設定されているフックを読み取り専用で一覧・確認できる（追加・変更・削除は設定JSONを直接編集するか、Claudeに依頼する）。

テスト用hookを仕込んで検証したい場合は、必ず `.claude/settings.local.json`（gitignore対象・個人ローカル）に追加し、プロジェクト共有の `.claude/settings.json` は変更しないこと。検証が終わったら設定を元に戻す。

---

## フックの種類（type）

ハンドラーの `type` フィールドで5種類から選べる。全て並列実行され、同一のハンドラー（コマンド文字列＋argsが同じ、URLが同じ等）は自動的に重複排除される。

| type       | 概要                                                                                       |
| ---------- | ------------------------------------------------------------------------------------------ |
| `command`  | シェルコマンドを実行。stdinでJSON入力を受け取り、exit codeとstdout/stderrで結果を返す      |
| `http`     | イベントのJSONをPOSTリクエストのボディとして送信。レスポンスボディで結果を返す             |
| `mcp_tool` | 接続済みのMCPサーバー上のツールを呼び出す                                                  |
| `prompt`   | Claudeモデル（デフォルトHaiku）に単発で判定させる。yes/noの構造化JSONを返させる            |
| `agent`    | サブエージェントを起動し、Read/Grep/Globなどのツールを使って条件を検証させる（実験的機能） |

### command（コマンドフック）

- 共通フィールドに加えて `command`（必須）, `args`, `async`, `asyncRewake`, `shell` を持つ。
- `args` を指定すると **exec form**（シェルを介さず直接実行）、省略すると **shell form**（`sh -c` やGit Bash、PowerShell経由）になる。
  - パスにスペースや特殊文字を含む場合や、`${CLAUDE_PROJECT_DIR}` などのプレースホルダーを使う場合は exec form (`args: []`) を推奨。
- `async: true` でバックグラウンド実行（後述の「落とし穴」参照）。

> **実地検証**: ログ仕込み用途では、`python -c "..."` のようにコマンド文字列にスクリプトをインラインで書くと、JSON内でのクォートエスケープが破綻しやすい（ダブルクォート・シングルクォート・改行の混在）。
>
> **本スキルでは、ログ仕込み用のスクリプトは常にPythonで書き、`"command": "python", "args": ["<script-path>", "<arg>", ...]` という exec form で呼び出す方針に統一する**（シェルスクリプトやshell form文字列コマンドは使わない）。理由:
>
> - Pythonはbash/PowerShellのシェルスクリプトより可読性が高く、Windows/POSIX間の差異も吸収しやすい
> - exec formは`args`を配列でそのままプロセスに渡すため、**コマンドライン上でのシェルクォート処理が一切発生しない**。フックへの入力（stdinのJSON）自体もクォート処理を経由せず渡るため、shell formで起きがちなクォート/エスケープ由来のトラブル（前段落）が構造的に発生しない
> - 実地検証で、通常のBashトリガーに加えて出力に`'`・`"`を含むBashトリガーでもexec form + pythonが問題なく発火・記録できることを確認済み
> - `python`という拡張子なしコマンド名でもexec formで正しく実行ファイルとして解決される（後述のnpm.cmd検証と同様の仕組み）

### http（HTTPフック）

- `url`（必須）, `headers`, `allowedEnvVars` を持つ。
- ヘッダー値は `$VAR_NAME` / `${VAR_NAME}` で環境変数展開できるが、`allowedEnvVars` に列挙した変数のみ展開される。
- 非2xxレスポンスや接続失敗・タイムアウトは**すべて「ブロックしないエラー」**として扱われ、処理は継続する。ブロックしたい場合は2xxレスポンス＋JSONボディで `decision: "block"` や `permissionDecision: "deny"` を返す必要がある。

### mcp_tool（MCPツールフック）

- `server`（必須）, `tool`（必須）, `input` を持つ。
- 対象のMCPサーバーは**既に接続済み**である必要がある。フック経由でOAuth等の接続フローがトリガーされることはない。
- ツールの返すテキストが有効なJSON出力ならデシジョンとして処理され、そうでなければ単なるテキストとして扱われる。サーバー未接続や `isError: true` の場合は非ブロッキングエラーになる。

### prompt / agent（判断が必要なフック）

- 決定的なルールではなく「判断」が必要な場合に使う。
- `prompt` は1回のLLM呼び出しで `{"ok": true/false, "reason": "..."}` を返させるだけ（デフォルトタイムアウト30秒）。
- `agent` はサブエージェントを起動し、最大50ターンのツール呼び出し（Read/Grep/Globなど）を使って実際のファイルやテスト結果を検証してから同じ形式のJSONを返す（デフォルトタイムアウト60秒）。**実験的機能であり、本番運用では非推奨。**
- 全イベントが対応しているわけではない。`SessionStart`/`Setup` は `command`/`mcp_tool` のみ対応、`ConfigChange`/`CwdChanged`/`FileChanged`/`Notification`/`SessionEnd` などは `command`/`http`/`mcp_tool` のみ対応で `prompt`/`agent` 非対応。

> `http` / `mcp_tool` / `prompt` / `agent` の4種は今回の実地検証（Step3）では未検証（副作用・外部呼び出し・課金を伴うため、ログ仕込み用途の主軸である`command`型を優先して検証した）。上記はドキュメント記載をそのまま転記したものであり、実機確認済みなのは`command`型のみである点に注意。

---

## 主なイベント一覧

発火頻度で3つに大別される。

- **セッションに1回**: `SessionStart`, `SessionEnd`
- **ターンに1回**: `UserPromptSubmit`, `Stop`, `StopFailure`
- **エージェントループ内のツール呼び出しごと**: `PreToolUse`, `PostToolUse`

| イベント                            | 発火タイミング                                          | マッチャーの対象                                |
| ----------------------------------- | ------------------------------------------------------- | ----------------------------------------------- |
| `SessionStart`                      | セッション開始・再開時                                  | 起動理由 (`startup`/`resume`/`clear`/`compact`) |
| `Setup`                             | `--init-only` や `-p --init`/`--maintenance` 実行時のみ | `init`/`maintenance`                            |
| `UserPromptSubmit`                  | プロンプト送信直後、Claudeが処理する前                  | 非対応（毎回発火）                              |
| `UserPromptExpansion`               | スラッシュコマンド等がプロンプトに展開される前          | コマンド名                                      |
| `PreToolUse`                        | ツール呼び出しの実行前（ブロック可）                    | ツール名                                        |
| `PermissionRequest`                 | 権限確認ダイアログが出るとき                            | ツール名                                        |
| `PermissionDenied`                  | 自動モードの分類器がツール呼び出しを拒否したとき        | ツール名                                        |
| `PostToolUse`                       | ツール呼び出し成功後                                    | ツール名                                        |
| `PostToolUseFailure`                | ツール呼び出し失敗後                                    | ツール名                                        |
| `PostToolBatch`                     | 並列ツール呼び出しのバッチが全て解決した後              | 非対応                                          |
| `Notification`                      | Claude Codeが通知を送るとき                             | 通知種別                                        |
| `MessageDisplay`                    | アシスタントのメッセージが画面表示されている間          | 非対応                                          |
| `SubagentStart` / `SubagentStop`    | サブエージェント起動時／終了時                          | エージェントタイプ                              |
| `TaskCreated` / `TaskCompleted`     | `TaskCreate`でタスク作成時／完了マーク時                | 非対応                                          |
| `Stop`                              | Claudeの応答が完了したとき                              | 非対応                                          |
| `StopFailure`                       | APIエラーでターンが終了したとき                         | エラー種別                                      |
| `TeammateIdle`                      | agent teamのメンバーがアイドルになる直前                | 非対応                                          |
| `InstructionsLoaded`                | CLAUDE.mdや`.claude/rules/*.md`がロードされたとき       | ロード理由                                      |
| `ConfigChange`                      | 設定ファイルがセッション中に変更されたとき              | 変更元                                          |
| `CwdChanged`                        | 作業ディレクトリが変わったとき（`cd`実行時など）        | 非対応                                          |
| `FileChanged`                       | 監視対象ファイルがディスク上で変更されたとき            | 監視するファイル名（後述）                      |
| `WorktreeCreate` / `WorktreeRemove` | worktree作成時／削除時                                  | 非対応                                          |
| `PreCompact` / `PostCompact`        | コンテキスト圧縮の前後                                  | 何が圧縮をトリガーしたか                        |
| `Elicitation` / `ElicitationResult` | MCPサーバーがユーザー入力を要求したとき／その応答後     | MCPサーバー名                                   |
| `SessionEnd`                        | セッション終了時                                        | 終了理由                                        |

> 実地検証では `PreToolUse` / `PostToolUse` のみ実際に発火させて確認した（ログ仕込み用途で最も使う2イベントのため）。他イベントの発火タイミングはドキュメント記載をそのまま転記している。

---

## マッチャーの評価ルール

`matcher` の値に含まれる文字種によって評価方法が変わる。

| matcherの値                            | 評価方法                                       |
| -------------------------------------- | ---------------------------------------------- |
| `"*"` / `""` / 省略                    | 全てにマッチ                                   |
| 英数字・`_`・`-`・空白・`,`・`\|` のみ | 完全一致（`\|`または`,`区切りでリストも可）    |
| それ以外の文字を含む                   | JavaScriptの正規表現として評価（アンカーなし） |

⚠️ **落とし穴**:

- 正規表現扱いになる場合、`Edit.*` は `Edit` にも `NotebookEdit` にもマッチする。完全一致させたいなら `^Edit$` のようにアンカーで囲む必要がある。
- `code-reviewer` のようなハイフン付き名前は、Claude Code v2.1.195以前では正規表現として評価され、`senior-code-reviewer` にも意図せずマッチしてしまう（`^code-reviewer$` で回避）。
  - > **実地検証**: この項目はサブエージェント起動を伴う検証コストが高い（実APIコールが発生する）ため、今回は独立して再現確認していない。Step1で確認済みのこの環境のバージョンはv2.1.215で、記載されている修正対象バージョン（v2.1.195以前）より新しいため、再現しない可能性が高いという推測に留める。
- `FileChanged` と `StopFailure` は完全一致の文字種セットが狭く（英数字・`_`・`|`のみ）、ハイフンやカンマを含む値は正規表現扱いになる。区切り文字も`|`のみで`,`は使えない。
- `UserPromptSubmit`, `PostToolBatch`, `Stop`, `TeammateIdle`, `TaskCreated`, `TaskCompleted`, `WorktreeCreate`, `WorktreeRemove`, `MessageDisplay`, `CwdChanged` は**マッチャー非対応**。これらに`matcher`を書いても**エラーにならず黙って無視される**。
- MCPツールをマッチさせる場合、`mcp__memory` のような「サーバー名のみ」の指定はそのサーバーの全ツールにマッチ**しない**（完全一致としてどのツール名とも一致しない）。`mcp__memory__.*` のように `.*` を付ける必要がある。

## `if` フィールドによる絞り込み（ツールイベント限定）

`matcher` はハンドラーグループ単位の絞り込みだが、個々のハンドラーに `if` を付けると[パーミッションルール構文](https://code.claude.com/docs/en/permissions)でツール名＋引数を細かくフィルタできる（例: `"Bash(git *)"`）。

⚠️ **落とし穴**:

- `if` は **`PreToolUse`, `PostToolUse`, `PostToolUseFailure`, `PermissionRequest`, `PermissionDenied` の5イベントでしか評価されない**。他のイベントに `if` を設定するとそのハンドラーは一切発火しなくなる。
- `&&` や `||` のような複合条件は書けない。1つの`if`につき1ルールのみ。複数条件が必要なら別々のハンドラーに分ける。
- Bashコマンドの`if`判定はベストエフォート。`$()` やバッククォート内、`&&`で連結したサブコマンドも展開してチェックされるが、パースできない場合は**フェイルオープン**（＝チェックをスキップしてフックを実行してしまう）。ハードな許可/拒否には使わず、パーミッションシステム（allow/denyルール）を使うこと。
- `Bash(git push *)` のようにコマンド名以上を指定したパターンは、`$()` やバッククォート、`$VAR`を含むコマンドに対しては（中身を検査できなくても）とりあえずフックを実行してしまう。

---

## 入出力と制御

### Exit codeの意味

| Exit code | 意味                                                                                                                            |
| --------- | ------------------------------------------------------------------------------------------------------------------------------- |
| `0`       | 成功。stdoutのJSONがパースされ処理される                                                                                        |
| `2`       | ブロッキングエラー。stderrがClaudeへのフィードバックになる（**stdoutのJSONは無視される**）                                      |
| それ以外  | ほとんどのイベントで「ブロックしないエラー」。処理は継続され、トランスクリプトに`<hook name> hook error`と最初の1行が表示される |

> **実地検証**（`PreToolUse` + `Glob`マッチャーで3パターンを個別に確認）:
>
> - `exit 2` + stderr出力 → ツール呼び出しがブロックされ、`PreToolUse:Glob hook error: [<command>]: <stderrの内容>` がそのままアシスタント側へのエラーとして返ってきた。ドキュメント記載通り。
> - `exit 0` + `{"hookSpecificOutput":{"permissionDecision":"deny","permissionDecisionReason":"..."}}` → 同様にブロックされたが、**`hook error` というプレフィックスは付かず、`permissionDecisionReason` の文言だけがそのままエラーとして返ってきた**。exit 2（フック自体のエラー扱い）と exit 0 + deny（正常な判断としてのブロック）は表示上区別できる。
> - `exit 1` + stderr出力 → ブロックされず、ツール呼び出しは正常に完了した。「exit 1は失敗として扱われない」というドキュメント記載を確認。

⚠️ **落とし穴**:

- **exit code 1は「失敗」として扱われない**。Unix的には1は失敗コードだが、Claude Codeでは非ブロッキングエラー扱いで処理が継続してしまう（上記実地検証で確認済み）。ポリシーを強制したいなら必ず **`exit 2`** を使うこと。唯一の例外は `WorktreeCreate` で、ここだけは0以外の全コードでworktree作成が中止される。
- exit 2とJSON出力は**併用不可**。exit 2で終了すると、stdoutに書いたJSONは丸ごと無視される。構造化制御をしたいなら exit 0 + JSON、ブロックだけしたいなら exit 2 + stderr、のどちらかに統一する。
- ブロック可能かどうかはイベントごとに異なる。`SessionStart`, `Setup`, `Notification`, `SubagentStart`, `SessionEnd`, `CwdChanged`, `FileChanged`, `PostCompact`, `WorktreeRemove`, `InstructionsLoaded`, `StopFailure` などは**ブロック不可**で、exit 2でもユーザーへの表示のみに留まる。

### JSON出力

- 共通フィールド: `continue`（falseで全処理停止）, `stopReason`, `suppressOutput`, `systemMessage`, `terminalSequence`。
- イベントごとにデシジョンの表現方法が異なるので注意（詳細は下表）。

| イベント群                                                     | デシジョンの持ち方                                                                                                                       |
| -------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| `UserPromptSubmit`, `PostToolUse`, `Stop`, `SubagentStop` など | トップレベルの `decision: "block"` + `reason`                                                                                            |
| `PreToolUse`                                                   | `hookSpecificOutput.permissionDecision`（`allow`/`deny`/`ask`/`defer`）+ `permissionDecisionReason`。**古い`decision`/`reason`は非推奨** |
| `PermissionRequest`                                            | `hookSpecificOutput.decision.behavior`（`allow`/`deny`）                                                                                 |
| `PermissionDenied`                                             | `hookSpecificOutput.retry: true`                                                                                                         |
| `MessageDisplay`                                               | `hookSpecificOutput.displayContent`（画面表示のみ書き換え、Claude/トランスクリプトには影響しない）                                       |

⚠️ **落とし穴**:

- フックの出力文字列（`additionalContext`, `systemMessage`, プレーンstdoutなど）は**10,000文字で切り詰められる**。超過分はファイルに保存されプレビュー＋パスに置き換わる。
- 複数の`PreToolUse`フックが異なる`permissionDecision`を返した場合、優先順位は **`deny` > `defer` > `ask` > `allow`**。
- 複数の`PreToolUse`フックが`updatedInput`で引数を書き換えようとした場合、**並列実行のため最後に完了したものが勝つ**（非決定的）。同じツールの入力を複数フックで書き換えるのは避ける。
- フックが`"allow"`を返しても、設定の**denyルールは常に優先**される（拒否リストを上書きすることはできない）。逆にaskルールがあればユーザーには確認が表示される。つまりフックは制限を「強める」ことはできても「緩める」ことはできない。
- `bypassPermissions`へのモード変更は、セッションがそもそもbypassモードを許可されている場合のみ有効（`--dangerously-skip-permissions`等）。それ以外では無視され、`defaultMode`としても永続化されない。

### `PostToolUse`は取り消せない

ツールは既に実行済みなので、`PostToolUse`フックで結果をブロック/取り消すことはできない（`updatedToolOutput`で結果を差し替えることはできるが、副作用自体は元に戻らない）。

### `Stop`フックが8回で強制解除される

`Stop`フックが**8回連続でブロック**すると、Claude Codeは強制的に停止させる（無限ループ防止）。入力の `stop_hook_active` フィールドが`true`のときは既に継続中であることを示すので、これをチェックして早期`exit 0`しないと簡単に上限に達してしまう。上限は環境変数 `CLAUDE_CODE_STOP_HOOK_BLOCK_CAP` で変更可能。

### `PreToolUse`は`@`参照では発火しない

プロンプト内で`@`によりファイル内容を直接埋め込んだ場合、これはツール呼び出しを経由しないため`PreToolUse`（`Read`にマッチさせても）は発火しない。特定パスを読ませたくない場合はパーミッションの`Read`拒否ルールを使う。

---

## Windows特有の落とし穴

- **exec form**（`args`指定あり）では`command`は実ファイル（`.exe`など）である必要がある。npm/npx/eslintなどが`node_modules/.bin`に置く`.cmd`/`.bat`シムは実行ファイルではないため、exec formでは起動できない。`"command": "node", "args": ["path/to/eslint.js"]`のように直接スクリプトを叩くか、`.cmd`/`.bat`を呼びたいならshell formを使う。
  - > **実地検証で相違を確認**: `"command": "npm", "args": ["--version"]`（exec form）を`PreToolUse`+`Glob`マッチャーで実際に試したところ、**失敗せず成功した**。`--debug-file`の出力で `Hook output does not start with {, treating as plain text` に続いて `Hook PreToolUse:Glob (PreToolUse) success:` の後にnpmのバージョン文字列（`11.2.0`）がそのまま出力されているのを確認した。少なくともこの環境（Claude Code v2.1.215、同梱Node.js）では`.cmd`シムの直接起動が失敗しない。Node.jsが2024年のセキュリティ修正以降、`.cmd`/`.bat`拡張子のコマンドをspawn時に自動的に`cmd.exe`でラップするようになった影響と推測されるが断定はできない。**ドキュメント記載のこの制約は古い/Node.jsバージョン依存の可能性がある**ため、「execFormで`.cmd`/`.bat`が動かない」という前提で設計を諦める前に、まず実際に試してみる価値がある。
- `"shell": "powershell"` を指定した場合、`${CLAUDE_PROJECT_DIR}` はv2.1.198以降 `${env:NAME}` 形式に書き換えられ、ダブルクォート文字列内でのみ展開される（**シングルクォート文字列内では展開されない**）。
  - > **実地検証で完全に再現を確認**。同一コマンド内で4パターンを同時テストした:
    - 二重引用符内 `"${CLAUDE_PROJECT_DIR}"` → `C:\CodeRoot\AI`（展開成功）
    - 単一引用符内 `'${CLAUDE_PROJECT_DIR}'` → `${env:CLAUDE_PROJECT_DIR}`（リテラルのまま。Claude Code側でのテキスト置換は行われるが、PowerShellの単一引用符内では変数展開されないため）
    - `"$env:CLAUDE_PROJECT_DIR"`（正しい書き方）→ `C:\CodeRoot\AI`（展開成功）
    - `"$CLAUDE_PROJECT_DIR"`（`$env:`なしの裸の変数）→ 空文字列（未定義のローカル変数として`$null`扱い）
- PowerShellフックで裸の `$CLAUDE_PROJECT_DIR`（`$env:`なし）と書くと、未定義のローカル変数として`$null`に解決されてしまう。必ず `$env:CLAUDE_PROJECT_DIR` の形式を使うこと。
  - > **実地検証によるボーナスの発見**: 裸の`$CLAUDE_PROJECT_DIR`を検知すると、Claude Code自身がデバッグログに `[WARN] PowerShell hook command references $CLAUDE_PROJECT_DIR, which PowerShell reads as an undefined variable ($null). Use $env:CLAUDE_PROJECT_DIR or ${CLAUDE_PROJECT_DIR} instead.` という具体的な警告を出すことを確認した。ドキュメントには記載がないが、`--debug-file`を見ればこの種の間違いに気付ける。

## シェルプロファイルが原因のJSONパースエラー

shell form（`args`省略）のコマンドフックは `sh -c` やGit Bashを経由するが、`BASH_ENV`が`~/.bashrc`等を指している環境では、プロファイル内の無条件`echo`が標準出力に混ざり込み、フックが出力した有効なJSONの前に余計なテキストが挿入されて**JSONパースが失敗する**。シェルプロファイル内のechoは`[[ $- == *i* ]]`（対話シェル判定）で囲んでガードすること。

> 今回の実地検証環境では`BASH_ENV`によるプロファイル汚染は再現しなかった（shell formのPythonスクリプト呼び出しでJSONパースエラーは発生しなかった）。ただし意図的にこの状況を再現する検証（`~/.bashrc`に無条件echoを仕込む等）は行っていないため、ドキュメント記載の落とし穴自体は否定されない。

## async（バックグラウンド）フックの制約

- `async: true` は `type: "command"` のみ対応。prompt/agentフックは非対応。
- 非同期フックは**ツール呼び出しをブロックしたりデシジョンを返したりできない**。完了時点で対象のアクションは既に終わっている。
- 完了後の`additionalContext`は**次の会話ターンで**Claudeに届く（セッションがアイドル中なら次のユーザー入力を待つ。`asyncRewake: true` + exit code 2 の場合のみアイドル中でも即座に起こされる）。
- 同一フックが複数回発火しても重複排除されず、毎回別プロセスが生成される。

> `async`は今回の実地検証では未検証（Step3の検証観点に含まれておらず、副作用の後片付けが複雑になるため見送った）。上記はドキュメント記載をそのまま転記している。

## セキュリティ上の注意

- **コマンドフックはユーザーの実行権限をフルで持つ**。ファイルの読み書き・削除など、ユーザーができることは全てフックからも可能。設定を追加する前に必ず内容をレビューする。
- ベストプラクティス: 入力を信用せず検証する／シェル変数は必ず`"$VAR"`のようにクォートする／パストラバーサル（`..`）を弾く／スクリプトパスは絶対パス（`${CLAUDE_PROJECT_DIR}`等）で指定する／`.env`や`.git/`など機密ファイルへのアクセスを避ける。
- `disableAllHooks: true` はユーザー/プロジェクト/ローカル設定のフックのみを無効化する。**managed policy settingsで定義されたフックは、managed設定側で`disableAllHooks`を設定しない限り無効化できない**。

## デバッグ

> **実地検証**: 以下の3手段のうち、`--debug-file` が最も原因切り分けに有効だった。今回のStep3の全検証（exit code挙動、exec form成否、PowerShell展開結果）は全て`--debug-file`の出力で裏取りしている。

- **`claude --debug-file <path>` でデバッグログをファイルに書き出すのが最も確実**。`claude -p "..." --model claude-haiku-4-5-20251001 --debug-file <path> --no-session-persistence` のような非対話1回実行にすれば、hookのstdout内容・成功/失敗・警告メッセージまで全てファイルに残り、後から`grep`で追える。
- `CLAUDE_CODE_DEBUG_LOG_LEVEL=verbose` を`--debug-file`と併用すると、**matcher評価の過程**が追加で見える（実地検証で確認した実際のログ行）:
  ```
  [VERBOSE] executePreToolHooks called for tool: Glob
  [VERBOSE] Getting matching hook commands for PreToolUse with query: Glob
  [VERBOSE] Found 1 hook matchers in settings
  [VERBOSE] Matched 1 unique hooks for query "Glob" (1 before deduplication)
  ```
  意図したhookがマッチしていない／別のhookが誤って多重発火している、といった切り分けにはverboseの指定がほぼ必須。
  - ⚠️ **紛らわしいログ行に注意**: `[DEBUG] Hooks: Found 0 total hooks in registry` という行は、実際にhookが発火していても常に`0`と表示される（settings.jsonベースのhookとは別のレジストリを指しているとみられる）。**この行だけを見てhookが未登録と判断しないこと**。
- `Ctrl+O` でトランスクリプト表示に切り替えると、各フックの発火結果（成功は無表示、ブロッキングエラーはstderr、非ブロッキングエラーは`<hook name> hook error`通知）が確認できる。
  - > この手段は対話UIが前提のため、今回のツール呼び出し経由の非対話実行環境からは直接検証できなかった。ドキュメント記載をそのまま採用し、未検証である旨をここに明記する。
- 手元でのテストは `echo '{"tool_name":"Bash","tool_input":{"command":"ls"}}' | ./my-hook.sh` のように標準入力にサンプルJSONを流し込んで `$?` を確認するのが手早い。

---

## 実際に動作確認済みのログ仕込みテンプレート

以下は全てStep3で`.claude/settings.local.json`に実際に仕込み、発火・出力を確認済みのテンプレート。方針は一貫して「別ファイルのPythonスクリプト + exec form（`command: "python"` 固定 + `args`にスクリプトパスと引数を配列で渡す）」。インラインの`python -c`やshell form文字列コマンド（シェルスクリプト含む）は使わない — exec formならJSON入力がstdin経由で渡り、`args`もシェルを介さず配列のままプロセスに渡るため、シェルのクォート/エスケープに起因する事故が構造的に起きない（出力に`'`・`"`を含むケースでも問題なく動作することを実地検証済み）。

### 1. 全Bashコマンドをjsonlに記録する（`PostToolUse`）

ログ追記スクリプト（例: `%USERPROFILE%\.claude\hook-scripts\log_stdin.py`）:

```python
import sys

target = sys.argv[1]
data = sys.stdin.read()
with open(target, "a", encoding="utf-8") as f:
    f.write(data + "\n")
```

`.claude/settings.json` 側の設定（exec form: `args`にスクリプトパス以下を配列で渡し、シェルを一切介さない）:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python",
            "args": [
              "${CLAUDE_PROJECT_DIR}/.claude/hook-scripts/log_stdin.py",
              "${CLAUDE_PROJECT_DIR}/.claude/logs/bash-history.jsonl"
            ]
          }
        ]
      }
    ]
  }
}
```

実際に発火したstdinの中身（実地検証で得た実例。フィールド構成の参考に）:

```json
{
  "session_id": "...",
  "transcript_path": "...",
  "cwd": "...",
  "prompt_id": "...",
  "permission_mode": "auto",
  "effort": { "level": "high" },
  "hook_event_name": "PostToolUse",
  "tool_name": "Bash",
  "tool_input": { "command": "...", "description": "..." },
  "tool_response": {
    "stdout": "...",
    "stderr": "",
    "interrupted": false,
    "isImage": false,
    "noOutputExpected": false
  },
  "tool_use_id": "...",
  "duration_ms": 1148
}
```

`tool_name`/`tool_input`/`tool_response`/`session_id`/`transcript_path`/`cwd`はドキュメント記載通り。加えて`prompt_id`, `permission_mode`, `effort`, `tool_use_id`, `duration_ms`も実際には渡ってくる（ドキュメント未記載）。

### 2. 特定ツール（Edit/Write）の変更内容だけを記録する（`PostToolUse` + matcherで絞り込み）

上記と同じ`log_stdin.py`を流用し、`matcher`だけ変える。

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "python",
            "args": [
              "${CLAUDE_PROJECT_DIR}/.claude/hook-scripts/log_stdin.py",
              "${CLAUDE_PROJECT_DIR}/.claude/logs/file-edits.jsonl"
            ]
          }
        ]
      }
    ]
  }
}
```

`matcher`の文字種は英数字・`|`のみなので完全一致リストとして評価される（正規表現扱いにはならない）。`tool_input`に変更後の内容（`Write`なら`content`、`Edit`なら`old_string`/`new_string`）がそのまま入っているので、追記するだけで差分ログになる。

### 3. 危険なコマンドをブロックしつつ理由を記録する（`PreToolUse` + exit 2）

判定スクリプト（例: `deny_check.py`。stdinのJSONを見て条件次第でexit 2）:

```python
import json
import sys

payload = json.load(sys.stdin)
command = payload.get("tool_input", {}).get("command", "")

if "rm -rf" in command:
    sys.stderr.write("rm -rf を含むコマンドはこのプロジェクトでは禁止されています\n")
    sys.exit(2)

sys.exit(0)
```

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python",
            "args": ["${CLAUDE_PROJECT_DIR}/.claude/hook-scripts/deny_check.py"]
          }
        ]
      }
    ]
  }
}
```

実地検証で確認した通り、`exit 2` + stderrの文言はそのまま `PreToolUse:Bash hook error: [...]: <stderrの内容>` としてアシスタント側に返る。**`exit 1`ではブロックされない**（非ブロッキングエラー扱いで処理が継続してしまう）ので、ブロックが目的なら必ず`exit 2`を使うこと。exit 0 + `{"hookSpecificOutput":{"permissionDecision":"deny","permissionDecisionReason":"..."}}`でも同様にブロックできるが、こちらは`hook error`プレフィックスが付かず理由文だけが返る（実地検証で確認済み）。
