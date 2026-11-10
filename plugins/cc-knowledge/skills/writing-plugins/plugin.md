# claudeコマンドでの、プラグインの利用方法

> 参考文献: [Create plugins](https://code.claude.com/docs/en/plugins) / [Plugins reference](https://code.claude.com/docs/en/plugins-reference) / [Discover and install plugins](https://code.claude.com/docs/en/discover-plugins) / [Create and distribute a plugin marketplace](https://code.claude.com/docs/en/plugin-marketplaces)

## 目次

- [基本概要](#基本概要)
- [クイックスタート](#クイックスタートプラグインの作成)
- [プラグインのフォルダ構造](#プラグインのフォルダ構造)
- [`plugin.json`（マニフェスト）](#pluginjsonマニフェスト)
- [主なコンポーネント](#主なコンポーネント)
- [スキルディレクトリプラグイン](#スキルディレクトリプラグインskills-dir)
- [テスト・デバッグ](#テストデバッグ)
- [マーケットプレイス](#マーケットプレイス)
- [バージョン管理](#バージョン管理)
- [主なCLIコマンド](#主なcliコマンド)
- [注意事項](#注意事項)
- [参考文献](#参考文献)

## 基本概要

プラグインは、skills・agents・hooks・MCPサーバー・LSPサーバーなどをまとめて配布できる自己完結型のディレクトリ。チーム・コミュニティへの共有、複数プロジェクトへの再利用、バージョン管理された配布に向く。

| 方式                                                                           | スキル名             | 向いている用途                                                                     |
| :----------------------------------------------------------------------------- | :------------------- | :--------------------------------------------------------------------------------- |
| スタンドアロン（`.claude/`配下）                                               | `/hello`             | 個人用ワークフロー、プロジェクト固有のカスタマイズ、試作                           |
| プラグイン（`skills`/`agents`/`hooks`等 + 任意で`.claude-plugin/plugin.json`） | `/plugin-name:hello` | チーム・コミュニティへの共有、複数プロジェクトでの再利用、バージョン管理された配布 |

まず`.claude/`で試作し、共有したくなったらプラグイン化するのが定石。プラグインのスキルは常に`/plugin-name:hello`のように名前空間化される（プラグイン間の名前衝突を防ぐため）。

## クイックスタート（プラグインの作成）

1. プラグイン用ディレクトリを作成（例: `my-first-plugin/`）
2. マニフェストを作成: `my-first-plugin/.claude-plugin/plugin.json`

   ```json
   {
     "name": "my-first-plugin",
     "description": "A greeting plugin to learn the basics",
     "version": "1.0.0",
     "author": { "name": "Your Name" }
   }
   ```

3. スキルを追加: `my-first-plugin/skills/hello/SKILL.md`（`skills/<name>/SKILL.md`という構造で、フォルダ名がスキル名になる）
4. `--plugin-dir`でローカル動作確認

   ```shell
   claude --plugin-dir ./my-first-plugin
   # セッション内で /my-first-plugin:hello を実行
   ```

5. `SKILL.md`を編集したら`/reload-plugins`で再起動なしに反映

### スキルディレクトリに直接置く方法（`claude plugin init`）

毎回`--plugin-dir`を付けたくない場合、`claude plugin init my-tool`を実行すると`~/.claude/skills/my-tool/`にマニフェストと雛形`SKILL.md`が生成され、次回セッションから`my-tool@skills-dir`として自動ロードされる（マーケットプレイス登録・インストール操作は不要）。詳細は[スキルディレクトリプラグイン](#スキルディレクトリプラグインskills-dir)を参照。

## プラグインのフォルダ構造

Source: [plugins.md#plugin-structure-overview](https://code.claude.com/docs/en/plugins#plugin-structure-overview)

| ディレクトリ／ファイル | 場所           | 用途                                                                               |
| :--------------------- | :------------- | :--------------------------------------------------------------------------------- |
| `.claude-plugin/`      | プラグイン直下 | `plugin.json`マニフェストのみを置く（任意）                                        |
| `skills/`              | プラグイン直下 | `<name>/SKILL.md`形式のスキル                                                      |
| `commands/`            | プラグイン直下 | フラットな`.md`ファイルのスキル（新規プラグインは`skills/`推奨）                   |
| `agents/`              | プラグイン直下 | カスタムサブエージェント定義                                                       |
| `hooks/`               | プラグイン直下 | `hooks.json`によるイベントハンドラ                                                 |
| `.mcp.json`            | プラグイン直下 | MCPサーバー設定                                                                    |
| `.lsp.json`            | プラグイン直下 | LSPサーバー設定（コードインテリジェンス）                                          |
| `monitors/`            | プラグイン直下 | `monitors.json`によるバックグラウンド監視設定                                      |
| `bin/`                 | プラグイン直下 | プラグイン有効時にBashツールの`PATH`へ追加される実行ファイル                       |
| `settings.json`        | プラグイン直下 | プラグイン有効時に適用されるデフォルト設定（`agent`/`subagentStatusLine`のみ対応） |

**よくある間違い**: `commands/`・`agents/`・`skills/`・`hooks/`等を`.claude-plugin/`の中に置いてしまうこと。`.claude-plugin/`直下に置くのは`plugin.json`だけで、それ以外は必ずプラグインのルート直下に置く。

スキルが1つだけのプラグインは、`skills/`ディレクトリを作らず`SKILL.md`をプラグイン直下に直接置いてもよい（frontmatterの`name`で呼び出し名を制御。未指定時はインストールディレクトリ名にフォールバックするが、マーケットプレイス経由のインストールではこれがバージョン文字列になり更新のたびに変わるため注意）。複数スキルを持たせる予定があるなら最初から`skills/`構成にする。

## `plugin.json`（マニフェスト）

マニフェストは任意。省略時はデフォルトの場所（上表）から自動検出し、プラグイン名はディレクトリ名になる。メタデータやカスタムパスが必要な場合にのみ作成する。

### 必須フィールド

`name`のみ必須（kebab-case、スペース不可）。コンポーネントの名前空間として使われる（例: `plugin-dev`というプラグインの`agent-creator`エージェントは`plugin-dev:agent-creator`として表示される）。

未知のトップレベルフィールドは無視される（他のエコシステム由来のメタデータ、`package.json`やMCPB/DXTマニフェストとの共用が可能）。型が違う場合はエラーになる。`claude plugin validate --strict`でCI上は未知フィールドの警告もエラー扱いにできる。

### 主なメタデータフィールド

| フィールド                                         | 型           | 説明                                                                                                                                           |
| :------------------------------------------------- | :----------- | :--------------------------------------------------------------------------------------------------------------------------------------------- |
| `displayName`                                      | string       | UI表示名（スペース・大文字小文字自由）。省略時は`name`にフォールバック                                                                         |
| `version`                                          | string       | 明示すると、このフィールドを上げたときだけユーザーに更新が配信される。省略時はgitのコミットSHAが使われ、コミットのたびに新バージョン扱いになる |
| `description`                                      | string       | プラグインの簡単な説明                                                                                                                         |
| `author`                                           | object       | `{"name": "...", "email": "...", "url": "..."}`                                                                                                |
| `homepage` / `repository` / `license` / `keywords` | string/array | ドキュメントURL・ソースURL・ライセンス・検索タグ                                                                                               |
| `defaultEnabled`                                   | boolean      | `false`にすると無効状態でインストールされる（外部サービス連携など、オプトインさせたいプラグイン向け。v2.1.154以降）                            |
| `metadata`                                         | object       | 自由形式のメタデータフィールド                                                                                                                 |

### コンポーネントパスフィールド

| フィールド                                      | 型                    | 説明                                                                                 |
| :---------------------------------------------- | :-------------------- | :----------------------------------------------------------------------------------- |
| `skills`                                        | string\|array         | デフォルトの`skills/`走査に**追加**するディレクトリ                                  |
| `commands`                                      | string\|array         | デフォルトの`commands/`を**置き換える**                                              |
| `agents`                                        | string\|array         | デフォルトの`agents/`を**置き換える**                                                |
| `hooks`                                         | string\|array\|object | フック設定ファイルパス、またはインライン設定                                         |
| `mcpServers`                                    | string\|array\|object | MCP設定ファイルパス、またはインライン設定                                            |
| `lspServers`                                    | string\|array\|object | LSP設定ファイルパス、またはインライン設定                                            |
| `experimental.themes` / `experimental.monitors` | string\|array         | カラーテーマ・バックグラウンド監視（実験的コンポーネント。スキーマが今後変わりうる） |
| `userConfig`                                    | object                | プラグイン有効化時にユーザーへ入力を促す値（下記参照）                               |
| `dependencies`                                  | array                 | このプラグインが依存する他プラグイン（semverレンジ指定可）                           |

パスはすべてプラグインルートからの相対パスで`./`から始める必要がある。`skills`だけは「追加」、それ以外（`commands`/`agents`/`outputStyles`/`experimental.*`）は「置き換え」である点に注意（両方欲しい場合はデフォルトパスも明示的に列挙する）。

### ユーザー設定（`userConfig`）

プラグイン有効化時にユーザーへ入力を促したい値（APIエンドポイント、トークン等）を宣言できる。

```json
{
  "userConfig": {
    "api_token": {
      "type": "string",
      "title": "API token",
      "description": "API authentication token",
      "sensitive": true
    }
  }
}
```

`sensitive: true`の値はOSのキーチェーン（不可なら`~/.claude/.credentials.json`）に保存される。フック・MCP/LSP設定・monitorコマンドでは`${user_config.KEY}`として、非sensitiveな値はスキル・エージェント本文でも参照できる。すべての値はサブプロセスに`CLAUDE_PLUGIN_OPTION_<KEY>`環境変数としても渡される。

### 環境変数（パス参照用プレースホルダ）

| 変数                    | 説明                                                                                                                   |
| :---------------------- | :--------------------------------------------------------------------------------------------------------------------- |
| `${CLAUDE_PLUGIN_ROOT}` | プラグインのインストールディレクトリの絶対パス。プラグイン更新のたびに変わるため、状態の永続化には使わない             |
| `${CLAUDE_PLUGIN_DATA}` | プラグイン更新をまたいで永続化されるデータディレクトリ（`node_modules`のインストール等に）。初回参照時に自動作成される |
| `${CLAUDE_PROJECT_DIR}` | プロジェクトルート（フックが受け取る`CLAUDE_PROJECT_DIR`と同じ）                                                       |

これらはスキル本文・エージェント本文・フックコマンド・monitorコマンド・MCP/LSP設定内のどこに書いても置換され、フック／MCP／LSPのサブプロセスには環境変数としても渡される。

## 主なコンポーネント

### Agents

`agents/`配下にMarkdownファイルを置く。対応frontmatterは`name`, `description`, `model`, `effort`, `maxTurns`, `tools`, `disallowedTools`, `skills`, `memory`, `background`, `isolation`（`"worktree"`のみ）。セキュリティ上、`hooks`・`mcpServers`・`permissionMode`はプラグイン提供エージェントでは無視される。詳細は同梱の[subagent.md](../writing-subagents/subagent.md)を参照。

### Hooks

`hooks/hooks.json`（またはマニフェストへのインライン記述）でイベントハンドラを定義する。対応イベント・タイプは通常のフックと同じ（`command`/`http`/`mcp_tool`/`prompt`/`agent`）。詳細は同梱の[hooks.md](../writing-hooks/hooks.md)を参照。

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "\"${CLAUDE_PLUGIN_ROOT}\"/scripts/format-code.sh"
          }
        ]
      }
    ]
  }
}
```

### MCPサーバー

`.mcp.json`（またはインライン）でMCPサーバーを同梱できる。プラグイン有効化時に自動起動する。

### LSPサーバー

`.lsp.json`でLanguage Server Protocol接続を定義すると、編集直後の診断（型エラー等）やコードナビゲーションをClaudeに与えられる。バイナリ自体は別途インストールが必要。TypeScript/Python/Rust等の主要言語は公式マーケットプレイスに`*-lsp`プラグインが用意されている。

### Monitors（バックグラウンド監視）

`monitors/monitors.json`にコマンドを列挙すると、プラグイン有効化中はセッション開始時に自動でバックグラウンド実行され、標準出力の各行がClaudeへの通知として届く。ログ監視やデプロイ状況のポーリングなどに使う。対話型CLIセッションでのみ動作。

### Themes

`themes/`配下のJSONでカラーテーマを配布できる。`base`（`dark`/`light`）と`overrides`（トークンごとの色）を持つ。ユーザーが`/theme`で選択すると`custom:<plugin-name>:<slug>`として永続化される。

## スキルディレクトリプラグイン（`@skills-dir`）

スキルディレクトリ（`~/.claude/skills/`または`<cwd>/.claude/skills/`）配下に`.claude-plugin/plugin.json`を持つフォルダがあると、マーケットプレイス登録もインストール操作も不要で次回セッションから`<name>@skills-dir`として自動ロードされる。`claude plugin init <name>`で雛形を作成できる。

| スキルディレクトリ      | スコープ     | 読み込まれるタイミング                                 |
| :---------------------- | :----------- | :----------------------------------------------------- |
| `~/.claude/skills/`     | 個人         | 全プロジェクトで（自分専用の場所のため）               |
| `<cwd>/.claude/skills/` | プロジェクト | そのフォルダのワークスペース信頼ダイアログを承認した後 |

プロジェクトスコープの`@skills-dir`プラグインはリポジトリルートまで遡って探索されない（サブディレクトリから起動すると見つからない）ため、リポジトリルートから起動するか`/reload-plugins`を使う。プロジェクトスコープではMCP/LSPサーバーの承認ゲートが通常より厳しく、バックグラウンドmonitorはそもそもロードされない。

`SKILL.md`の変更は即座に反映されるが、`hooks/`・`.mcp.json`・`agents/`等の変更は`/reload-plugins`または再起動が必要。停止は`claude plugin disable my-tool@skills-dir`（インストールしていないので`uninstall`は無い）。

## テスト・デバッグ

```shell
# ローカルディレクトリを一時的にロード（複数指定可、.zipアーカイブも可）
claude --plugin-dir ./my-plugin
claude --plugin-dir ./plugin-one --plugin-dir ./plugin-two

# 変更を再起動せずに反映
/reload-plugins

# マニフェスト・スキル・エージェント・フックの構文チェック
claude plugin validate ./my-plugin --strict

# 読み込み詳細を確認
claude --debug
```

`--plugin-dir`が既存のマーケットプレイスプラグインと同名の場合、そのセッションではローカル版が優先される（管理設定で強制有効/無効化されたプラグインを除く）。よくあるハマりどころ: コンポーネントを`.claude-plugin/`の中に置いてしまう、フックスクリプトに実行権限がない（`chmod +x`）、パスに`${CLAUDE_PLUGIN_ROOT}`を使っていない。

## マーケットプレイス

マーケットプレイスは他者が作ったプラグインのカタログ。「マーケットプレイスを追加」→「個別プラグインをインストール」の2段階。

```shell
# 追加
/plugin marketplace add anthropics/claude-code        # GitHub owner/repo
/plugin marketplace add https://gitlab.com/team/x.git # 任意のgitホスト
/plugin marketplace add ./my-marketplace               # ローカルパス
/plugin marketplace add https://example.com/marketplace.json # リモートURL

# インストール
/plugin install plugin-name@marketplace-name
claude plugin install plugin-name@marketplace-name --scope project

# 管理
/plugin list
/plugin disable plugin-name@marketplace-name
/plugin uninstall plugin-name@marketplace-name
/reload-plugins
```

公式マーケットプレイス`claude-plugins-official`は初回起動時に自動登録される（`github`, `pr-review-toolkit`, `security-guidance`, 各言語の`*-lsp`など）。コミュニティ審査を通過したものは`claude-plugins-community`（手動追加が必要）。

### マーケットプレイス自体を作る（`marketplace.json`）

リポジトリ直下に`.claude-plugin/marketplace.json`を置く。

```json
{
  "name": "company-tools",
  "owner": { "name": "DevTools Team", "email": "devtools@example.com" },
  "plugins": [
    {
      "name": "code-formatter",
      "source": "./plugins/formatter",
      "description": "Automatic code formatting on save",
      "version": "2.1.0"
    },
    {
      "name": "deployment-tools",
      "source": { "source": "github", "repo": "company/deploy-plugin" },
      "description": "Deployment automation tools"
    }
  ]
}
```

**プラグインソース（`source`）の種類**:

| 種類         | 形式                                                                           | 備考                                                                                    |
| :----------- | :----------------------------------------------------------------------------- | :-------------------------------------------------------------------------------------- |
| 相対パス     | `"./plugins/foo"`                                                              | マーケットプレイスリポジトリ内。マーケットプレイスルート基準、`..`不可                  |
| `github`     | `{"source":"github","repo":"owner/repo","ref?":"...","sha?":"..."}`            |                                                                                         |
| `url`        | `{"source":"url","url":"https://...","ref?":"...","sha?":"..."}`               | 任意のgitホスト                                                                         |
| `git-subdir` | `{"source":"git-subdir","url":"...","path":"tools/plugin"}`                    | モノレポのサブディレクトリをスパースクローン                                            |
| `npm`        | `{"source":"npm","package":"@acme/plugin","version?":"...","registry?":"..."}` | `npm install`で導入                                                                     |
| `archive`    | `{"source":"archive","url":"https://...","sha256?":"..."}`                     | HTTPS経由のzipファイルから導入。gitもnpmも不要。整合性検証用のSHA-256ハッシュ指定は任意 |

`ref`と`sha`を両方指定した場合は`sha`が優先される。ローカル相対パスはURL経由で追加されたマーケットプレイスでは解決できない（`marketplace.json`単体しかダウンロードされないため）ので、URL配布する場合は`github`/`npm`/gitURLソースを使う。

`strict`（デフォルト`true`）は「`plugin.json`が正」か「マーケットプレイスエントリが正」かを決める。`false`にすると、そのプラグインは自前の`plugin.json`を持たず、マーケットプレイスエントリだけで全コンポーネントを定義できる。

### チームへの自動導入

`.claude/settings.json`に`extraKnownMarketplaces`を書くと、リポジトリを信頼したメンバーに自動でマーケットプレイス追加・インストールが促される。

```json
{
  "extraKnownMarketplaces": {
    "my-team-tools": {
      "source": { "source": "github", "repo": "your-org/claude-plugins" }
    }
  },
  "enabledPlugins": { "code-formatter@company-tools": true }
}
```

管理者は`strictKnownMarketplaces`で追加可能なマーケットプレイスを許可リスト化できる。

## バージョン管理

バージョンは以下の優先順位で解決される（先に見つかったものを使用）:

1. `plugin.json`の`version`
2. マーケットプレイスエントリの`version`
3. gitコミットSHA（`github`/`url`/`git-subdir`/gitホスト内の相対パスソースのみ）
4. `unknown`（npmソースやgit管理外のローカルディレクトリ）

| 方式            | やり方                              | 更新の挙動                                                                 |
| :-------------- | :---------------------------------- | :------------------------------------------------------------------------- |
| 明示バージョン  | `plugin.json`に`"version": "2.1.0"` | このフィールドを上げたときだけ更新配信。コミットを積むだけでは何も起きない |
| コミットSHA方式 | `version`を省略                     | 新しいコミットのたびに更新扱い                                             |

`plugin.json`と`marketplace.json`の両方に`version`を書くと、常に`plugin.json`側が警告なしに優先される。

## 主なCLIコマンド

```shell
claude plugin init <name> [--with skills agents hooks mcp lsp output-style channel]
claude plugin install <plugin> [--scope user|project|local]
claude plugin uninstall <plugin> [--keep-data] [--prune]
claude plugin enable <plugin> / claude plugin disable <plugin>
claude plugin update <plugin>
claude plugin list [--json] [--available]
claude plugin details <plugin>     # コンポーネント一覧とトークンコスト見積り
claude plugin validate <path> [--strict]
claude plugin prune [--dry-run]    # 依存関係で自動導入されたが不要になったプラグインの削除

claude plugin marketplace add <source> [--scope user|project|local] [--sparse <paths...>]
claude plugin marketplace list [--json]
claude plugin marketplace remove <name> [--scope ...]
claude plugin marketplace update [name]
```

## 注意事項

- インストール済みプラグインは`~/.claude/plugins/cache`にコピーされて使われる。プラグインルート外（`../shared-utils`等）へのパス参照は動かない。同一マーケットプレイス内で共有したい場合はシンボリックリンクを使う
- プラグイン・マーケットプレイスは自分のユーザー権限で任意コードを実行できる強い信頼を要するコンポーネント。信頼できる提供元のものだけを追加・インストールする
- `CLAUDE.md`をプラグインルートに置いてもプロジェクトコンテキストとしては読み込まれない。指示をコンテキストに注入したいならスキルとして配布する

## 参考文献

- プラグインの作成方法全般（本記事の主な情報源）: https://code.claude.com/docs/en/plugins
- 技術リファレンス（スキーマ・CLIコマンド・全コンポーネント仕様）: https://code.claude.com/docs/en/plugins-reference
- プラグインの発見・インストール: https://code.claude.com/docs/en/discover-plugins
- マーケットプレイスの作成・配布: https://code.claude.com/docs/en/plugin-marketplaces
- 依存関係のバージョン制約: https://code.claude.com/docs/en/plugin-dependencies
