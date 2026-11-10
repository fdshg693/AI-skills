# Cline Plugins Reference

> Source: Cline official docs extracted via `cline-docs`:
>
> - <https://docs.cline.bot/customization/plugins>
> - <https://docs.cline.bot/sdk/guides/writing-plugins>
> - <https://docs.cline.bot/sdk/plugins>
> - <https://docs.cline.bot/sdk/plugin-install>
> - <https://docs.cline.bot/sdk/plugin-examples>

このファイルは、`cline-plugin-writer/SKILL.md` 本体を短く保つための詳細リファレンス。Cline 用プラグインの仕様確認、マニフェスト設計、hook stages の把握、配布形式の判断、examples 参照が必要な時だけ読む。

## 目次

- [概要](#概要)
- [対象範囲](#対象範囲)
- [AgentPlugin 構造](#agentplugin-構造)
- [マニフェスト（package.json cline field）](#マニフェストpackagejson-cline-field)
- [配布形式](#配布形式)
- [配置場所とディレクトリ構造](#配置場所とディレクトリ構造)
- [install コマンド](#install-コマンド)
- [プログラムティックなロード](#プログラムティックなロード)
- [Hook stages](#hook-stages)
- [Hook policies](#hook-policies)
- [host 提供依存](#host-提供依存)
- [スキル同梱](#スキル同梱)
- [Plugin / Skill / Rule の切り分け](#plugin--skill--rule-の切り分け)
- [公式 examples](#公式-examples)
- [作成テンプレート](#作成テンプレート)
- [セルフレビュー](#セルフレビュー)
- [フォールバック](#フォールバック)

## 概要

Cline の Plugin は、`AgentPlugin` オブジェクトとして tools / hooks / commands / rules / events を1つにまとめた再配布可能なパッケージ。SDK / CLI / Kanban で使え、npm / git / file URL / local path で配布できる。

向いている用途:

- モデルが呼ぶカスタムツール（DB query, API call, domain action）
- lifecycle hook による監査・メトリクス・ポリシー
- slash command の手動発火
- 外部イベント（PR, Slack 等）での agent 起動
- 複数ツール・hooks のバンドル

向かない用途:

- VSCode / JetBrains 拡張の Skills（`.cline/skills/<skill-name>/SKILL.md`）
- 常時適用するコーディング規約（`.clinerules/`）
- 一回限りの依頼

## 対象範囲

公式 docs の明示:

> This feature currently only applies to Cline SDK, CLI, and Kanban. This feature is not applicable on VSCode and JetBrains Extension for now.

VSCode / JetBrains 拡張で Skills を作りたい場合は `cline-skill-writer` を使う。

## AgentPlugin 構造

```typescript
import { type AgentPlugin, createTool } from "@cline/sdk";

const myPlugin: AgentPlugin = {
  name: "my-plugin",
  manifest: { capabilities: ["tools", "hooks"] },
  setup(api, ctx) {
    api.registerTool(
      createTool({
        name: "my_action",
        description: "...",
        inputSchema: { type: "object", properties: {/* ... */} },
        execute: async (input) => ({/* ... */}),
      }),
    );
  },
  hooks: {
    beforeTool(context) {
      /* observe */
    },
    afterRun(context) {
      /* metrics */
    },
  },
};
```

- `name`: プラグイン識別子。
- `manifest.capabilities`: 宣言する拡張種別（`"tools"`, `"hooks"`, 等）。
- `setup(api, ctx)`: 同期・高速。最初の LLM call より前に走る。ツール登録はここで。
- `hooks`: lifecycle hook 群。`hooks` object の中に定義する（extension 直下ではない）。

### factory function パターン

設定が要る場合は factory にする:

```typescript
export function createMyPlugin(config: { token: string }): AgentPlugin {
  return {
    name: "my-plugin",
    manifest: {/* ... */},
    setup(api) {
      /* use config */
    },
  };
}
```

不要なら default export で直接 object を出す:

```typescript
const plugin: AgentPlugin = {/* ... */};
export default plugin;
```

## マニフェスト（package.json cline field）

パッケージプラグインは `package.json` の `cline` field で entry を宣言する。

```json
{
  "name": "my-cline-plugin",
  "version": "1.0.0",
  "cline": {
    "plugins": [{ "paths": ["./index.ts"], "capabilities": ["tools", "hooks"] }]
  }
}
```

`cline.plugins` 配列の要素は次のいずれか:

| 形式                                    | 例                                                            |
| --------------------------------------- | ------------------------------------------------------------- |
| `paths` と `capabilities` を持つ object | `{ "paths": ["./src/plugin.ts"], "capabilities": ["tools"] }` |
| plain string                            | `"./index.ts"`                                                |

各 path は `.ts` / `.js` ファイルを指し、`AgentPlugin` を default または named export する。

`cline.plugins` が無い場合は auto-discovery が走る: 標準 entry を探したあと、`node_modules` と `.git` を除いて `.ts` / `.js` を再帰的に走査する。

## 配布形式

| 形式       | コマンド例                                                                          | 備考                                                                                         |
| ---------- | ----------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| File URL   | `cline plugin install https://github.com/owner/repo/blob/main/plugins/my-plugin.ts` | GitHub `blob` と raw URL をサポート。`https://` 必須。単一 `.ts` / `.js` のみ。              |
| Git repo   | `cline plugin install https://github.com/owner/repo.git`                            | clone → prod deps install → entry 登録。`@ref` で branch/tag 指定可。                        |
| npm        | `cline plugin install npm:@scope/my-plugin` または `--npm my-plugin`                | npm registry から取得。                                                                      |
| Local path | `cline plugin install ./my-plugin`                                                  | 単一ファイル or `package.json` を持つディレクトリ。`.git` / `node_modules` は除外して copy。 |

追加 flags:

| Flag           | 説明                                                      |
| -------------- | --------------------------------------------------------- |
| `--force`      | 同一 source の既存 install を置き換える                   |
| `--json`       | 結果を JSON で出力（scripting 向け）                      |
| `--cwd <path>` | `<path>/.cline/plugins` に install する（project scoped） |

### 単一ファイル vs パッケージ

- **単一ファイル**: Node builtins と `@cline/*` だけ import できる。npm 依存が要った瞬点でパッケージ化が必須。
- **パッケージ**: `package.json` で `cline.plugins` を宣言し、runtime `dependencies` を書く。`@cline/*` は host 提供なので `peerDependencies`（`optional: true`）に置く。

## 配置場所とディレクトリ構造

```text
~/.cline/
  plugins/                     # Global plugins（全 session で利用可）
    _installed/                # `cline plugin install` が管理
      npm/                     # npm-sourced
      git/                     # git-sourced
      remote/                  # file URL-sourced
      local/                   # local-sourced

.cline/                        # Project root
  plugins/                     # Project-scoped plugins（その project でのみ有効）
```

- Global plugins は全 session で有効。
- Project plugins はその project でのみ有効。`--cwd .` で project scoped にする。
- CLI は `.cline/plugins/`（workspace）、`~/.cline/plugins/`、system plugins folder を auto-discovery する。

## install コマンド

```sh
cline plugin install <source> [options]
cline plugin i <source>        # shorthand
```

source 別:

```sh
# File URL
cline plugin install https://github.com/cline/cline/blob/main/sdk/examples/plugins/weather-metrics.ts

# npm
cline plugin install --npm @scope/plugin-name

# Git
cline plugin install --git https://github.com/owner/repo.git
cline plugin install --git github.com/owner/repo

# Local
cline plugin install ./path/to/plugin.ts
cline plugin install /absolute/path/to/dir
```

確認:

```sh
cline config   # plugins タブに現れる
```

## プログラムティックなロード

### `pluginPaths`（ClineCore）

```typescript
import { ClineCore } from "@cline/sdk";

const cline = await ClineCore.create({ clientName: "my-app" });

await cline.start({
  config: {
    systemPrompt: "...",
    pluginPaths: ["/absolute/path/to/plugin.ts"],
  },
});
```

- ファイルは `AgentPlugin` を default export する。
- package directory も渡せる（`package.json` の `cline.plugins` を読む）。

### `plugins`（Agent Runtime）

```typescript
import { Agent } from "@cline/sdk";
import { myPlugin } from "./my-plugin";

const agent = new Agent({
  providerId: "anthropic",
  modelId: "claude-sonnet-4-6",
  plugins: [myPlugin],
});
```

### `extensions`（ClineCore）

```typescript
await cline.start({
  config: {
    extensions: [myPlugin],
  },
});
```

## Hook stages

公式 docs に記載される stages:

```text
input
runtime_event
session_start
run_start
iteration_start
turn_start
before_agent_start
tool_call_before
tool_call_after
turn_end
stop_error
iteration_end
run_end
session_shutdown
error
```

よく使う stage:

| Stage                | 用途                                      |
| -------------------- | ----------------------------------------- |
| `before_agent_start` | context や prompt / messages の注入・変更 |
| `run_start`          | logging, timers, rate limits              |
| `tool_call_before`   | tool call の監査・block                   |
| `tool_call_after`    | 結果 log, 副作用 trigger                  |
| `run_end`            | metrics, notifications, cleanup           |
| `error`              | error reporting                           |

`beforeTool` / `afterTool` / `beforeRun` / `afterRun` / `beforeModel` / `afterModel` / `onEvent` が `hooks` object に生える（公式 `sdk/plugins` ページ）。

## Hook policies

| Field            | 意味                             |
| ---------------- | -------------------------------- |
| `mode`           | `"blocking"` or `"async"`        |
| `timeoutMs`      | hook timeout                     |
| `retries`        | retry count                      |
| `retryDelayMs`   | retry 間隔                       |
| `failureMode`    | `"fail_open"` or `"fail_closed"` |
| `maxConcurrency` | 同時 hook 実行数                 |
| `queueLimit`     | drop 前の queue size             |

ポリシー強制 hook では `fail_closed` を使う（bypass が安全でない場合）。

## host 提供依存

`@cline/` scope 下の依存は host runtime が提供する。installer は plugin の dependency list からこれらを strip してから `npm install` する。

host が提供する主な package:

- `@cline/sdk`
- `@cline/core`
- `@cline/agents`
- `@cline/llms`
- `@cline/shared`

正しい宣言:

```json
{
  "peerDependencies": { "@cline/sdk": "*" },
  "peerDependenciesMeta": { "@cline/sdk": { "optional": true } }
}
```

`dependencies` に書くと host 提供の前提が崩れるので避ける。

## スキル同梱

公式の Writing Plugins ガイドには、パッケージプラグインの `package.json` と同階層に `skills/` を置いて Skill を同梱する形式が記載されている:

```text
cline-github-plugin/
  package.json
  github-plugin.ts
  skills/
    triage/
      SKILL.md
```

各 Skill は通常の Cline Skill と同形式で、少なくとも次の条件を満たす必要がある。

- `skills/<skill-name>/SKILL.md` を持つ。
- `SKILL.md` の `name` がディレクトリ名と一致する。
- `description` が発火条件を具体的に記述している。

ただし、これは Plugin の配布形式であって、すべての Cline のバージョン・クライアント・ロード経路で各 Skill が一覧に登録されることを意味しない。公式の Skills は `.cline/skills/`（プロジェクト）または `~/.cline/skills/`（グローバル）が標準の探索先であり、各 Skill を確実に使わせる必要がある場合はこちらへ通常の Skill としてインストールし、Skills 一覧・自動発火・`/skill-name` による明示発火を対象環境で確認する。

Skill の同梱を理由に Plugin 側へ `list_skills` / `read_skill` のような検索ツールを追加しても、Cline の Skill 登録にはならない。Plugin に残すのは、Skill では代替できない実行時の Tool / Hook / Command だけにする。

## Plugin / Skill / Rule の切り分け

| 判断軸             | Plugin                                    | Skill                                  | Rule                       |
| ------------------ | ----------------------------------------- | -------------------------------------- | -------------------------- |
| 対象               | SDK / CLI / Kanban                        | 全般（VSCode/JetBrains 含む）          | 全般                       |
| 読まれるタイミング | install / load 後に有効                   | 関連タスク時、または明示呼び出し時だけ | 常時                       |
| 向く内容           | コード化されたツール・hook・command       | 手順・判断プロセス                     | 規約・禁止事項             |
| 形式               | `.ts` / `.js` / `package.json`            | `SKILL.md`                             | `.clinerules/*.md`         |
| 例                 | GitHub integration, LSP tools, web search | release notes 生成手順                 | TypeScript 必須、test 方針 |

迷った時:

- 「コードで再配布したいか？」→ Plugin
- 「手順・判断プロセスか？」→ Skill（`cline-skill-writer`）
- 「常時守る規約か？」→ Rule（`cline-rule-writer`）

## 公式 examples

[SDK repository](https://github.com/cline/cline/tree/main/sdk/examples/plugins) に install 可能な例がある。

| Example                                                                                                                        | 何を示すか                                                          |
| ------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------- |
| [`weather-metrics.ts`](https://github.com/cline/cline/blob/main/sdk/examples/plugins/weather-metrics.ts)                       | tool 登録 + lifecycle metrics hook。最小の参考。                    |
| [`mac-notify.ts`](https://github.com/cline/cline/blob/main/sdk/examples/plugins/mac-notify.ts)                                 | `afterRun` hook からの macOS Notification Center alert。            |
| [`custom-compaction.ts`](https://github.com/cline/cline/blob/main/sdk/examples/plugins/custom-compaction.ts)                   | `registerMessageBuilder` による provider message compaction。       |
| [`background-terminal.ts`](https://github.com/cline/cline/blob/main/sdk/examples/plugins/background-terminal.ts)               | detached shell job と `steer_message` による session 通知。         |
| [`automation-events.ts`](https://github.com/cline/cline/blob/main/sdk/examples/plugins/automation-events.ts)                   | plugin が発する automation event。                                  |
| [`gitignore-read-files-guard.ts`](https://github.com/cline/cline/blob/main/sdk/examples/plugins/gitignore-read-files-guard.ts) | `beforeTool` で workspace `.gitignore` 外の file access を block。  |
| [`web-search.ts`](https://github.com/cline/cline/blob/main/sdk/examples/plugins/web-search.ts)                                 | Exa API を使う `web_search` tool。                                  |
| [`typescript-lsp/`](https://github.com/cline/cline/tree/main/sdk/examples/plugins/typescript-lsp)                              | TypeScript Language Service を使う `goto_definition` tool。         |
| [`agents-squad/`](https://github.com/cline/cline/tree/main/sdk/examples/plugins/agents-squad)                                  | 独自 model と personality を持つ subagent による multi-agent team。 |

試す:

```sh
cline plugin install https://github.com/cline/cline/blob/main/sdk/examples/plugins/weather-metrics.ts --cwd .
cline -i "What's the weather like in Tokyo and Paris?"
```

## 作成テンプレート

### 単一ファイル

```typescript
// my-plugin.ts
import { type AgentPlugin, createTool } from "@cline/sdk";

const plugin: AgentPlugin = {
  name: "my-plugin",
  manifest: { capabilities: ["tools"] },
  setup(api) {
    api.registerTool(
      createTool({
        name: "my_action",
        description: "Does X for Y.",
        inputSchema: {
          type: "object",
          properties: { arg: { type: "string", description: "..." } },
          required: ["arg"],
        },
        execute: async (input) => ({ result: `done: ${input.arg}` }),
      }),
    );
  },
};

export default plugin;
```

### パッケージ

```text
my-plugin/
├── package.json
├── index.ts
└── skills/        # 任意。対象環境で Skill 登録を検証する
    └── my-skill/
        └── SKILL.md
```

```json
{
  "name": "my-cline-plugin",
  "version": "1.0.0",
  "cline": {
    "plugins": [{ "paths": ["./index.ts"], "capabilities": ["tools", "hooks"] }]
  },
  "dependencies": {},
  "peerDependencies": { "@cline/sdk": "*" },
  "peerDependenciesMeta": { "@cline/sdk": { "optional": true } }
}
```

## セルフレビュー

作成・更新後に確認する。

- [ ] 対象が SDK/CLI/Kanban 向けプラグイン（VSCode/JetBrains Skills ではない）
- [ ] 単一ファイルかパッケージかが依存関係に合っている
- [ ] `setup()` が同期で、ツールは `setup()` 内で登録されている
- [ ] hook は観測用で、純観測のものはエラーを握っている
- [ ] `package.json` の `cline.plugins` が entry を正しく宣言している（パッケージの場合）
- [ ] `@cline/*` は `peerDependencies`（`optional: true`）に置かれている
- [ ] `name` と `capabilities` が実装と一致している
- [ ] `cline plugin install` で入ることを確認済み（可能な場合）
- [ ] Skill / Rule にすべき内容を Plugin に混ぜていない
- [ ] 公式仕様が曖昧な項目は cline-docs で確認済み

## フォールバック

1. このリファレンスで解決する。
2. Skill / Rule との切り分けなら `cline-skill-writer` / `cline-rule-writer` を使う。
3. Cline 仕様の最新確認が必要なら `cline-docs` スキルを使う。
   - 参照 slug: `customization/plugins`, `sdk/guides/writing-plugins`, `sdk/plugins`, `sdk/plugin-install`, `sdk/plugin-examples`
   - 公式 URL:
     - <https://docs.cline.bot/customization/plugins>
     - <https://docs.cline.bot/sdk/guides/writing-plugins>
     - <https://docs.cline.bot/sdk/plugins>
     - <https://docs.cline.bot/sdk/plugin-install>
     - <https://docs.cline.bot/sdk/plugin-examples>
