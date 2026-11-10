# 既存ログの所在・デバッグフラグ・settings切り分け

`claude-logs-investigate` ・ `claude-settings` スキル（作成時の参考資料）の内容を要約せず転記した上で、実地検証（Windows 11 / Claude Code v2.1.215）で見つかった相違点・実例を **> 実地検証:** として各所に追記してある。

## 目次

- [既存ログの所在](#既存ログの所在)
- [デバッグフラグ・スラッシュコマンド](#デバッグフラグスラッシュコマンド)
- [ログを仕込む(概要)](#ログを仕込む概要)
- [settingsスコープ](#settingsスコープ)
- [設定の反映タイミング](#設定の反映タイミング)
- [permissions（権限設定）](#permissions権限設定)
- [sandbox（サンドボックス）](#sandboxサンドボックス)
- [よく使う設定キー](#よく使う設定キー)
- [環境変数](#環境変数)
- [参照](#参照)

## 既存ログの所在

`~/.claude/`（Windowsでは`%USERPROFILE%\.claude`に解決される）配下:

- `projects/<project>/<session-id>.jsonl` — セッショントランスクリプト本体。`<project>` は作業ディレクトリの絶対パスの非英数字を `-` に置換したもの。1行1JSONで、会話・ツール呼び出し・thinking・添付ファイル等が記録される（実体は内部形式でバージョン間に差異があるため、jqやgrepで特定フィールドを拾う使い方が安全）
  - 巨大なツール出力は同名の `<session-id>/tool-results/` ディレクトリに退避され、jsonl側には参照のみが残ることがある
  - > 実地検証: ドライブレターが小文字化される場合がある（`C:\CodeRoot\AI` → `c--CodeRoot-AI`）。一方で生成元によっては大文字始まり（`C--CodeRoot-AI-*`）のディレクトリも同居しており、表記揺れが実在する。`<project>`名で決め打ち検索する場合は大文字・小文字両方を候補に入れること
- `sessions/<pid>.json` — 実行中セッションのプロセスレジストリ。ドキュメント上の主要フィールドは `pid`, `sessionId`, `cwd`, `startedAt`, `version`, `entrypoint`, `name`
  - > 実地検証: 実際には上記に加え `procStart`, `peerProtocol`, `kind`（`interactive`等）, `nameSource`（`derived`等）, `status`（`busy`等）, `updatedAt`, `statusUpdatedAt` も入っている。今動いているセッションの生死・busy状態を機械的に知りたい時は`status`/`updatedAt`が使える
- `shell-snapshots/snapshot-bash-<timestamp>-<rand>.sh` — Bashツール起動時のシェル環境（関数・エイリアス・PATH等）のスナップショット。関数定義は`eval "$(echo '<base64>' | base64 -d)"`形式で埋め込まれている（実地検証で確認済み）
- `session-env/<session-id>/` — セッションごとの環境情報ディレクトリ。実地検証では対象セッション分が空ディレクトリだった（何をトリガーに書き込まれるかは今回未特定）
- `history.jsonl` — プロジェクト横断のプロンプト入力履歴。フィールドは`display`, `pastedContents`, `project`, `sessionId`, `timestamp`（実地検証で実物のフィールドと一致を確認）
- `debug/` — `--debug-file`等で明示的にファイル出力させたデバッグログの書き出し先
  - > **実地検証で相違を確認**: 「通常は空」という想定と異なり、`--debug-file`を指定しない通常起動でも`debug/<uuid>.txt`が毎回自動生成され、起動時の`[DEBUG]`ログ（MDM設定読み込み、CA証明書ロード、skill/plugin読み込み等）が最初から書き出されていた。少なくともこの環境・バージョンでは常時デバッグログが出力される。原因不明の起動時異常を調べる際は、まず`--debug-file`を指定しなくても`debug/`配下の最新ファイルを確認すればよい

補足:

- `CLAUDE_CONFIG_DIR` で `~/.claude` 自体の場所を変更できる（調査環境を汚したくない時の切り分けにも使える。詳細は[testing.md](testing.md)）
- 保持期間は `settings.json` の `cleanupPeriodDays`（デフォルト30日）
- `CLAUDE_CODE_SKIP_PROMPT_HISTORY` 環境変数、または非対話1回実行時の `--no-session-persistence` フラグでトランスクリプト書き込みを抑止できる
- hookやstatuslineには `transcript_path` フィールドが渡ってくるため、そこから該当セッションのjsonlパスを直接取得できる
- `~/.claude.json` には`settings.json`とは別に、OAuthセッション・MCPサーバー設定（user/localスコープ）・プロジェクトごとの許可状態・各種キャッシュが入る。プロジェクトスコープのMCPは`.mcp.json`に別途保存される
  - > 実地検証: `~/.claude.json`は大文字小文字違いの重複キー（プロジェクトパス等）を含むことがあり、**PowerShellの`ConvertFrom-Json`がそのままでは失敗する**（`Cannot convert the JSON string because it contains keys with different casing`）。Windowsで解析する場合は`ConvertFrom-Json -AsHashtable`を使うこと

## デバッグフラグ・スラッシュコマンド

- `-d, --debug [filter]` — カテゴリフィルタ付きデバッグモード。例: `"api,hooks"`（該当カテゴリのみ）、`"!1p,!file"`（除外指定）
  - > **実地検証で相違を確認**: `-d "hooks"`を指定しても「hooksカテゴリのみに絞り込まれる」という挙動は確認できなかった。`claude -p "..." --debug-file <path> -d "hooks"` の出力172行のうち、起動処理・CA証明書ロード・MCP接続・API送受信など無関係な`[DEBUG]`行がほぼ全て出力され、hook関連は3行（`Registered 0 hooks from 0 plugins`等）のみだった。フィルタが実際に何を制御しているか（カテゴリではなく別の軸の可能性）はこの検証だけでは断定できないため、**フィルタで期待通り絞り込めない前提で、絞り込み後も`grep`で二段構えに読む**のが安全
- `--debug-file <path>` — デバッグログを指定ファイルに書き出す（暗黙的にdebugモードを有効化）。実地検証で動作確認済み（非対話1回実行 `claude -p "..." --model claude-haiku-4-5-20251001 --debug-file <path>` で通常起動と同形式の`[DEBUG]`ログがファイルに書き出された）
- `claude --debug` — MCPサーバーのstderr出力（接続してもツールが0件、等の切り分けに有効）や、hookのマッチャー判定・終了コード・出力のライブトレースを確認（`--debug mcp`/`--debug hooks`のようなサブモード指定は廃止され、単一の`--debug`がこれらを含む形に統一された）
  - > 実地検証: このプロジェクトには`.mcp.json`も`~/.claude.json`の`mcpServers`キーも存在しなかったが、`--debug-file`の出力には`claude.ai Google Drive/Calendar/Gmail`という**アカウント紐付けのリモートMCP統合**が登場した。プロジェクトローカルのMCP設定が空でも、アカウント側のMCP接続ログは出る点に注意
- `--safe-mode` — 全カスタマイズ（hook/MCP/skills等）を無効化して起動し、問題の切り分けを行う（実地検証詳細は[testing.md](testing.md)）
- `CLAUDE_CONFIG_DIR=/tmp/claude-clean claude` — クリーンな設定ディレクトリで起動して切り分ける（実地検証詳細は[testing.md](testing.md)）
- セッション内スラッシュコマンド:
  - `/context` — コンテキスト消費の内訳
  - `/doctor` — 設定の診断（不正なキー等の検出）
  - `/hooks` — 現在有効なhook設定の一覧
  - `/mcp` — MCP接続状態
  - `/permissions` — 有効な許可/拒否ルール
  - `/status` — どの設定ソース（managed/user/project/local）が効いているか
  - `/memory` — 読み込まれているCLAUDE.md/rules
  - `/debug [issue]` — セッション内でデバッグログを有効化
  - > 実地検証メモ: これらはインタラクティブUI前提のスラッシュコマンドのため、ツール呼び出し経由の非対話実行では直接叩けない。同等の裏取りは、実在する`.claude/settings.json` / `.claude/settings.local.json` / `~/.claude/settings.json`を直接読み比べることで代替できる（下記「settingsスコープ」の実例）

これらのコマンド・フラグの使い分けの詳細な使用手順は `debug-your-config` ドキュメント相当の内容であり、`claude-code-docs` スキル経由で最新の公式ドキュメントを参照できる。正確なフラグ文言は`claude-cli-docs`スキルを参照。

## ログを仕込む(概要)

- hookでの仕込み方の具体的な手順（hookの種類・matcher・exit code・Windows注意点・実際に動作確認済みのテンプレート）は [hooks-logging.md](hooks-logging.md) を参照
- OpenTelemetryでの継続的な計装は [otel-reference.md](otel-reference.md) を参照

## settingsスコープ

| スコープ                        | 保存先                                                          | 影響範囲                   | チーム共有                                           |
| ------------------------------- | --------------------------------------------------------------- | -------------------------- | ---------------------------------------------------- |
| Managed（管理者）               | サーバー配信 / MDM(plist・レジストリ) / `managed-settings.json` | 組織全体 or マシン全体     | される（ITが配布）                                   |
| User（個人）                    | `~/.claude/settings.json`                                       | 自分・全プロジェクト       | されない                                             |
| Project（プロジェクト）         | `.claude/settings.json`                                         | このリポジトリの全員       | される（gitにコミット）                              |
| Local（個人・プロジェクト限定） | `.claude/settings.local.json`                                   | 自分・このプロジェクトのみ | されない（Claude Codeが作成時に自動でgitignore登録） |

- Windowsでは`~/.claude`は`%USERPROFILE%\.claude`に解決される（実地検証でも一致）
- 優先順位（同じキーが複数箇所にある場合）: **Managed > コマンドライン引数 > Local > Project > User**
  - ただし`permissions`のルールは上書きでなく**全スコープがマージ**される（詳細は下記permissions節）
- > 実地検証の実例: このリポジトリでは Project設定 `.claude/settings.json` は`enabledPlugins`のみ、Local設定 `.claude/settings.local.json` は`outputStyle`のみを持ち、`permissions.defaultMode: "auto"`はUser設定（`~/.claude/settings.json`）側にのみ書かれていた。Managed設定ファイル（`C:\Program Files\ClaudeCode\managed-settings.json`）は未配置で、debugログ上も「symlink or missing file」と出ていた

### どのスコープを使うべきか

- **Managed**: 組織全体で強制したいセキュリティポリシー・コンプライアンス要件
- **User**: テーマ・エディタ設定など個人の好み、全プロジェクトで使うAPIキー
- **Project**: `permissions`・`hooks`・MCPサーバーなどチームで共有すべき設定
- **Local**: このプロジェクトだけの個人的な上書き、共有前の実験的設定

## 設定の反映タイミング

`permissions`・`hooks`・`apiKeyHelper`などほとんどのキーはファイル変更を検知して**再起動なしで反映**される（変更検知のたびに`ConfigChange`フックが発火）。例外は次の2つで、**次回起動時**に反映：

- `model`（セッション中に変えたいなら`/model`を使う）
- `outputStyle`（システムプロンプトの一部のため、`/clear`か再起動が必要）

## permissions（権限設定）

```json
{
  "permissions": {
    "allow": ["Bash(npm run lint)", "Bash(npm run test *)", "Read(~/.zshrc)"],
    "deny": [
      "Bash(curl *)",
      "Read(./.env)",
      "Read(./.env.*)",
      "Read(./secrets/**)"
    ],
    "ask": ["Bash(git push *)"]
  }
}
```

- ルールの形式は`Tool`または`Tool(specifier)`。評価順は**deny → ask → allow**で、最初にマッチしたものが適用される（ルールの詳細度に関わらず）
- MCPツールは`mcp__<server>__get_*`のようにサーバー名の後ろだけglobが使える（サーバー名自体にはglob不可）
- `defaultMode`: 起動時のデフォルト権限モード（`default`/`acceptEdits`/`plan`/`auto`/`dontAsk`/`bypassPermissions`/`manual`）。`auto`はProject/Local設定からは無視される（リポジトリが自分自身にauto modeを付与できないようにするため）。User設定(`~/.claude/settings.json`)に置く必要がある
  - > 実地検証: この制約に整合する実例を確認済み（`defaultMode: "auto"`は実際にUser設定にのみ存在し、Project/Localには書かれていなかった）

## sandbox（サンドボックス）

Bashコマンドをファイルシステム・ネットワークから隔離する機能（macOS/Linux/WSL2。Windowsネイティブでは対象外）。

```json
{
  "sandbox": {
    "enabled": true,
    "excludedCommands": ["docker *"],
    "filesystem": {
      "allowWrite": ["/tmp/build", "~/.kube"],
      "denyRead": ["~/.aws/credentials"]
    },
    "network": {
      "allowedDomains": ["github.com", "*.npmjs.org"],
      "deniedDomains": ["uploads.github.com"]
    }
  }
}
```

- `filesystem.*`はOSレベルのサンドボックス境界（`kubectl`・`terraform`など全サブプロセスに適用）。パスのプレフィックスは`/`=絶対パス、`~/`=ホーム基準、`./`=プロジェクトルート基準
- パーミッションルール（`Edit`/`Read`/`WebFetch`の allow/deny）もサンドボックス設定にマージされる
- `credentials.envVars`で特定の環境変数（`GITHUB_TOKEN`など）をサンドボックス内コマンドから隠せる

## よく使う設定キー

| キー                           | 説明                                                                                                    | 例                                                          |
| ------------------------------ | ------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------- |
| `model`                        | デフォルトモデルの上書き。1セッションだけなら`--model`か`ANTHROPIC_MODEL`                               | `"claude-sonnet-5"`                                         |
| `fallbackModel`                | 主モデルが過負荷の時に順に試すモデル（最大3つ、マージされず最優先のファイルが全体を上書き）             | `["claude-sonnet-5", "claude-haiku-4-5"]`                   |
| `alwaysThinkingEnabled`        | 拡張思考をデフォルトでON                                                                                | `true`                                                      |
| `effortLevel`                  | reasoning effortの永続化（`low`/`medium`/`high`/`xhigh`）。`/effort`実行時に自動保存                    | `"xhigh"`                                                   |
| `env`                          | 全セッション・サブプロセスに適用する環境変数                                                            | `{"FOO": "bar"}`                                            |
| `hooks`                        | ライフサイクルイベントでのカスタムコマンド                                                              | —                                                           |
| `statusLine`                   | カスタムステータスライン                                                                                | `{"type": "command", "command": "~/.claude/statusline.sh"}` |
| `outputStyle`                  | システムプロンプトを変えるスタイル                                                                      | `"Explanatory"`                                             |
| `language`                     | Claudeの応答言語（音声入力・セッションタイトルにも影響）                                                | `"japanese"`                                                |
| `autoCompactEnabled`           | コンテキスト逼迫時の自動圧縮（デフォルト`true`）                                                        | `false`                                                     |
| `autoMemoryEnabled`            | auto memoryの有効/無効（デフォルト`true`）                                                              | `false`                                                     |
| `fileCheckpointingEnabled`     | `/rewind`用の編集前スナップショット（デフォルト`true`）                                                 | `false`                                                     |
| `includeGitInstructions`       | commit/PRワークフローの指示とgit状態をシステムプロンプトに含めるか（デフォルト`true`）                  | `false`                                                     |
| `cleanupPeriodDays`            | 古いセッションファイルの自動削除までの日数（デフォルト30、最小1）                                       | `20`                                                        |
| `disableBundledSkills`         | 同梱スキル・ワークフローを無効化                                                                        | `true`                                                      |
| `disableWorkflows`             | 動的ワークフローを無効化                                                                                | `true`                                                      |
| `theme` / `tui`                | カラーテーマ / ターミナルUIレンダラー（`fullscreen`推奨）                                               | `"dark"` / `"fullscreen"`                                   |
| `verbose`                      | ツール出力を省略せず全表示                                                                              | `true`                                                      |
| `attribution`                  | git commit / PRへのAttribution文言のカスタマイズ・無効化                                                | `{"commit": "", "pr": ""}`                                  |
| `defaultShell`                 | `!`コマンドのデフォルトシェル（Windowsで`"powershell"`にすると`CLAUDE_CODE_USE_POWERSHELL_TOOL=1`必須） | `"powershell"`                                              |
| `disableBypassPermissionsMode` | `--dangerously-skip-permissions`自体を無効化                                                            | `"disable"`                                                 |

全キー一覧（100以上ある）は公式ドキュメント参照。上記は個人利用でよく触るものの抜粋。

## 環境変数

同じ挙動が環境変数と設定キーの両方にある場合、**環境変数が優先**される（例: `ANTHROPIC_MODEL`が`model`設定より優先）。CLIフラグ・セッション内コマンドとの優先順位は機能ごとに異なる（例: `--model`/`/model` > `ANTHROPIC_MODEL`、`CLAUDE_CODE_EFFORT_LEVEL` > `/effort`）。環境変数は起動時に読み込まれるため、変更は次回起動から反映される。

| 変数                                         | 用途                                                                                                        |
| -------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| `ANTHROPIC_API_KEY`                          | APIキー（サブスクリプションより優先。対話モードでは初回承認が必要、`unset`で元に戻せる）                    |
| `ANTHROPIC_MODEL`                            | 使用モデル名の指定                                                                                          |
| `BASH_DEFAULT_TIMEOUT_MS`                    | 長時間実行bashコマンドのデフォルトタイムアウト（デフォルト120000ms）                                        |
| `MAX_THINKING_TOKENS`                        | 拡張思考のトークン予算上限。`0`で無効化（Fable 5除く）                                                      |
| `CLAUDE_CODE_MAX_OUTPUT_TOKENS`              | 1リクエストの最大出力トークン数（増やすとauto-compactionまでの実効コンテキストが減る）                      |
| `DISABLE_AUTOUPDATER`                        | バックグラウンド自動更新を無効化（`claude update`は手動実行可）                                             |
| `DISABLE_COST_WARNINGS`                      | コスト警告メッセージを無効化                                                                                |
| `DO_NOT_TRACK`                               | テレメトリをオプトアウト（`DISABLE_TELEMETRY`と同等、業界共通の慣習に準拠）                                 |
| `HTTP_PROXY` / `HTTPS_PROXY`                 | プロキシサーバー指定                                                                                        |
| `CLAUDE_CODE_ENABLE_TELEMETRY`               | OpenTelemetry送信の有効化。詳細は[otel-reference.md](otel-reference.md)                                     |
| `CLAUDE_CODE_USE_POWERSHELL_TOOL`（Windows） | PowerShellツールの有効化。Git Bash未導入なら自動有効、導入済みなら`1`でopt-in                               |
| `CLAUDE_CODE_GIT_BASH_PATH`（Windows）       | Git Bash（`bash.exe`）がPATH上に無い場合の明示パス指定                                                      |
| `CLAUDE_CONFIG_DIR`                          | `~/.claude`自体の場所を変更（クリーンな設定ディレクトリでの分離起動に使う。詳細は[testing.md](testing.md)） |

こちらも全変数一覧（300以上）は公式ドキュメント参照。

- > **実地検証**: このマシン・このセッションのプロセス環境には、既に `CLAUDE_CODE_ENABLE_TELEMETRY=1` が設定されていた（`CLAUDECODE=1` / `CLAUDE_CODE_CHILD_SESSION=1` / `CLAUDE_CODE_ENTRYPOINT=cli` も同時に確認）。OTelを新規に有効化する検証を行う際は、「まっさらな状態から有効化する」のではなく「既に有効化されている前提でエンドポイント等の追加設定を確認する」ことになる点に注意（詳細は[otel-reference.md](otel-reference.md)）

## 参照

- [otel-reference.md](otel-reference.md) — OTel環境変数・メトリクス名・イベント名の全量リファレンス
- [hooks-logging.md](hooks-logging.md) — hookでのログ仕込みの具体的な手順
- [testing.md](testing.md) — サブエージェント/CLI分離でのテスト手法
- `writing-hooks` スキル — hookの書き方・登録方法・デバッグ方法の詳細
- `claude-code-docs` スキル — 上記の元になっている公式ドキュメント（`monitoring-usage`, `sessions`, `settings`, `env-vars`, `debug-your-config` 等）の最新版を直接参照したい場合
- `claude-cli-docs` スキル — `--debug`/`--debug-file`/`--verbose` などCLIフラグの正確な説明文
- 設定ファイル公式ドキュメント: https://code.claude.com/docs/en/settings
- 環境変数公式ドキュメント: https://code.claude.com/docs/en/env-vars
