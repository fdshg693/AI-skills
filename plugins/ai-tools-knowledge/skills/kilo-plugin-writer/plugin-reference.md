# Kilo Plugins Reference

> Source: kilo.ai公式docs（`kilo-code-docs`スキル経由で取得したスナップショット `output/llms.txt` の `## Source: /automate/extending/plugins` セクション）
>
> - <https://kilo.ai/docs/automate/extending/plugins>
> - 挙動はOpenCodeと同一: <https://opencode.ai/docs/plugins>, <https://opencode.ai/docs/custom-tools>

このファイルは、`kilo-plugin-writer/SKILL.md` 本体を短く保つための詳細リファレンス。Kilo用プラグインの仕様確認、hooks一覧の把握、manifest設計、配布経路の判断が必要な時だけ読む。

## 目次

- [概要](#概要)
- [プラグインでできること](#プラグインでできること)
- [プラグインを使う（読み込み経路）](#プラグインを使う読み込み経路)
- [読み込み順序](#読み込み順序)
- [外部プラグインの無効化](#外部プラグインの無効化)
- [プラグインを作る](#プラグインを作る)
- [モジュール形状](#モジュール形状)
- [npmプラグイン向けpackage manifest](#npmプラグイン向けpackage-manifest)
- [TypeScriptサポート](#typescriptサポート)
- [エンジン互換性](#エンジン互換性)
- [依存関係](#依存関係)
- [Hooksリファレンス](#hooksリファレンス)
- [Events](#events)
- [カスタムツール](#カスタムツール)
- [Examples](#examples)
- [TUIプラグイン](#tuiプラグイン)
- [Troubleshooting](#troubleshooting)
- [公式リファレンスリンク](#公式リファレンスリンク)
- [セルフレビュー](#セルフレビュー)
- [フォールバック](#フォールバック)

## 概要

KiloのPluginは、イベントへのhook・カスタムツール追加・認証/モデルプロバイダ登録・ランタイム挙動のカスタマイズを行うTypeScript/JavaScriptモジュール。Kilo CLIとVS Code拡張の両方で動作する。

## プラグインでできること

- **カスタムツール追加**: `read`/`write`/`bash`のような組み込みツールと並んでモデルが呼べるツールを追加する。
- **ツール呼び出しの介入**: 引数の書き換え、出力の書き換え、危険な操作のblock。
- **イベント購読**: session、message、permission、LSP diagnostics、file changesなど。
- **認証プロバイダ登録**: モデルプロバイダ向けのOAuthまたはAPIキーフロー。
- **モデルプロバイダ登録**: 動的なモデルカタログ。
- **chatパラメータ/ヘッダの変更**: LLMに送るリクエストを調整する。
- **compactionのカスタマイズ**: session圧縮時に使うpromptを注入または置き換える。
- **shell環境変数の注入**: agentまたはuserが実行するコマンドに対して。

## プラグインを使う（読み込み経路）

### config file

```json
{
  "$schema": "https://app.kilo.ai/config.json",
  "plugin": [
    "@your-org/your-plugin",
    "your-plugin@1.2.3",
    ["your-plugin", { "apiKey": "{env:MY_API_KEY}" }],
    "./plugins/local.ts",
    "file:///abs/path/plugin.ts"
  ]
}
```

| 形式                                   | 読み込み元                                                         |
| -------------------------------------- | ------------------------------------------------------------------ |
| `"package-name"`                       | npmの最新版                                                        |
| `"package-name@1.2.3"`                 | npmのpin版                                                         |
| `["package-name", { options }]`        | npmパッケージ＋関数に渡すoptions                                   |
| `"./path/plugin.ts"` / `"file:///..."` | ローカルファイル（config fileからの相対パスまたは絶対`file:` URL） |

config fileの置き場所はCLI設定と同じ（CLI configuration reference参照）。

### plugin directory

任意のconfigディレクトリ内の`plugin/`または`plugins/`フォルダにTS/JSファイルを置くと自動登録される（config記載不要）。

- Global: `~/.config/kilo/plugin/`
- Project: `.kilo/plugin/` または legacy `.kilocode/plugin/`

```text
my-project/
├── kilo.json
└── .kilo/
    └── plugin/
        ├── env-guard.ts
        └── notifications.ts
```

### `kilo plugin` コマンド

npmプラグインのインストール＋config書き換えを一度に行う。

```bash
kilo plugin my-plugin              # current projectのconfigへ
kilo plugin my-plugin --global     # globalへ
kilo plugin my-plugin --force      # 既存entryを置き換え
```

パッケージを解決し、`package.json`のplugin entrypointsを読んで適切なconfig file（local: `.kilo/opencode.jsonc` / `.kilo/tui.jsonc`、global: `~/.config/kilo/opencode.jsonc` / `~/.config/kilo/tui.jsonc`）にentryを書き込む（JSONCコメントは保持）。

### インストールの仕組み

- **npmプラグイン**はstartup時にBunで自動インストールされる。パッケージとその依存はCLIのXDGキャッシュディレクトリ配下の`packages/`にキャッシュされる（既定`~/.cache/opencode/packages/`、`$XDG_CACHE_HOME`設定時はその配下）。
- **pin指定**（`my-plugin@1.2.3`）はそのバージョンをインストールし、新版チェックをしない。bareなpackage名は`latest`に解決され、キャッシュが古いと更新されうる。
- **install scriptは無効**: npmプラグインの`install`/`postinstall`等のlifecycle scriptはblockされる。
- **ローカルプラグイン**はplugin directoryから直接ロードされる。外部パッケージをimportする場合はconfigディレクトリに`package.json`を追加する（[依存関係](#依存関係)参照）— KiloがstartupでBun installを走らせる。

## 読み込み順序

全sessionで以下の順にロードされる:

1. 内部組み込み（Kilo Gateway auth、Codex auth、Copilot auth、Cloudflare等）
2. Global config plugin配列（`~/.config/kilo/kilo.json`）
3. Global plugin directory（`~/.config/kilo/plugin/`）
4. Project config plugin配列（`kilo.json` / `opencode.json`）
5. Project plugin directory（`.kilo/plugin/`等）

同一package・同一versionの重複は除去される。複数プラグインのhookはロード順に逐次実行される。

## 外部プラグインの無効化

`KILO_PURE=1`環境変数を設定すると外部プラグインを全てskipし、組み込みプラグインのみロードされる。再現可能なCI runやデバッグに有用。

## プラグインを作る

プラグインは、[hooks](#hooksリファレンス)の集合を返す関数をexportするモジュール。

### 基本構造

```ts
// .kilo/plugin/hello.ts
import type { Plugin } from "@kilocode/plugin";

const hello: Plugin = async ({ project, client, $, directory, worktree }) => {
  console.log("hello plugin loaded");

  return {
    // hook implementations go here
  };
};

export default { id: "hello", server: hello };
```

プラグイン関数が受け取るcontextオブジェクト:

| Field                    | Description                                                 |
| ------------------------ | ----------------------------------------------------------- |
| `project`                | 現在のプロジェクトメタデータ                                |
| `directory`              | このsessionの現在の作業ディレクトリ                         |
| `worktree`               | このsessionのGit worktree root                              |
| `client`                 | ローカルサーバを呼ぶKilo SDKクライアント（`@kilocode/sdk`） |
| `$`                      | [Bun's shell API](https://bun.com/docs/runtime/shell)       |
| `serverUrl`              | ローカルKiloサーバのURL                                     |
| `experimental_workspace` | workspace adaptorの登録（Agent Managerが使用）              |

関数は`Hooks`オブジェクトを返す。第2引数はconfig経由で渡されたoptionsオブジェクト（例: `["my-plugin", { apiKey: "..." }]`の`{ apiKey: "..." }`）。

### workspace adaptorの登録

Kiloのworkspace作成フローに独自のworkspaceターゲットを追加できる。**experimental APIで将来変わりうる**。

```ts
import type { Plugin } from "@kilocode/plugin";
import { mkdir, rm } from "node:fs/promises";

const WorkspacePlugin: Plugin = async ({ experimental_workspace }) => {
  experimental_workspace.register("folder", {
    name: "Folder",
    description: "Create a blank folder",
    configure(config) {
      return { ...config, directory: `/tmp/kilo-${Date.now()}` };
    },
    async create(config) {
      await mkdir(config.directory!, { recursive: true });
    },
    async remove(config) {
      await rm(config.directory!, { recursive: true, force: true });
    },
    target(config) {
      return { type: "local", directory: config.directory! };
    },
  });

  return {};
};

export default { id: "workspace-folder", server: WorkspacePlugin };
```

adaptorは`configure(config)`、`create(config, env, from?)`、`remove(config)`、`target(config)`を実装する。`target`は`{ type: "local", directory }`（ローカル）または`{ type: "remote", url, headers? }`（リモート）を返す。

## モジュール形状

プラグインはmodule descriptorをdefault exportする必要がある。`id`はローカルファイルプラグインでは必須、npmプラグインでは`package.json#name`から推論される。

```ts
import type { Plugin } from "@kilocode/plugin";

const server: Plugin = async (ctx) => ({/* hooks */});

export default {
  id: "my-plugin",
  server,
};
```

npmプラグインは[TUI plugin](#tuiプラグイン)向けに`tui`エントリポイントも公開できるが、`server`と`tui`は別モジュールにする。

## npmプラグイン向けpackage manifest

公開するnpmプラグインは、対応するruntime毎に別のpackage entrypointを宣言する。Kiloは`package.json`からinstall targetを検出する:

- `exports["./server"]` → server pluginとしてマーク
- `exports["./tui"]` → TUI pluginとしてマーク
- `main` → `exports`未使用時のserver-only fallback
- `oc-themes` → `./tui` exportが無くてもTUI theme packageとしてマーク

```json
{
  "name": "@acme/kilo-plugin",
  "type": "module",
  "main": "./dist/server.js",
  "exports": {
    "./server": {
      "import": "./dist/server.js",
      "config": { "apiKey": "{env:ACME_API_KEY}" }
    },
    "./tui": {
      "import": "./dist/tui.js",
      "config": { "compact": true }
    }
  },
  "engines": {
    "opencode": "^1.0.0"
  }
}
```

exportの`config`オブジェクトはoptionalで、初回install時にuser configへ書き込まれるdefault optionsタプルになる。server/TUIコードは別ファイルに保ち、各runtimeは対応するentrypointだけをロードする。

theme専用パッケージはコードentrypointを省略し、package相対のtheme fileを提供できる:

```json
{
  "name": "@acme/kilo-themes",
  "oc-themes": ["themes/acme-dark.json", "themes/acme-light.json"]
}
```

`oc-themes`のentryはpackage内の相対パスに限る。絶対パス、`file://` URL、package外へ出るパスはrejectされる。installされたtheme packageは初回installとpackage更新時にthemeを同期する。

## TypeScriptサポート

```bash
bun add -d @kilocode/plugin
```

```ts
import type { Plugin } from "@kilocode/plugin";
import { tool } from "@kilocode/plugin/tool";
```

`plugin/`フォルダを含むconfigディレクトリには、Kiloが自動的に`package.json`を作成し`@kilocode/plugin`をインストールするので型解決は最初から効く。

## エンジン互換性

CLIバージョン範囲を宣言し、非互換buildでのロードを防ぐ:

```json
{
  "name": "my-plugin",
  "engines": { "opencode": "^7.0.0" }
}
```

実行中CLIがrangeを満たさない場合、プラグインはskipされwarningが出る。

## 依存関係

ローカルプラグインとカスタムツールは外部npmパッケージを使える。configディレクトリに`package.json`を追加する:

```json
// .kilo/package.json
{
  "dependencies": {
    "shescape": "^2.1.0"
  }
}
```

Kiloはstartupで`bun install`を実行するので、プラグインからimportできるようになる:

```ts
// .kilo/plugin/escape-bash.ts
import { escape } from "shescape";
import type { Plugin } from "@kilocode/plugin";

const EscapeBash: Plugin = async () => ({
  "tool.execute.before": async (input, output) => {
    if (input.tool === "bash") {
      output.args.command = escape(output.args.command);
    }
  },
});

export default { id: "escape-bash", server: EscapeBash };
```

## Hooksリファレンス

全hookはoptional。必要なものだけ返す。

### Lifecycle

| Hook     | Description                                                           |
| -------- | --------------------------------------------------------------------- |
| `config` | startup時にfully-resolved configを受け取る。read-only、inspection用。 |
| `event`  | 内部bus上の**全**eventで呼ばれる（[Events](#events)参照）。           |

### Tools

| Hook                  | Description                                                                            |
| --------------------- | -------------------------------------------------------------------------------------- |
| `tool`                | ツール名 → [ツール定義](#カスタムツール)のmap。追加したツールはモデルから呼べる。      |
| `tool.execute.before` | ツール実行前に発火。`output.args`を書き換えられる。                                    |
| `tool.execute.after`  | ツール実行後に発火。`output.title`/`output.output`/`output.metadata`を書き換えられる。 |
| `tool.definition`     | モデルに送る前に、ツールの`description`と`parameters`を書き換える。                    |

### Chat

| Hook                     | Description                                                                        |
| ------------------------ | ---------------------------------------------------------------------------------- |
| `chat.message`           | 新しいuser messageが届いたときに発火。`parts`を検査・変更できる。                  |
| `chat.params`            | `temperature`、`topP`、`topK`、`maxOutputTokens`、provider `options`を書き換える。 |
| `chat.headers`           | LLM API callへのHTTPヘッダを追加・置換する。                                       |
| `permission.ask`         | permissionプロンプトを自動allow/denyする。                                         |
| `command.execute.before` | slash command実行に介入し、結果`parts`を書き換える。                               |
| `shell.env`              | Kiloが実行する全shellコマンドに環境変数を注入する。                                |

### Providers & auth

| Hook       | Description                                                            |
| ---------- | ---------------------------------------------------------------------- |
| `auth`     | providerの認証方法（OAuthまたはAPIキー、対話的prompt付き）を登録する。 |
| `provider` | providerのモデルカタログを動的に供給する（BYOモデルgateway向け）。     |

`provider` hookはproviderの定義とauth contextを受け取り、model ID → model metadataのmapを返す:

```ts
import type { Plugin } from "@kilocode/plugin";

const ProviderPlugin: Plugin = async () => ({
  provider: {
    id: "my-gateway",
    async models(provider, { auth }) {
      const res = await fetch("https://gateway.example.com/models", {
        headers:
          auth?.type === "api" ? { Authorization: `Bearer ${auth.key}` } : {},
      });
      return await res.json();
    },
  },
});

export default { id: "my-provider", server: ProviderPlugin };
```

Kiloは返されたカタログからprovider/model IDを埋め、pickerとprovider routerで使う。

### Experimental

`experimental.`prefix付きhook。リリース間で変わりうる。

| Hook                                   | Description                                                                                           |
| -------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| `experimental.chat.messages.transform` | モデルに送る前にmessage履歴全体を書き換える。                                                         |
| `experimental.chat.system.transform`   | system prompt配列を変更する。                                                                         |
| `experimental.session.compacting`      | 追加context（`output.context`）を注入、またはcompaction promptを丸ごと置き換える（`output.prompt`）。 |
| `experimental.compaction.autocontinue` | compaction後に続く合成"continue"ターンを無効化する。                                                  |
| `experimental.text.complete`           | 最終text partを後処理する（例: 署名追加、secret redaction）。                                         |

## Events

`event` hookはKiloの内部bus上の全eventで発火する。代表的なevent type:

- **Session**: `session.created`, `session.updated`, `session.idle`, `session.error`, `session.deleted`, `session.compacted`, `session.diff`, `session.status`
- **Message**: `message.updated`, `message.removed`, `message.part.updated`, `message.part.removed`
- **Tool**: `tool.execute.before`, `tool.execute.after`
- **Permission**: `permission.asked`, `permission.replied`
- **File**: `file.edited`, `file.watcher.updated`
- **Shell**: `shell.env`
- **Command**: `command.executed`
- **LSP**: `lsp.updated`, `lsp.client.diagnostics`
- **Todo**: `todo.updated`
- **Server**: `server.connected`
- **Installation**: `installation.updated`

```ts
const server: Plugin = async () => ({
  event: async ({ event }) => {
    if (event.type === "session.idle") {
      // session finished responding
    }
  },
});
```

## カスタムツール

プラグインは組み込みツールと並んでモデルが呼べるツールを登録できる。型安全のため`tool()` helperを使う:

```ts
// .kilo/plugin/database.ts
import type { Plugin } from "@kilocode/plugin";
import { tool } from "@kilocode/plugin/tool";

const DatabasePlugin: Plugin = async () => ({
  tool: {
    query: tool({
      description: "Run a read-only SQL query against the project database",
      args: {
        sql: tool.schema.string().describe("SQL query to execute"),
      },
      async execute(args, context) {
        const { directory, worktree } = context;
        // your query logic here
        return `ran: ${args.sql}`;
      },
    }),
  },
});

export default { id: "database", server: DatabasePlugin };
```

`args`は`tool.schema`経由の[Zod](https://zod.dev)スキーマ。ツールの`execute`関数が受け取るのは:

- `args` — スキーマに対してvalidate済み
- `context` — `{ sessionID, messageID, agent, directory, worktree, abort, metadata, ask }`

### 名前の優先順位

カスタムツールが組み込みツールと同名の場合、**カスタムツールが勝つ**。組み込みを意図的にoverrideする場合（例: `bash`を追加validationでwrapする）以外は、ユニークな名前を選ぶ。

### 代替: standalone tool file

プラグイン全体のcontextが不要なツールは、任意のconfigディレクトリ内の`tool/`または`tools/`フォルダに置ける（例: `.kilo/tool/database.ts`、`~/.config/kilo/tool/database.ts`）。ファイル名がそのままツール名になり、各ファイルが直接`tool()`定義をexportする。レイアウトは[OpenCode custom tools guide](https://opencode.ai/docs/custom-tools)と同一で、`.opencode/`の代わりに`.kilo/`（legacy `.kilocode/`）を使う。

## Examples

### `.env`ファイルの読み取りをblockする

```ts
// .kilo/plugin/env-guard.ts
import type { Plugin } from "@kilocode/plugin";

const EnvGuard: Plugin = async () => ({
  "tool.execute.before": async (input, output) => {
    if (
      input.tool === "read" &&
      String(output.args.filePath).includes(".env")
    ) {
      throw new Error("reading .env files is blocked");
    }
  },
});

export default { id: "env-guard", server: EnvGuard };
```

### 全shellコマンドに環境変数を注入する

```ts
// .kilo/plugin/inject-env.ts
import type { Plugin } from "@kilocode/plugin";

const InjectEnv: Plugin = async () => ({
  "shell.env": async (input, output) => {
    output.env.MY_API_KEY = "secret";
    output.env.PROJECT_ROOT = input.cwd;
  },
});

export default { id: "inject-env", server: InjectEnv };
```

### 構造化ログ

`console.log`より`client.app.log()`を使うとKiloのログパイプラインに載る:

```ts
import type { Plugin } from "@kilocode/plugin";

const Logger: Plugin = async ({ client }) => {
  await client.app.log({
    body: {
      service: "my-plugin",
      level: "info",
      message: "plugin initialized",
      extra: { version: "1.0.0" },
    },
  });
  return {};
};

export default { id: "logger", server: Logger };
```

Levels: `debug`, `info`, `warn`, `error`。

### session compaction時にcontextを注入する

```ts
// .kilo/plugin/compaction.ts
import type { Plugin } from "@kilocode/plugin";

const Compaction: Plugin = async () => ({
  "experimental.session.compacting": async (input, output) => {
    output.context.push(
      "## Persist across compaction\n- current task status\n- files being actively edited\n- key decisions",
    );
  },
});

export default { id: "compaction", server: Compaction };
```

`output.prompt`を設定するとdefault compaction promptを丸ごと置き換える — 設定されている場合`output.context`は無視される。

### compaction後の自動continueを止める

Kiloはdefaultでcompaction後に合成"continue"ターンを送り、中断したタスクを再開させる。特定session/providerでこれを無効化するには`experimental.compaction.autocontinue`を使う:

```ts
const CompactionStop: Plugin = async () => ({
  "experimental.compaction.autocontinue": async (input, output) => {
    if (input.overflow) output.enabled = false;
  },
});
```

hookは`sessionID`、`agent`、`model`、`provider`、compact済み`message`、context overflowが原因かどうかを受け取る。`output.enabled`はdefault `true`。

## TUIプラグイン

プラグインはKilo TUI自体（slash command、route、slot、dialog、keybind）もターゲットにできる。TUIプラグインはpluginパッケージの`"./tui"`からexportされるSolidJSモジュール、またはtheme専用パッケージ（`oc-themes`宣言）。

TUIプラグインは別モジュール namespace（`@kilocode/plugin/tui`）にあり、独自API surface（`TuiPluginApi`）を持つ。TUI APIは大きく発展途上のため、このリファレンスでは網羅しない — `@kilocode/plugin/tui`の型を参照し、`packages/opencode/src/cli/cmd/tui/feature-plugins/`配下の組み込みTUIプラグインを動作例として見る。

代表的なTUI API:

- `api.command.register(...)`でcommand追加、`api.command.show()`でcommand palette表示。
- `api.ui.Slot`でhost slotまたはカスタムplugin slotを描画。
- `api.slots.register(...)`で他プラグイン向けの再利用可能なカスタムslotを定義。
- `api.ui.Prompt`でprompt置換slot内にprompt componentを描画。

host slotには`home_prompt_right`、`session_prompt`、`session_prompt_right`、`home_footer`がある。`session_prompt`はdefaultのsession promptを置き換え、`*_prompt_right`系はprompt metadata行の隣にcontrolを追加する。

## Troubleshooting

- **Plugin failed to load** — `kilo --print-logs --log-level DEBUG`でCLIログを確認する。load失敗はTUIやVS Code拡張のsession errorとしても表示される。
- **Plugin loaded but hooks never fire** — default exportに`server`が含まれているか確認する:

  ```ts
  export default { id: "my-plugin", server };
  ```

  named function exportも後方互換で受け付けられるがlegacy扱い。

- **Package installed but not active in one runtime** — packageが対応するentrypointを公開しているか確認する。server pluginには`exports["./server"]`または`main`、TUI pluginには`exports["./tui"]`または有効な`oc-themes`が必要。片方のruntimeにしか対応しないpackageは致命的load errorにはならずwarning付きでskipされる。

- **Local plugin can't find an npm import** — configディレクトリに`package.json`を追加し`bun install`に依存を拾わせる（[依存関係](#依存関係)参照）。
- **Plugin loads in dev but not in CI** — `KILO_PURE`が未設定であること、npm-installed pluginがCLIのXDGキャッシュディレクトリ配下の`packages/`にキャッシュされていること（既定`~/.cache/opencode/packages/`、`$XDG_CACHE_HOME`設定時はその配下）を確認する。`--log-level DEBUG`でinstall出力を見る。
- **Reset the plugin cache** — CLIの`packages/`キャッシュディレクトリ配下（またはconfigディレクトリ配下の`node_modules`キャッシュ）のplugin packageフォルダを削除しKiloを再起動する。

## 公式リファレンスリンク

- Types: [`@kilocode/plugin`](https://github.com/Kilo-Org/kilocode/tree/main/packages/plugin) — `Plugin`, `Hooks`, `PluginInput`, `ToolDefinition`, `AuthHook`, `ProviderHook`。
- Example plugin: [`packages/plugin/src/example.ts`](https://github.com/Kilo-Org/kilocode/blob/main/packages/plugin/src/example.ts)
- CLI command: [`kilo plugin`](https://kilo.ai/docs/code-with-ai/platforms/cli-reference#kilo-plugin)
- Upstream docs（挙動はOpenCodeと同一）: [opencode.ai/docs/plugins](https://opencode.ai/docs/plugins), [opencode.ai/docs/custom-tools](https://opencode.ai/docs/custom-tools)

## セルフレビュー

作成・更新後に確認する。

- [ ] 対象がKilo CLI/TUI/VS Code拡張向けPlugin
- [ ] `export default { id, server }`の形でmodule descriptorを返している
- [ ] 単一ファイルかパッケージかが依存関係に合っている
- [ ] 実装したhookが必要最小限で、観測用hookはエラーを握っている
- [ ] カスタムツール名が組み込みツールと意図せず衝突していない
- [ ] パッケージの場合、`package.json`の`exports`/`engines.opencode`が実装と一致している
- [ ] `@kilocode/*`はpeerDependencies（`optional: true`）に置かれている
- [ ] `kilo --print-logs --log-level DEBUG`でロードを確認済み（可能な場合）
- [ ] 公式仕様が曖昧な項目はkilo-code-docsで確認済み

## フォールバック

1. このリファレンスで解決する。
2. Kilo仕様の最新確認が必要なら`kilo-code-docs`スキルを使う。
   - 参照path: `automate/extending/plugins`（関連: `automate/extending/local-models`, `automate/extending/shell-integration`）
   - 公式URL: <https://kilo.ai/docs/automate/extending/plugins>
