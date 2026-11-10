# フック機能の使い方

フックは、Claude Codeのライフサイクル上の特定のタイミングで自動実行される、ユーザー定義のシェルコマンド・HTTPエンドポイント・LLMプロンプトのこと。`.claude/settings.json` などの設定ファイルに記述する。

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
- [デバッグ](#デバッグ)

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
- `ok: false`のとき何が起きるかはイベントごとに異なる。`Stop`/`SubagentStop`は`reason`がClaudeに返りそのまま続行。`PreToolUse`/`PostToolUse`はv2.1.210以降デフォルトでターンが終了し`reason`が警告として表示されるだけになった（それ以前はClaudeへのツールエラーとして返り続行していた）。続行させたい場合は`continueOnBlock: true`を設定する（`PostToolBatch`/`UserPromptSubmit`/`UserPromptExpansion`は`continueOnBlock`があっても常にターン終了）。

---

## 主なイベント一覧

発火頻度で3つに大別される。

- **セッションに1回**: `SessionStart`, `SessionEnd`
- **ターンに1回**: `UserPromptSubmit`, `Stop`, `StopFailure`
- **エージェントループ内のツール呼び出しごと**: `PreToolUse`, `PostToolUse`

| イベント                            | 発火タイミング                                                                                            | マッチャーの対象                                                                        |
| ----------------------------------- | --------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| `SessionStart`                      | セッション開始・再開時                                                                                    | 起動理由 (`startup`/`resume`/`clear`/`compact`)                                         |
| `Setup`                             | `--init-only` や `-p --init`/`--maintenance` 実行時のみ                                                   | `init`/`maintenance`                                                                    |
| `UserPromptSubmit`                  | プロンプト送信直後、Claudeが処理する前                                                                    | 非対応（毎回発火）                                                                      |
| `UserPromptExpansion`               | スラッシュコマンド等がプロンプトに展開される前                                                            | コマンド名                                                                              |
| `PreToolUse`                        | ツール呼び出しの実行前（ブロック可）                                                                      | ツール名                                                                                |
| `PermissionRequest`                 | 権限確認ダイアログが出るとき                                                                              | ツール名                                                                                |
| `PermissionDenied`                  | 自動モードの分類器がツール呼び出しを拒否したとき                                                          | ツール名                                                                                |
| `PostToolUse`                       | ツール呼び出し成功後                                                                                      | ツール名                                                                                |
| `PostToolUseFailure`                | ツール呼び出し失敗後                                                                                      | ツール名                                                                                |
| `PostToolBatch`                     | 並列ツール呼び出しのバッチが全て解決した後                                                                | 非対応                                                                                  |
| `Notification`                      | Claude Codeが通知を送るとき                                                                               | 通知種別                                                                                |
| `MessageDisplay`                    | アシスタントのメッセージが画面表示されている間                                                            | 非対応                                                                                  |
| `SubagentStart` / `SubagentStop`    | サブエージェント起動時／終了時                                                                            | エージェントタイプ                                                                      |
| `TaskCreated` / `TaskCompleted`     | `TaskCreate`でタスク作成時／完了マーク時                                                                  | 非対応                                                                                  |
| `Stop`                              | Claudeの応答が完了したとき                                                                                | 非対応                                                                                  |
| `StopFailure`                       | APIエラーでターンが終了したとき                                                                           | エラー種別                                                                              |
| `TeammateIdle`                      | agent teamのメンバーがアイドルになる直前                                                                  | 非対応                                                                                  |
| `InstructionsLoaded`                | CLAUDE.mdや`.claude/rules/*.md`がロードされたとき                                                         | ロード理由                                                                              |
| `ConfigChange`                      | 設定ファイルがセッション中に変更されたとき                                                                | 変更元                                                                                  |
| `CwdChanged`                        | 作業ディレクトリが変わったとき（`cd`実行時など）                                                          | 非対応                                                                                  |
| `FileChanged`                       | 監視対象ファイルがディスク上で変更されたとき                                                              | 監視するファイル名（後述）                                                              |
| `WorktreeCreate` / `WorktreeRemove` | worktree作成時／削除時                                                                                    | 非対応                                                                                  |
| `DirectoryAdded`                    | `/add-dir`またはSDKの`register_repo_root`でセッション中に作業ディレクトリが追加されたとき（v2.1.219以降） | 不明（要検証。公式リファレンスの本表に相当する記載が未確認、changelogのみで存在を確認） |
| `PreCompact` / `PostCompact`        | コンテキスト圧縮の前後                                                                                    | 何が圧縮をトリガーしたか                                                                |
| `Elicitation` / `ElicitationResult` | MCPサーバーがユーザー入力を要求したとき／その応答後                                                       | MCPサーバー名                                                                           |
| `SessionEnd`                        | セッション終了時                                                                                          | 終了理由                                                                                |

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

⚠️ **落とし穴**:

- **exit code 1は「失敗」として扱われない**。Unix的には1は失敗コードだが、Claude Codeでは非ブロッキングエラー扱いで処理が継続してしまう。ポリシーを強制したいなら必ず **`exit 2`** を使うこと。唯一の例外は `WorktreeCreate` で、ここだけは0以外の全コードでworktree作成が中止される。
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
- `"shell": "powershell"` を指定した場合、`${CLAUDE_PROJECT_DIR}` はv2.1.198以降 `${env:NAME}` 形式に書き換えられ、ダブルクォート文字列内でのみ展開される（**シングルクォート文字列内では展開されない**）。
- PowerShellフックで裸の `$CLAUDE_PROJECT_DIR`（`$env:`なし）と書くと、未定義のローカル変数として`$null`に解決されてしまう。必ず `$env:CLAUDE_PROJECT_DIR` の形式を使うこと。

## シェルプロファイルが原因のJSONパースエラー

shell form（`args`省略）のコマンドフックは `sh -c` やGit Bashを経由するが、`BASH_ENV`が`~/.bashrc`等を指している環境では、プロファイル内の無条件`echo`が標準出力に混ざり込み、フックが出力した有効なJSONの前に余計なテキストが挿入されて**JSONパースが失敗する**。シェルプロファイル内のechoは`[[ $- == *i* ]]`（対話シェル判定）で囲んでガードすること。

## async（バックグラウンド）フックの制約

- `async: true` は `type: "command"` のみ対応。prompt/agentフックは非対応。
- 非同期フックは**ツール呼び出しをブロックしたりデシジョンを返したりできない**。完了時点で対象のアクションは既に終わっている。
- 完了後の`additionalContext`は**次の会話ターンで**Claudeに届く（セッションがアイドル中なら次のユーザー入力を待つ。`asyncRewake: true` + exit code 2 の場合のみアイドル中でも即座に起こされる）。
- 同一フックが複数回発火しても重複排除されず、毎回別プロセスが生成される。

## セキュリティ上の注意

- **コマンドフックはユーザーの実行権限をフルで持つ**。ファイルの読み書き・削除など、ユーザーができることは全てフックからも可能。設定を追加する前に必ず内容をレビューする。
- ベストプラクティス: 入力を信用せず検証する／シェル変数は必ず`"$VAR"`のようにクォートする／パストラバーサル（`..`）を弾く／スクリプトパスは絶対パス（`${CLAUDE_PROJECT_DIR}`等）で指定する／`.env`や`.git/`など機密ファイルへのアクセスを避ける。
- `disableAllHooks: true` はユーザー/プロジェクト/ローカル設定のフックのみを無効化する。**managed policy settingsで定義されたフックは、managed設定側で`disableAllHooks`を設定しない限り無効化できない**。

## デバッグ

- `Ctrl+O` でトランスクリプト表示に切り替えると、各フックの発火結果（成功は無表示、ブロッキングエラーはstderr、非ブロッキングエラーは`<hook name> hook error`通知）が確認できる。
- `claude --debug-file <path>` でデバッグログをファイルに書き出し、`tail -f`で監視するのが確実。`CLAUDE_CODE_DEBUG_LOG_LEVEL=verbose` でマッチャーの一致判定など、より詳細なログも見られる。
- 手元でのテストは `echo '{"tool_name":"Bash","tool_input":{"command":"ls"}}' | ./my-hook.sh` のように標準入力にサンプルJSONを流し込んで `$?` を確認するのが手早い。

---

#### 参考文献

- [Hooks reference](https://code.claude.com/docs/en/hooks) — フックイベントの全スキーマ、設定形式、JSON入出力形式、非同期/HTTP/MCPツールフックなどの詳細
- [Automate actions with hooks](https://code.claude.com/docs/en/hooks-guide) — クイックスタートガイドと具体的なユースケース例
