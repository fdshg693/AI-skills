---
# 詳細仕様は同階層の plugin-reference.md を必要時だけ読む。最終フォールバックは cline-docs スキルで公式 docs.cline.bot を確認する。
name: cline-plugin-writer
description: Cline 用プラグイン（AgentPlugin）を新規作成・編集するためのメタスキル。Use when designing or updating Cline plugins, plugin manifests (package.json cline field), custom tools, lifecycle hooks, slash commands, automation events, or deciding whether an extension belongs in a Plugin vs Skill/Rule. Covers SDK/CLI/Kanban plugins (not VSCode/JetBrains extension skills).
meta:
  tag: []
  requires_repo_tools: none
  requires_env: none
  dependencies: "@cline/sdk"
  requires_install: none
  requires_hooks: none
  requires_skills: cline-skill-writer, cline-rule-writer, cline-docs
  status: experimental
  description: no description
  version: 1.0.0
---

# Cline Plugin Writer

Cline 用プラグイン（`AgentPlugin`）を作る・直すときの実践ガイド。Cline は TypeScript/Node.js の基本と SDK の一般構造を理解している前提で、ここでは**落とし穴と判断基準**だけを優先する。

詳細仕様（マニフェスト全フィールド、hook stages 一覧、install コマンド、ディレクトリ構造、配布形式）は必要になった時だけ [plugin-reference.md](plugin-reference.md) を読む。仕様変更が疑わしい場合の最終フォールバックは **cline-docs スキル**で `customization/plugins` または `sdk/guides/writing-plugins` を確認する。

## 対象と非対象

- **対象**: Cline SDK / CLI / Kanban 向けのプラグイン（`AgentPlugin` を export する `.ts` / `.js` ファイル、または `package.json` を持つパッケージ）。
- **非対象**: VSCode / JetBrains 拡張の Skills（`.cline/skills/<skill-name>/SKILL.md`）。そちらは `cline-skill-writer` を使う。
- **非対象**: 永続的なコーディング規約。そちらは `cline-rule-writer` で `.clinerules/` に置く。

## まず判断すること

1. **Plugin にすべきか**
   - モデルが呼べるツール、slash command、lifecycle hook、automation event を**コードとして再配布したい**なら Plugin。
   - 単なる手順・判断プロセスなら Skill（`cline-skill-writer`）。Plugin パッケージに `skills/` を置く方式は公式ガイドに記載があるが、対象 Cline のバージョン・クライアント・ロード経路で各 Skill が一覧登録されることまで保証されたものとして扱わない。各 Skill を確実に使わせる必要がある場合は、通常の `.cline/skills/` または `~/.cline/skills/` にインストールして検証する。
   - 常に守る規約なら Rule（`cline-rule-writer`）。
   - 一回限りの依頼、設定メモ、巨大仕様書の丸写しは Plugin にしない。
2. **既存プラグインで足りるか**
   - `~/.cline/plugins/`、`.cline/plugins/`、`cline config` の plugins タブを確認する。
   - [SDK examples](https://github.com/cline/cline/tree/main/sdk/examples/plugins) に近いものがないか探す（`weather-metrics.ts` が最小の参考）。
   - 似たプラグインがあるなら新規より統合・拡張を優先する。
3. **単一ファイルかパッケージか**
   - Node builtins と `@cline/*` だけ使う → 単一 `.ts` / `.js` ファイルで配布できる。
   - `zod`・HTTP client など npm 依存が必要 → `package.json` を持つパッケージにする。
4. **何を拡張するか**
   - モデルにアクションさせたい → **Tool**（`api.registerTool`）
   - ユーザーが手動発火したい → **Command**（slash command）
   - 実行ログ・監査・ポリシー → **Hook**（`hooks.beforeTool` など）
   - 外部イベントで agent を動かす → **Event**
   - 複数をまとめて再配布 → **Plugin** で一括する

## 作成・編集フロー

1. **プラグインの形を決める**
   - 単一ファイル: `my-plugin.ts` が `AgentPlugin` を default export。
   - パッケージ: `package.json` の `cline.plugins` で entry paths を宣言。
2. **`AgentPlugin` 本体を書く**
   - 設定が要るなら **factory function**（`createMyPlugin(config)`）にする。不要なら object を直接 export。
   - `setup(api, ctx)` は**同期・高速**に保つ。最初の LLM call より前に走るため、async 初期化は setup を遅らせる。
   - **ツールは `setup()` 内で登録**する。lifecycle hook に入れない。
   - hook は観測（logging/metrics/audit）用に使い、agent の挙動変更には `beforeRun` / `beforeModel` で prompt/context を調整するにとどめる。
3. **マニフェストを整える**
   - 単一ファイル: 不要（ファイルがそのまま entry）。
   - パッケージ: `package.json` の `cline.plugins` に `paths` と `capabilities` を書く。`cline.plugins` が無い場合は auto-discovery が走る。
   - `@cline/*` 依存は host 提供なので `peerDependencies`（`optional: true`）に宣言する。
4. **配布形式を決める**
   - file URL / git / npm / local path のいずれかで `cline plugin install` できるようにする。
   - プロジェクトに閉じたい場合は `--cwd .` で `.cline/plugins/` に入れる。
5. **検証する**
   - `cline plugin install <source>` で入るか。
   - `cline config` の plugins タブに現れるか。
   - 単一ファイルの場合、npm 依存を import していないか（`@cline/*` と Node builtins 以外はパッケージ化必須）。
   - `setup()` が同期で完了するか。

## 最小の単一ファイルプラグイン

```typescript
// my-plugin.ts
import { type AgentPlugin, createTool } from "@cline/sdk";

const plugin: AgentPlugin = {
  name: "my-plugin",
  manifest: { capabilities: ["tools"] },
  setup(api) {
    api.registerTool(
      createTool({
        name: "hello",
        description: "Returns a greeting.",
        inputSchema: {
          type: "object",
          properties: { name: { type: "string" } },
        },
        execute: async (input) => ({
          message: `Hello, ${input.name ?? "world"}!`,
        }),
      }),
    );
  },
};

export default plugin;
```

インストール:

```bash
cline plugin install ./my-plugin.ts --cwd .
cline config   # plugins タブで確認
```

## パッケージプラグインの最小構成

```text
my-plugin/
├── package.json
└── index.ts
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

npm 依存が必要になったら単一ファイルからパッケージへ移行する。詳細は [plugin-reference.md](plugin-reference.md) の「配布形式」「host 提供依存」を参照。

## ベストプラクティス

- **`setup()` は同期・高速**: 最初の LLM call を遅らせない。重い初期化は遅延初期化か `beforeRun` に逃がす。
- **ツールは `setup()` で登録**: hook に入れない。最初の iteration 前に使えなければならない。
- **hook は観測用**: 挙動変更は `beforeRun` / `beforeModel` で prompt/context 調整にとどめる。
- **観測用 hook はエラーを握る**: `beforeTool` で投げた error は tool 失敗として扱われる。純観測なら catch する。
- **factory function で設定を注入**: `createMyPlugin({ token, owner })` の形にし、プラグインオブジェクト直接 export は設定不要な場合だけ。
- **`@cline/*` は peerDependencies（optional）**: host が提供するため `npm install` からは除外される。
- **単一ファイルは依存を絞る**: Node builtins と `@cline/*` 以外の import があるなら必ずパッケージ化する。
- **スキル同梱は自動登録と同一視しない**: 公式の Writing Plugins にはパッケージ直下の `skills/` 同梱が記載されているが、Plugin のインストール・ロードと Skill の一覧登録は別の機能である。対象環境で各 Skill が実際に表示・発火することを確認し、確実性が必要なら `.cline/skills/` または `~/.cline/skills/` へ通常の Skill として配布する。Skill のためだけに `list_*` / `read_*` のカスタムツールを追加しない。
- **パスは forward slash**: Windows 環境でもドキュメント・マニフェスト中のパスは原則 `/`。

## よくある落とし穴

- VSCode / JetBrains 拡張の Skills と SDK/CLI/Kanban の Plugins を混同する。前者は `cline-skill-writer`、後者がこのスキル。
- Plugin の `skills/` 同梱を、すべての Cline 環境での Skill 自動登録と断定する。Cline のバージョン・クライアント・ロード経路を確認し、必要なら標準の Skill 配置先へ別途インストールする。
- `setup()` で async 処理を待ってしまい、最初の LLM call が遅れる。
- ツールを hook 内で登録し、最初の iteration で使えない。
- 単一ファイルに npm 依存を import してしまい、インストール時に壊れる。
- `@cline/*` を `dependencies` に書いてしまい、host 提供の前提が崩れる（`peerDependencies` + `optional: true` が正しい）。
- 観測用 hook で throw し、tool が失敗扱いになる。
- `name` と manifest の `capabilities` が実装とズレていて、Cline が想定しない挙動になる。
- `cline.plugins` を書かずに entry が標準位置になく、auto-discovery に頼って意図しないファイルが読まれる。
- Skill にすべき手順を Plugin に押し込み、コードで判断させようとする。

## 出力時のチェックリスト

- [ ] 対象が SDK/CLI/Kanban 向けプラグイン（VSCode/JetBrains Skills ではない）
- [ ] 単一ファイルかパッケージかが依存関係に合っている
- [ ] `setup()` が同期で、ツールは `setup()` 内で登録されている
- [ ] hook は観測用で、純観測のものはエラーを握っている
- [ ] `package.json` の `cline.plugins` が entry を正しく宣言している（パッケージの場合）
- [ ] `@cline/*` は `peerDependencies`（`optional: true`）に置かれている
- [ ] `name` と `capabilities` が実装と一致している
- [ ] `cline plugin install` で入ることを確認済み（可能な場合）
- [ ] Skill / Rule にすべき内容を Plugin に混ぜていない（同梱 Skill を使う場合も、対象環境で一覧登録・発火を確認済み）
- [ ] 仕様に不安がある場合のフォールバックとして cline-docs を案内している

## 困ったとき

1. 同階層の [plugin-reference.md](plugin-reference.md) を読む（マニフェスト全フィールド、hook stages、install コマンド、ディレクトリ構造、配布形式、examples）。
2. Skill / Rule との切り分けで迷うなら `cline-skill-writer` / `cline-rule-writer` を使う。
3. Cline の公式仕様・マニフェスト・hook stages が変わっていそうなら、最終フォールバックとして **cline-docs スキル**を使い、`customization/plugins` または `sdk/guides/writing-plugins` を確認する。
