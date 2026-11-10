# 設定ファイル

Claude Codeは`settings.json`（と環境変数）で挙動を設定する。`/config`コマンドでUIから変更することも、`/config key=value`で1項目だけ変更することも出来る（v2.1.181〜）。

## 目次

- [スコープ](#スコープ保存先の階層)
  - [どのスコープを使うべきか](#どのスコープを使うべきか)
- [設定の反映タイミング](#設定の反映タイミング)
- [permissions（権限設定）](#permissions権限設定)
- [sandbox（サンドボックス）](#sandboxサンドボックス)
- [よく使う設定キー](#よく使う設定キー)
- [環境変数](#環境変数)
- [参考文献](#参考文献)

## スコープ（保存先の階層）

| スコープ                        | 保存先                                                          | 影響範囲                   | チーム共有                                           |
| ------------------------------- | --------------------------------------------------------------- | -------------------------- | ---------------------------------------------------- |
| Managed（管理者）               | サーバー配信 / MDM(plist・レジストリ) / `managed-settings.json` | 組織全体 or マシン全体     | される（ITが配布）                                   |
| User（個人）                    | `~/.claude/settings.json`                                       | 自分・全プロジェクト       | されない                                             |
| Project（プロジェクト）         | `.claude/settings.json`                                         | このリポジトリの全員       | される（gitにコミット）                              |
| Local（個人・プロジェクト限定） | `.claude/settings.local.json`                                   | 自分・このプロジェクトのみ | されない（Claude Codeが作成時に自動でgitignore登録） |

- Windowsでは`~/.claude`は`%USERPROFILE%\.claude`に解決される。
- 優先順位（同じキーが複数箇所にある場合）: **Managed > コマンドライン引数 > Local > Project > User**。
  - 例: User設定で`spinnerTipsEnabled: true`、Project設定で`false`なら、Projectの`false`が勝つ。
  - ただし`permissions`のルールは上書きでなく**全スコープがマージ**される（詳細は下記）。
- `~/.claude.json`には`settings.json`とは別に、OAuthセッション・MCPサーバー設定（user/localスコープ）・プロジェクトごとの許可状態・各種キャッシュが入る。プロジェクトスコープのMCPは`.mcp.json`に別途保存される。

### どのスコープを使うべきか

- **Managed**: 組織全体で強制したいセキュリティポリシー・コンプライアンス要件
- **User**: テーマ・エディタ設定など個人の好み、全プロジェクトで使うAPIキー
- **Project**: `permissions`・`hooks`・MCPサーバーなどチームで共有すべき設定
- **Local**: このプロジェクトだけの個人的な上書き、共有前の実験的設定

## 設定の反映タイミング

`permissions`・`hooks`・`apiKeyHelper`などほとんどのキーはファイル変更を検知して**再起動なしで反映**される（変更検知のたびに`ConfigChange`フックが発火）。
例外は次の2つで、**次回起動時**に反映：

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

- ルールの形式は`Tool`または`Tool(specifier)`。評価順は**deny → ask → allow**で、最初にマッチしたものが適用される（ルールの詳細度に関わらず）。
- MCPツールは`mcp__<server>__get_*`のようにサーバー名の後ろだけglobが使える（サーバー名自体にはglob不可）。
- `defaultMode`: 起動時のデフォルト権限モード（`default`/`acceptEdits`/`plan`/`auto`/`dontAsk`/`bypassPermissions`/`manual`）。`auto`はProject/Local設定からは無視される（リポジトリが自分自身にauto modeを付与できないようにするため）。User設定(`~/.claude/settings.json`)に置く必要がある。

## sandbox（サンドボックス）

Bashコマンドをファイルシステム・ネットワークから隔離する機能（macOS/Linux/WSL2）。

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

- `filesystem.*`はOSレベルのサンドボックス境界（`kubectl`・`terraform`など全サブプロセスに適用）。パスのプレフィックスは`/`=絶対パス、`~/`=ホーム基準、`./`=プロジェクトルート基準。
- パーミッションルール（`Edit`/`Read`/`WebFetch`の allow/deny）もサンドボックス設定にマージされる。
- `credentials.envVars`で特定の環境変数（`GITHUB_TOKEN`など）をサンドボックス内コマンドから保護できる。単純な非表示に留まらず、拡張されたcredential-masking機構になっている。
  - `mode`: 隠す（従来のhide/hidden相当）か、`"mask"`（Linux/WSLでは値をセンチネルファイルに置き換える）かを選べる。
  - `extract` / `onExtractNoMatch`: パターンでcredential値の一部だけを抽出し、マッチしなかった場合の挙動も制御できる。
  - JWTを認識した`decode`処理にも対応。
  - `awsPairs` / `sigv4`でAWS SigV4署名付きリクエストの再署名にも対応。

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

| 変数                                         | 用途                                                                                     |
| -------------------------------------------- | ---------------------------------------------------------------------------------------- |
| `ANTHROPIC_API_KEY`                          | APIキー（サブスクリプションより優先。対話モードでは初回承認が必要、`unset`で元に戻せる） |
| `ANTHROPIC_MODEL`                            | 使用モデル名の指定                                                                       |
| `BASH_DEFAULT_TIMEOUT_MS`                    | 長時間実行bashコマンドのデフォルトタイムアウト（デフォルト120000ms）                     |
| `MAX_THINKING_TOKENS`                        | 拡張思考のトークン予算上限。`0`で無効化（Fable 5除く）                                   |
| `CLAUDE_CODE_MAX_OUTPUT_TOKENS`              | 1リクエストの最大出力トークン数（増やすとauto-compactionまでの実効コンテキストが減る）   |
| `DISABLE_AUTOUPDATER`                        | バックグラウンド自動更新を無効化（`claude update`は手動実行可）                          |
| `DISABLE_COST_WARNINGS`                      | コスト警告メッセージを無効化                                                             |
| `DO_NOT_TRACK`                               | テレメトリをオプトアウト（`DISABLE_TELEMETRY`と同等、業界共通の慣習に準拠）              |
| `HTTP_PROXY` / `HTTPS_PROXY`                 | プロキシサーバー指定                                                                     |
| `CLAUDE_CODE_USE_POWERSHELL_TOOL`（Windows） | PowerShellツールの有効化。Git Bash未導入なら自動有効、導入済みなら`1`でopt-in            |
| `CLAUDE_CODE_GIT_BASH_PATH`（Windows）       | Git Bash（`bash.exe`）がPATH上に無い場合の明示パス指定                                   |

こちらも全変数一覧（300以上）は公式ドキュメント参照。

## 参考文献

- 設定ファイル: https://code.claude.com/docs/en/settings
- 環境変数: https://code.claude.com/docs/en/env-vars
