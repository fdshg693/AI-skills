---
# 詳細仕様は同階層の plugin-reference.md を必要時だけ読む。最終フォールバックは kilo-code-docs スキルで公式 kilo.ai/docs を確認する。
name: kilo-plugin-writer
description: Kilo Code（kilo.ai、CLI/TUI/VS Code拡張）用プラグイン（TypeScript/JavaScriptモジュール、`@kilocode/plugin`）を新規作成・編集するためのメタスキル。Use when designing or updating Kilo plugins, plugin manifests (package.json exports/`opencode` engine field), custom tools, hooks (tool/chat/provider/experimental), TUI plugins, workspace adaptors, or deciding whether an extension belongs in a Plugin vs a config/rule.
meta:
  tag: []
  requires_repo_tools: none
  requires_env: none
  dependencies: none
  requires_install: none
  requires_hooks: none
  requires_skills: kilo-code-docs
  status: experimental
  description: no description
  version: 1.0.0
---

# Kilo Plugin Writer

Kilo Code（CLI/TUI/VS Code拡張、内部的にOpenCodeベース）用プラグインを作る・直すときの実践ガイド。TypeScript/Node.jsの基本を理解している前提で、ここでは**落とし穴と判断基準**だけを優先する。

詳細仕様（hooks全種、モジュール形状、package.json manifest、配布経路、TUI plugin、troubleshooting）は必要になった時だけ [plugin-reference.md](plugin-reference.md) を読む。仕様変更が疑わしい場合の最終フォールバックは **kilo-code-docs スキル**で `automate/extending/plugins` を確認する。

## 対象と非対象

- **対象**: Kilo CLI / TUI / VS Code拡張に共通して読み込まれる Plugin（`@kilocode/plugin` の `Plugin` 型を実装し `{ id, server }` を default export する `.ts` / `.js` ファイル、または npm パッケージ）。
- **非対象**: 単なる設定（`kilo.json` の provider/model/permission 設定など)。コードで拡張する必要がなければ Plugin にしない。
- **非対象**: 一回限りの依頼、手順メモ、恒常的な手順知識。Kilo は Agent Skills仕様（`.kilo/skills/`、SKILL.md形式）を実装しており、手順・ドメイン知識はコード拡張が不要ならSkill（このリポジトリでは`.kilo/skills/`配下）またはこのリポジトリの`AGENTS.md`等の指示ファイルに書き、コードでの拡張が要るものだけをPluginにする。

## まず判断すること

1. **Plugin にすべきか**
   - モデルが呼べるカスタムツール、tool呼び出しの介入（引数書き換え・block）、chat/compaction/認証周りのフック、custom auth/model provider を**コードとして再配布したい**なら Plugin。
   - env変数の注入や通知設定だけなら、まず `tui.json`/`kilo.json` の設定項目（`attention` セクション等）で足りないか確認する。
2. **既存プラグインで足りるか**
   - `~/.config/kilo/plugin/`、`.kilo/plugin/`（legacy `.kilocode/plugin/`）、`kilo.json` の `plugin` 配列を確認する。
   - [`packages/plugin/src/example.ts`](https://github.com/Kilo-Org/kilocode/blob/main/packages/plugin/src/example.ts) や公式リポジトリの examples に近いものがないか探す。
   - 似たプラグインがあるなら新規より統合・拡張を優先する。
3. **単一ファイルかパッケージか**
   - Node builtins と `@kilocode/*` だけ使う → `.kilo/plugin/` 直下の単一ファイルで足りる（auto-discovery される）。
   - npm依存が必要、または配布・バージョン管理をしたい → `package.json` を持つパッケージにする。
4. **何を拡張するか**
   - モデルにアクションさせたい → **Custom tool**（`tool` hookまたは `tool/`フォルダの standalone tool file）
   - tool呼び出しの前後を書き換え/blockしたい → **`tool.execute.before` / `tool.execute.after` / `tool.definition`**
   - chatメッセージ・パラメータ・ヘッダを調整したい → **`chat.message` / `chat.params` / `chat.headers`**
   - 独自の認証フロー・モデルカタログを提供したい → **`auth` / `provider`**
   - shellコマンドに環境変数を注入したい → **`shell.env`**
   - TUI自体（slot/command/keybind）を拡張したい → **TUI plugin**（`@kilocode/plugin/tui`）

## 作成フロー

1. **モジュール形状を決める**（詳細は [plugin-reference.md#モジュール形状](plugin-reference.md#モジュール形状)）
   - `Plugin`型の関数を書き、`export default { id: "my-plugin", server: myPlugin }`。`id`はローカルファイルでは必須、npmパッケージでは`package.json#name`から推論される。
2. **`Plugin`本体を書く**
   - シグネチャ: `const myPlugin: Plugin = async ({ project, client, $, directory, worktree }) => ({ /* hooks */ })`
   - 必要なhookだけを返す。全hookはoptional。
   - 設定を受け取りたい場合、第2引数（configの`{ options }`タプル）を読む。
3. **配置場所を選ぶ**
   - 単一ファイル: `.kilo/plugin/*.ts`（project）または `~/.config/kilo/plugin/*.ts`（global）に置くだけでauto-discoveryされる。
   - config登録: `kilo.json`の`plugin`配列にローカルパス/npm指定を追加する。
   - npmパッケージ: `kilo plugin <package>`でインストール＋config自動追記。
4. **npm依存が要るなら`package.json`を用意する**
   - 単一ファイルパッケージなら `exports["./server"]`（と必要なら`exports["./tui"]`）または`main`。
   - `engines.opencode`でCLIバージョン範囲を宣言する。
5. **検証する**
   - `kilo --print-logs --log-level DEBUG`でロード失敗を確認。
   - 意図しない外部pluginの混入がないか`KILO_PURE=1`で切り分ける。

## 最小の単一ファイルプラグイン

```ts
// .kilo/plugin/hello.ts
import type { Plugin } from "@kilocode/plugin";

const hello: Plugin = async ({ project, client, $, directory, worktree }) => {
  return {
    "tool.execute.before": async (input, output) => {
      if (
        input.tool === "read" &&
        String(output.args.filePath).includes(".env")
      ) {
        throw new Error("reading .env files is blocked");
      }
    },
  };
};

export default { id: "hello", server: hello };
```

npm依存が必要になったら `.kilo/package.json` を追加してパッケージ化する。詳細は [plugin-reference.md](plugin-reference.md) の「パッケージ manifest」「依存関係」を参照。

## ベストプラクティス

- **hookはoptionalなので必要なものだけ返す**: `Hooks`オブジェクト全体を実装する必要はない。
- **カスタムツールは同名の組み込みツールに優先する**: `bash`等の名前を再利用すると意図的なoverrideになる。意図しない衝突を避けるため基本はユニーク名にする。
- **観測用hookはエラーを握る**: `tool.execute.before`でthrowするとtool失敗として扱われる。純観測（ログのみ）ならcatchする。
- **`console.log`ではなく`client.app.log()`を使う**: Kiloのログパイプラインに載る（`service`/`level`/`message`/`extra`）。
- **`@kilocode/*`はhost提供**: パッケージ化する場合`peerDependencies`（`optional: true`）に置き、`dependencies`には書かない。
- **experimental hookは変わりうる**: `experimental.`prefix付きhookはリリース間で変更されうる前提で使う。
- **パスはforward slash**: Windows環境でもドキュメント・manifest中のパスは原則`/`。

## よくある落とし穴

- 単一ファイルなのに`@kilocode/*`以外のnpmパッケージをimportし、インストール時に壊れる（要パッケージ化）。
- `package.json`の`exports`に`./server`/`./tui`を正しく宣言せず、意図した runtime でロードされない。
- `tool.execute.before`で純観測のつもりで投げたerrorがtool失敗として扱われてしまう。
- 独自ツール名が組み込みツール名と衝突し、意図せず組み込みツールをoverrideしてしまう。
- `KILO_PURE=1`環境でのCI/デバッグを想定せず、外部pluginへの依存が本番でだけ動く。
- Cline/Cursor等の他ツールのプラグイン形式（`AgentPlugin`等）と混同する。KiloのPlugin型・hook名は`@kilocode/plugin`固有。
- 仕様確認をせず記憶（学習データ）だけでhook名やmanifestフィールドを書き、実際のAPIとズレる。

## 出力時のチェックリスト

- [ ] 対象がKilo CLI/TUI/VS Code拡張向けPlugin（設定ファイルだけで足りる内容を混ぜていない）
- [ ] `export default { id, server }`の形でmodule descriptorを返している
- [ ] 単一ファイルかパッケージかが依存関係に合っている（`@kilocode/*`以外のimportがあればパッケージ化）
- [ ] 実装したhookが必要最小限で、観測用hookはエラーを握っている
- [ ] カスタムツール名が組み込みツールと意図せず衝突していない
- [ ] パッケージの場合、`package.json`の`exports`/`engines.opencode`が実装と一致している
- [ ] `@kilocode/*`はpeerDependencies（`optional: true`）に置かれている
- [ ] `kilo --print-logs --log-level DEBUG`でロードを確認済み（可能な場合）
- [ ] 仕様に不安がある場合のフォールバックとしてkilo-code-docsを案内している

## 困ったとき

1. 同階層の [plugin-reference.md](plugin-reference.md) を読む（hooks全種一覧、モジュール形状、manifest全フィールド、配布経路、TUI plugin、troubleshooting）。
2. Kilo Codeの公式仕様・hook名・manifestフィールドが変わっていそうなら、最終フォールバックとして **kilo-code-docs スキル**を使い、`automate/extending/plugins`（および必要なら`automate/extending/local-models`、`automate/extending/shell-integration`）を確認する。
