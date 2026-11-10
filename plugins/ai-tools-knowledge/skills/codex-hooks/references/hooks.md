# Codex Hooksリファレンス

Codex Hooksは、Codexのライフサイクル中の特定タイミングでスクリプトやMCPツールを実行する拡張機構。`hooks.json`または`config.toml`の`[hooks]`テーブルに記述する。

出典: https://developers.openai.com/codex/hooks （2026-08時点の内容。最新版は本ページまたは`codex-docs`スキルで確認）

## 目次

- [ランタイムの挙動](#ランタイムの挙動)
- [定義場所](#定義場所)
- [信頼レビュー（trust）](#信頼レビューtrust)
- [設定の形](#設定の形)
- [command ハンドラー](#command-ハンドラー)
- [mcp_tool ハンドラー](#mcp_tool-ハンドラー)
- [hooksをオフにする](#hooksをオフにする)
- [managed hooks（requirements.toml）](#managed-hooksrequirementstoml)
- [プラグイン同梱hooks](#プラグイン同梱hooks)
- [マッチャーパターン](#マッチャーパターン)
- [ツールカバレッジ](#ツールカバレッジ)
- [共通input/output フィールド](#共通inputoutput-フィールド)
- [大きいhook出力（spilling）](#大きいhook出力spilling)
- [バックグラウンドhooks（async）](#バックグラウンドhooksasync)
- [イベント別の詳細](#イベント別の詳細)

---

## ランタイムの挙動

- 複数ファイル・複数レイヤーでマッチしたhooksは**全て実行される**（上位レイヤーが下位レイヤーのhookを置き換えることはない）。
- 同一イベントにマッチする複数のcommand hookは**並列に起動**される。1つのhookが他のhookの起動を止めることはできない。
- 非managed（＝ユーザー/プロジェクト/プラグイン由来）のhookは、実行前に**必ずレビュー・信頼（trust）**する必要がある。

## 定義場所

Codexはアクティブなconfigレイヤーごとに以下いずれかの形式を探す。

- `hooks.json`
- `config.toml`内のインライン`[hooks]`テーブル

実務上よく使う4箇所:

- `~/.codex/hooks.json`
- `~/.codex/config.toml`
- `<repo>/.codex/hooks.json`
- `<repo>/.codex/config.toml`

補足:

- 複数のhookソースが存在する場合、Codexはマッチする全hookを読み込む。上位優先度のconfigレイヤーが下位優先度のhookを**置き換えることはない**。
- 同一レイヤー内に`hooks.json`とインライン`[hooks]`の両方があると、Codexは両方をマージした上で起動時に警告する。**1レイヤーにつきどちらか一方の表現に統一する**のが望ましい。
- プラグインもプラグインマニフェストまたはデフォルトの`hooks/hooks.json`経由でhooksを同梱できる（[プラグイン同梱hooks](#プラグイン同梱hooks)参照）。
- プロジェクトローカルhook（`<repo>/.codex/`配下）は、そのプロジェクトの`.codex/`レイヤーが**信頼済み（trusted）**の場合のみ読み込まれる。未信頼プロジェクトでも、ユーザー/システムレベルのhookは引き続き読み込まれる。

## 信頼レビュー（trust）

- Codexはhookを実行する前に、設定済みhookを列挙し、どれが実行可能かを判断する。
- 非managedなhookが実行される前に、**そのhook定義そのものをレビュー・信頼**する必要がある。Codexはhookの現在のハッシュに対して信頼を記録するため、hookが新規追加・変更されるとレビュー待ち状態になり、信頼するまでスキップされる。
- CLIで`/hooks`を使うと、hookソースの確認、新規/変更hookのレビュー、信頼、個別の非managed hookの無効化ができる。起動時にレビュー待ちのhookがあれば、Codexは`/hooks`を開くよう警告を表示する。
- system/MDM/cloud/`requirements.toml`由来の**managed hooks**はmanaged扱いとなり、ポリシーにより自動的に信頼済みとなる。ユーザーのhookブラウザから無効化することはできない。
- Codex外で既にソースを検証済みの一度きりの自動化では、`--dangerously-bypass-hook-trust`を渡すと、そのセッションに限りhook信頼の永続化を求めずに有効なhookを実行できる。

## 設定の形

設定は3階層になっている。

1. **hookイベント**（`PreToolUse`、`PostToolUse`、`PreCompact`、`SubagentStart`、`Stop`など）
2. **マッチャーグループ**（そのイベントがいつマッチするか）
3. **1つ以上のhookハンドラー**（マッチャーグループがマッチしたときに実行される）

```json
{
  "description": "Optional lifecycle hooks for this workspace.",
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup|resume",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.codex/hooks/session_start.py",
            "statusMessage": "Loading session notes",
            "additionalContextLimit": 5000
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "/usr/bin/python3 \"$(git rev-parse --show-toplevel)/.codex/hooks/pre_tool_use_policy.py\"",
            "statusMessage": "Checking Bash command"
          }
        ]
      }
    ]
  }
}
```

`config.toml`側の等価なインライン表現:

```toml
[[hooks.PreToolUse]]
matcher = "^Bash$"

[[hooks.PreToolUse.hooks]]
type = "command"
command = '/usr/bin/python3 "$(git rev-parse --show-toplevel)/.codex/hooks/pre_tool_use_policy.py"'
timeout = 30
statusMessage = "Checking Bash command"
```

補足:

- `description`は`hooks.json`のオプションのトップレベルメタデータ。どのhookが動くかには影響しない。
- `timeout`は秒単位。省略時、ほとんどのhookは`600`秒（`SessionEnd`のみ既定`1`秒・最大`3`秒）。
- `statusMessage`はオプション。
- `additionalContextLimit`は[大きいhook出力（spilling）](#大きいhook出力spilling)を参照。
- `commandWindows`はWindows専用のコマンド上書き（TOMLキーは`command_windows`または`commandWindows`）。
- `async: true`で[バックグラウンド実行](#バックグラウンドhooksasync)。
- ハンドラーの`type`は`command`と`mcp_tool`のみ実際に実行される。`prompt`/`agent`はパースされるが**実行されない**。
- コマンドはセッションの`cwd`をカレントディレクトリとして実行される。
- リポジトリローカルなhookは、`.codex/hooks/...`のような相対パスではなく、**gitルートから解決するパス**を使う方が安全（Codexがサブディレクトリから起動される場合があり、gitルート基準の方が場所が安定する）。

## command ハンドラー

上記の設定例を参照。`command`（必須）に加えて、`commandWindows`（Windows用上書き）、`timeout`、`statusMessage`、`additionalContextLimit`、`async`が使える。

## mcp_tool ハンドラー

ライフサイクルイベントから、**既に接続済みの**MCPサーバー上のツールを直接呼び出す。command hookと同じ信頼レビュー・出力コントラクトを使う。

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "mcp_tool",
            "server": "scanner",
            "tool": "scan_patch",
            "input": { "patch": "${tool_input.command}" },
            "timeout": 30,
            "statusMessage": "Scanning edited files"
          }
        ]
      }
    ]
  }
}
```

| フィールド      | 意味                                                       |
| --------------- | ---------------------------------------------------------- |
| `type`          | `mcp_tool`固定                                             |
| `server`        | 必須。既に接続済みのMCPサーバー名                          |
| `tool`          | 必須。そのサーバーが公開するツール名                       |
| `input`         | オプション。引数テンプレートのJSONオブジェクト（既定`{}`） |
| `timeout`       | オプション。実行中タイムアウト秒（既定`600`）              |
| `statusMessage` | オプション。実行中に表示するメッセージ                     |

### 引数展開

`${field.nested}`でhookイベントのドット区切りフィールドを参照できる。値全体がプレースホルダーの場合はJSON型が保持され、より大きな文字列の一部として使う場合はテキストとしてレンダリングされる。オブジェクト・配列は再帰的に展開される。

例: イベントに`{"tool_input":{"file_path":"src/main.rs","count":3}}`が含まれる場合、

```json
{
  "path": "${tool_input.file_path}",
  "count": "${tool_input.count}",
  "message": "Scanning ${tool_input.file_path}"
}
```

は次のように展開される。

```json
{ "path": "src/main.rs", "count": 3, "message": "Scanning src/main.rs" }
```

### 実行とライフサイクル

- hookは既存のMCP接続を使う。サーバーの起動・再接続は行わない。
- ツールがブロッキングなdecisionを返した場合、操作をブロックできる。エラー・サーバー未発見・ツール未発見は操作をブロック**しない**。
- MCP tool hookは同期実行される。ツール承認をリクエストしたり他のhookをトリガーしたりはしない。
- hookのタイムアウトとサーバー側タイムアウトのうち短い方が適用される。MCP elicitationの応答待ち時間はタイムアウトにカウントされない。
- `SessionStart`のhookはMCPサーバーが準備できる前に実行されることがある。その場合、セッションをブロックしない。
- `SessionEnd`はMCP tool hookに対応しない。

## hooksをオフにする

hooksは既定で有効。`config.toml`で無効化するには:

```toml
[features]
hooks = false
```

正規のフィーチャーキーは`hooks`。`codex_hooks`は非推奨エイリアスとして引き続き動作する。管理者は`requirements.toml`の`[features].hooks = false`で同様に強制無効化できる。

## managed hooks（requirements.toml）

エンタープライズ管理の`requirements.toml`は`[hooks]`配下にインラインでhookを定義できる。管理者がhook設定を強制しつつ、実際のスクリプト配布はMDM等の別手段で行いたい場合に有用。

- `allow_managed_hooks_only = true`にすると、ユーザー/プロジェクト/セッション/プラグイン由来のhookを無視し、管理者のmanaged hookのみを許可する。
- ユーザーがローカルでhooksを無効化していてもmanaged hookを強制したい場合は、`requirements.toml`側で`[features].hooks = true`を`[hooks]`と併せてピン留めする。

```toml
allow_managed_hooks_only = true

[features]
hooks = true

[hooks]
managed_dir = "/enterprise/hooks"
windows_managed_dir = 'C:\enterprise\hooks'

[[hooks.PreToolUse]]
matcher = "^Bash$"

[[hooks.PreToolUse.hooks]]
type = "command"
command = "python3 /enterprise/hooks/pre_tool_use_policy.py"
command_windows = 'py -3 C:\enterprise\hooks\pre_tool_use_policy.py'
timeout = 30
statusMessage = "Checking managed Bash command"
```

補足:

- `managed_dir`はmacOS/Linux用、`windows_managed_dir`はWindows用。
- Codex自体は`managed_dir`配下のスクリプトを配布しない。企業側のツールでインストール・更新する必要がある。
- managed hookのコマンドは、設定したmanagedディレクトリ配下の**絶対パス**を使うべき。

## プラグイン同梱hooks

プラグインが有効化されると、Codexはユーザー/プロジェクト/managed hookと並行してそのプラグインのライフサイクルhookを読み込める。

- 既定ではプラグインルート直下の`hooks/hooks.json`を探す。
- `.codex-plugin/plugin.json`の`hooks`エントリでデフォルトを上書きできる（`./`始まりの単一パス／パス配列／インラインhooksオブジェクト／インラインオブジェクト配列のいずれか）。

```json
{
  "name": "repo-policy",
  "hooks": "./hooks/hooks.json"
}
```

- マニフェストのhookパスはプラグインルート基準で解決され、**プラグインルート内に留まる必要がある**。マニフェストが`hooks`を定義していれば、既定の`hooks/hooks.json`ではなくそちらが使われる。
- プラグインのhookコマンドには以下の環境変数が渡される。
  - `PLUGIN_ROOT`（Codex拡張）: インストール済みプラグインルートを指す
  - `PLUGIN_DATA`（Codex拡張）: プラグインの書き込み可能データディレクトリを指す
  - 互換性のため`CLAUDE_PLUGIN_ROOT`/`CLAUDE_PLUGIN_DATA`も同時に設定される
- プラグインhookは他のhookと同じイベントスキーマを使う。プラグインのインストール・有効化だけでは自動的に信頼されない。現在のhook定義をレビュー・信頼するまでスキップされる。

## マッチャーパターン

`matcher`フィールドはhookの発火可否を絞り込む**正規表現文字列**。`"*"`・`""`・省略はそのイベントの全発火にマッチする。

現時点で`matcher`が意味を持つイベントは以下のみ。

| イベント            | `matcher`が絞り込む対象 | 補足                                      |
| ------------------- | ----------------------- | ----------------------------------------- |
| `PermissionRequest` | ツール名                | `Bash`・`apply_patch`※・MCPツール名に対応 |
| `PostToolUse`       | ツール名                | [ツールカバレッジ](#ツールカバレッジ)参照 |
| `PostCompact`       | 圧縮のトリガー          | `manual`または`auto`                      |
| `PreCompact`        | 圧縮のトリガー          | `manual`または`auto`                      |
| `PreToolUse`        | ツール名                | [ツールカバレッジ](#ツールカバレッジ)参照 |
| `SessionEnd`        | 終了理由                | 現状は常に`other`                         |
| `SessionStart`      | 起動元                  | `startup`・`resume`・`clear`・`compact`   |
| `SubagentStart`     | サブエージェント種別    | 起動するサブエージェントに依存            |
| `SubagentStop`      | サブエージェント種別    | 終了するサブエージェントに依存            |
| `UserPromptSubmit`  | 非対応                  | `matcher`を設定しても無視される           |
| `Stop`              | 非対応                  | `matcher`を設定しても無視される           |

※`apply_patch`では、`matcher`の値として`Edit`または`Write`も使える。

例: `Bash` / `^apply_patch$` / `Edit|Write` / `mcp__filesystem__read_file` / `mcp__filesystem__.*` / `startup|resume|clear|compact` / `manual|auto`

## ツールカバレッジ

`PreToolUse`/`PostToolUse`はシェル・MCP呼び出し以外の多くのローカル関数ツールも観測できる。ほとんどのローカル関数ツールは同じhookパスを通るため、ツール名でマッチさせ、JSON引数を検査し、`PreToolUse`ならブロック・書き換えができる。

| ツール経路                      | `PreToolUse` | `PostToolUse` | 備考                                                                                                       |
| ------------------------------- | ------------ | ------------- | ---------------------------------------------------------------------------------------------------------- |
| シェルコマンド                  | 対応         | 対応          | `Bash`としてマッチ                                                                                         |
| unified exec（`exec_command`）  | 対応         | 対応          | `Bash`としてマッチ。後続の`write_stdin`ポーリングが、完了時に元コマンドの`PostToolUse`を配送することがある |
| `apply_patch`                   | 対応         | 対応          | `apply_patch`・`Edit`・`Write`のいずれでもマッチ可能                                                       |
| MCPツール                       | 対応         | 対応          | `mcp__filesystem__read_file`のようなMCPツール名でマッチ                                                    |
| その他のローカル関数ツール      | 対応         | 対応          | `update_plan`のような関数ツール名でマッチ。`spawn_agent`は`Agent`にもマッチする                            |
| hosted tools（`WebSearch`など） | 非対応       | 非対応        | ローカル関数ツールのhookパスを通らない                                                                     |

補足: `write_stdin`は既存のunified execセッションへの入力伝送であり、既に`PreToolUse`を通過済みのコマンドへの送信・ポーリング時に`PreToolUse`を再実行することはない。一部の特殊なツール経路はデフォルトのhookパスを迂回できるため、ツールhookは**完全な強制境界ではなく有用なガードレール**として扱うこと。

## 共通input/output フィールド

すべてのcommand hookは`stdin`で1つのJSONオブジェクトを受け取る。

| フィールド        | 型               | 意味                                                                  |
| ----------------- | ---------------- | --------------------------------------------------------------------- |
| `session_id`      | `string`         | 現在のCodexセッションid。サブエージェントのhookは親セッションidを使う |
| `transcript_path` | `string \| null` | セッションのトランスクリプトファイルパス（あれば）                    |
| `cwd`             | `string`         | セッションの作業ディレクトリ                                          |
| `hook_event_name` | `string`         | 現在のhookイベント名                                                  |
| `model`           | `string`         | Codex拡張。有効なモデルslug                                           |

ターンスコープのhookは、イベント固有フィールドの中にCodex拡張として`turn_id`を持つ。

`SessionStart`・`PreToolUse`・`PermissionRequest`・`PostToolUse`・`UserPromptSubmit`・`SubagentStart`・`SubagentStop`・`Stop`は`permission_mode`（`default`・`acceptEdits`・`plan`・`dontAsk`・`bypassPermissions`のいずれか）も持つ。

`transcript_path`は利便性のためのパスであり、トランスクリプト形式自体はhookにとって安定インターフェースではなく将来変わり得る。正確なワイヤーフォーマットが必要な場合はGenerated schemas（本ファイル末尾のリンク）を参照。

### 共通output フィールド

`SessionStart`・`PreCompact`・`PostCompact`・`UserPromptSubmit`・`SubagentStop`・`Stop`は次の共通JSONフィールドに対応する。`SubagentStart`も`systemMessage`とhook固有contextについては同じ形を受け付けるが、`continue: false`はサブエージェントを止めない。

```json
{
  "continue": true,
  "stopReason": "optional",
  "systemMessage": "optional",
  "suppressOutput": false
}
```

| フィールド       | 効果                                             |
| ---------------- | ------------------------------------------------ |
| `continue`       | `false`でそのhook実行を停止扱いにする            |
| `stopReason`     | 停止理由として記録される                         |
| `systemMessage`  | UIまたはイベントストリームに警告として表示される |
| `suppressOutput` | パースされるが未実装                             |

出力なしでexit `0`した場合は成功として扱われ、Codexは処理を続行する。

`PreToolUse`と`PermissionRequest`は`systemMessage`に対応するが、`continue`・`stopReason`・`suppressOutput`はこの2イベントでは**現状未対応**。これらのフィールドを返すと、Codexはそのhook実行を失敗としてエラー報告し、ツール呼び出し自体は続行する。

`PostToolUse`は`systemMessage`・`continue: false`・`stopReason`に対応する。`suppressOutput`はパースされるがこのイベントでは未対応。

## 大きいhook出力（spilling）

Codexは既定で、モデルに見えるhook出力メッセージ1件あたり約2,500トークンに制限する。それを超えると、Codexは全文を`<temp_dir>/hook_outputs/<session_id>/<uuid>.txt`に保存し、モデルには先頭・末尾のプレビューと保存先パスだけを渡す（この挙動を**spilling**と呼ぶ）。ファイルへの書き込みに失敗した場合でも、モデルには切り詰めたプレビューが渡される。

- `additionalContext`を返すcommand hookは、ハンドラーに`additionalContextLimit`を設定することでこの閾値（概算トークン数）をカスタマイズできる。省略時は既定の`2500`。正の整数で別の閾値を、`0`でハンドラーの完全なadditional contextをそのままモデルに渡す。
- `0`を指定するのは、hook側で厳格な出力上限を強制している場合以外は避けること。さもないと1つのhookがコンテキストウィンドウ全体を消費し得る。
- この設定は`additionalContext`にのみ適用される。ツールフィードバックや継続プロンプトは既定の上限のまま。
- oversizedな出力はディスクに書き出され得るため、hook出力にシークレットや機微情報を含めないこと。

## バックグラウンドhooks（async）

既定では、Codexはcommand hookの完了を待ってから、それをトリガーした操作を続行する。`async: true`を設定すると、Codexが処理を続けながらcommand hookをバックグラウンドで実行できる。

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.codex/hooks/post_tool_use.py",
            "async": true,
            "timeout": 120
          }
        ]
      }
    ]
  }
}
```

- バックグラウンドhookは同期hookと同じinput・matcher・信頼レビュー・timeout・[spilling](#大きいhook出力spilling)を使う。`timeout`は秒単位、既定`600`。
- バックグラウンドhookが完了すると、Codexは会話中の次に安全なタイミングで対応する情報出力を配送する。ターンが進行中なら現在のモデルリクエスト・ツール呼び出しの完了を待ってから次のモデルリクエストに反映し、ターンが無ければ次のユーザーターンまで待つ（バックグラウンドhookの完了自体は新しいターンを開始しない）。
- 出力形式は同期hookと同じイベント固有JSON。`additionalContext`はモデルのコンテキストに追加され、`systemMessage`は警告として表示される。
- **バックグラウンドhookは操作をブロック・承認・書き換え・制御できない**。ツールポリシー・権限判断・プロンプト拒否・ターン継続の制御には同期hookを使うこと。

制約:

- Codexは1セッションあたり最大8個のバックグラウンドhookを並行実行する。それを超える分は実行中のhookが終わるまで待機する。
- 各マッチした呼び出しは独立して実行され、開始順とは異なる順序で完了し得る。
- セッションが終了すると、Codexは未完了のバックグラウンドhookをキャンセルし、配送されていない出力は破棄する。
- `SessionEnd`のhookは`async`指定の有無にかかわらず**常に同期実行**される。

## イベント別の詳細

### SessionStart

`matcher`は`source`に適用される。

追加フィールド: `source`（`string`）— `startup`・`resume`・`clear`・`compact`のいずれか。

- `stdout`のプレーンテキストは追加のdeveloper contextとして扱われる。
- `stdout`のJSONは[共通outputフィールド](#共通output-フィールド)に加え、次のhook固有形を使える。

```json
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "Load the workspace conventions before editing."
  }
}
```

ルートセッションのcompact後、`source: "compact"`にマッチする`SessionStart`hookは次のモデルリクエスト前に実行される。ターン途中で自動compactionが起きた場合も同様で、Codexはそのhookのadditional contextを次のユーザーターンを待たずに直後の継続に反映する。hookが`continue: false`を返すと、Codexは次のモデルリクエストを送らずにターンを終了する。

### SessionEnd

会話をアーカイブ・削除したとき、Codexが通常終了したとき、または会話がどのクライアントにも接続されないまま30分アイドルになったときに、メインスレッドに対して実行される（サブエージェントでは実行されない）。会話を切り替えるだけ、あるいは`thread/unsubscribe`を呼ぶだけではすぐには`SessionEnd`は走らない。

追加フィールド: `reason`（`string`）— 現状は常に`other`。`matcher`は省略するか`other`を指定する。

```json
{
  "session_id": "thr_123",
  "transcript_path": "/workspace/.codex/rollout.jsonl",
  "cwd": "/workspace",
  "hook_event_name": "SessionEnd",
  "reason": "other"
}
```

`SessionEnd`のhookは`async`設定にかかわらず常に同期実行される。出力はアドバイザリであり、Codexの挙動を左右したりスレッドを開いたままにしたりはしない。コマンドがタイムアウトまたはエラー終了した場合、Codexはhook失敗として報告する。

### SubagentStart

`matcher`は`agent_type`に適用される。

追加フィールド: `turn_id`（Codex拡張）、`agent_id`、`agent_type`、`permission_mode`。

`stdout`のプレーンテキストはサブエージェント向けの追加developer contextになる。JSON出力は`systemMessage`と次のhook固有形に対応する。

```json
{
  "hookSpecificOutput": {
    "hookEventName": "SubagentStart",
    "additionalContext": "Review the repository test conventions first."
  }
}
```

`continue: false`は互換性のためパースされるが、サブエージェントの起動を止めることはできない。

### PreToolUse

Bash・`apply_patch`によるファイル編集・MCPツール呼び出し・その他のローカル関数ツールをインターセプトできる（[ツールカバレッジ](#ツールカバレッジ)参照）。

`matcher`は`tool_name`とそのエイリアスに適用される。`apply_patch`によるファイル編集は`matcher`に`apply_patch`・`Edit`・`Write`のいずれも使えるが、hook入力の`tool_name`は常に`"apply_patch"`。

追加フィールド: `turn_id`（Codex拡張）、`tool_name`、`tool_use_id`、`tool_input`（`Bash`/`apply_patch`は`tool_input.command`、MCP等はその引数）。

`stdout`のプレーンテキストは無視される。JSONで`systemMessage`を使える。ツール呼び出しを拒否するには次のhook固有形を返す。

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Destructive command blocked by hook."
  }
}
```

古い形（互換用）:

```json
{ "decision": "block", "reason": "Destructive command blocked by hook." }
```

exit code `2`＋`stderr`へのブロック理由書き込みでも同様にブロックできる。

ブロックせずモデルに見えるcontextだけ追加するには`hookSpecificOutput.additionalContext`を返す。

ブロックせずにツール呼び出しを書き換えるには、`permissionDecision: "allow"`と`updatedInput`を返す。

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "allow",
    "updatedInput": { "command": "echo rewritten" }
  }
}
```

- Bash/`apply_patch`の`updatedInput`は文字列`command`フィールドを含む必要がある。MCPやその他のローカル関数ツールでは`updatedInput`は差し替え後の引数オブジェクトそのもの。
- `updatedInput`は`permissionDecision: "allow"`と併用する場合のみ有効。それ以外の`updatedInput`はエラー扱い。
- `permissionDecision: "ask"`、旧形式の`decision: "approve"`、`continue: false`、`stopReason`、`suppressOutput`は現状**未対応**。これらを返すとCodexはそのhook実行を失敗としてエラー報告し、ツール呼び出し自体は続行する。

### PermissionRequest

Codexがシェルのエスカレーションやmanaged-network承認など、承認を求めようとするタイミングで実行される。リクエストを許可・拒否、または判断せず通常の承認プロンプトに委ねることができる。承認が不要なコマンドには実行されない。

`matcher`は`tool_name`とそのエイリアスに適用される。現在対応する値は`Bash`・`apply_patch`・`mcp__server__tool`のようなMCPツール名（`apply_patch`は`Edit`/`Write`にもマッチ）。

追加フィールド: `turn_id`（Codex拡張）、`tool_name`、`tool_input`、`tool_input.description`（人間可読な承認理由。常にあるとは限らない）。

`stdout`のプレーンテキストは無視される。

許可する場合:

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PermissionRequest",
    "decision": { "behavior": "allow" }
  }
}
```

拒否する場合:

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PermissionRequest",
    "decision": {
      "behavior": "deny",
      "message": "Blocked by repository policy."
    }
  }
}
```

複数のマッチしたhookが判断を返した場合、**`deny`が優先**される。それ以外で`allow`があれば承認プロンプトを出さずにリクエストを進める。どのhookも判断しない場合、通常の承認フローが使われる。

`updatedInput`・`updatedPermissions`・`interrupt`は将来の挙動用に予約されており、現状は**フェイルクローズ**（返しても無視/エラーになる）ので使わないこと。

### PostToolUse

Bash・`apply_patch`・MCPツール呼び出し・その他のローカル関数ツールが出力を返した後に実行される（Bashは非ゼロ終了時にも実行される）。既に実行済みのツールの副作用を取り消すことはできない（[ツールカバレッジ](#ツールカバレッジ)参照）。

`matcher`は`tool_name`とそのエイリアスに適用される（`apply_patch`の扱いは`PreToolUse`と同様）。

追加フィールド: `turn_id`（Codex拡張）、`tool_name`、`tool_use_id`、`tool_input`、`tool_response`（MCPはMCP呼び出し結果、その他のローカル関数ツールは通常モデル向け出力）。

`stdout`のプレーンテキストは無視される。JSONは`systemMessage`と次のhook固有形に対応する。

```json
{
  "decision": "block",
  "reason": "The Bash output needs review before continuing.",
  "hookSpecificOutput": {
    "hookEventName": "PostToolUse",
    "additionalContext": "The command updated generated files."
  }
}
```

このイベントの`decision: "block"`は**既に完了したBashコマンドを取り消さない**。代わりにCodexはそのフィードバックを記録し、ツール結果をそのフィードバックに差し替えて、hookが返したメッセージからモデルの続行を行う。exit code `2`＋`stderr`へのフィードバック書き込みでも同様。

元のツール結果の通常処理を止めるには`continue: false`を返す。Codexはツール結果をフィードバックまたは停止テキストに差し替えてそこから続行する。

`updatedMCPToolOutput`・`suppressOutput`は現状未対応。返すとそのhook実行は失敗としてエラー報告され、ツール結果の通常処理は続行される。

#### code modeからのツール呼び出し

モデルがcode modeでJavaScriptからツールを呼ぶ場合、hookの判断はそのネストした呼び出しにも適用される。

| hookの結果                                            | code mode側から見える挙動                                                                                   |
| ----------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| `PreToolUse`がブロック                                | ツールが実行される前にPromiseがreject                                                                       |
| `PreToolUse`が`updatedInput`を返す                    | 書き換えられた入力でツールが実行され、その結果でPromiseがresolve                                            |
| `PostToolUse`が`decision: "block"`またはexit code `2` | ツールは実行された後、hookの理由でPromiseがreject                                                           |
| `PostToolUse`が`continue: false`を返す                | モデルに見える結果にはhookのフィードバックが使われるが、実行中スクリプトへのネストしたPromiseはrejectしない |

### PreCompact

Codexがチャットをcompactする前に実行される。`matcher`は`trigger`（`manual`または`auto`）に適用される。

追加フィールド: `turn_id`（Codex拡張）、`trigger`。

`stdout`のプレーンテキストは無視される。JSONは[共通outputフィールド](#共通output-フィールド)に対応。マッチした`PreCompact`hookが`continue: false`を返すと、Codexはcompactionを行う前に停止する。

### PostCompact

Codexがチャットをcompactした後に実行される。`matcher`は`trigger`（`manual`または`auto`）に適用される。

追加フィールド: `turn_id`（Codex拡張）、`trigger`。

`stdout`のプレーンテキストは無視される。JSONは[共通outputフィールド](#共通output-フィールド)に対応。マッチした`PostCompact`hookが`continue: false`を返すと、Codexはcompaction後に停止する。

### UserPromptSubmit

`matcher`は現状このイベントでは使われない。

追加フィールド: `turn_id`（Codex拡張）、`prompt`（送信されようとしているユーザープロンプト）。

`stdout`のプレーンテキストは追加のdeveloper contextとして扱われる。JSONは[共通outputフィールド](#共通output-フィールド)に加え次のhook固有形に対応。

```json
{
  "hookSpecificOutput": {
    "hookEventName": "UserPromptSubmit",
    "additionalContext": "Ask for a clearer reproduction before editing files."
  }
}
```

プロンプトをブロックするには次を返すか、exit code `2`＋`stderr`にブロック理由を書く。

```json
{ "decision": "block", "reason": "Ask for confirmation before doing that." }
```

### SubagentStop

`matcher`は`agent_type`に適用される。

追加フィールド: `turn_id`（Codex拡張）、`agent_id`、`agent_type`、`agent_transcript_path`、`stop_hook_active`（このサブエージェントが既に継続済みかどうか）、`last_assistant_message`。

`SubagentStop`はexit `0`の場合、`stdout`にJSONを期待する。プレーンテキスト出力はこのイベントでは**無効**。

JSONは[共通outputフィールド](#共通output-フィールド)に対応。サブエージェントフローを継続させるには次を返すか、exit code `2`＋`stderr`に継続理由を書く。

```json
{
  "decision": "block",
  "reason": "Run one more focused pass inside the subagent."
}
```

複数のマッチした`SubagentStop`hookのうち、いずれかが`continue: false`を返した場合、他のhookの継続判断より**それが優先**される。

### Stop

`matcher`は現状このイベントでは使われない。

追加フィールド: `turn_id`（Codex拡張）、`stop_hook_active`（このターンが既に`Stop`により継続済みかどうか）、`last_assistant_message`。

`Stop`はexit `0`の場合、`stdout`にJSONを期待する。プレーンテキスト出力はこのイベントでは**無効**。

JSONは[共通outputフィールド](#共通output-フィールド)に対応。Codexを継続させるには次を返すか、exit code `2`＋`stderr`に継続理由を書く。

```json
{ "decision": "block", "reason": "Run one more pass over the failing tests." }
```

このイベントの`decision: "block"`はターンを拒否するのではなく、Codexに継続を指示し、`reason`を新しいユーザープロンプトのテキストとして扱う継続プロンプトを自動生成する。

複数のマッチした`Stop`hookのうち、いずれかが`continue: false`を返した場合、他のhookの継続判断より**それが優先**される。

## Schemas

`main`ブランチのスキーマにはまだリリースされていないhookフィールドが含まれる場合がある。リリース済みの挙動については本ページを正とする。厳密な現行ワイヤーフォーマットが必要な場合はCodex GitHubリポジトリのgenerated schemasを参照する: https://github.com/openai/codex/tree/main/codex-rs/hooks/schema/generated

---

## 参考文献

- Hooks（本ページの原文）: https://developers.openai.com/codex/hooks
- Build plugins（プラグイン同梱hooksのパッケージングルール）: https://developers.openai.com/plugins/build/plugins#bundled-mcp-servers-and-lifecycle-hooks
- Generated schemas: https://github.com/openai/codex/tree/main/codex-rs/hooks/schema/generated
