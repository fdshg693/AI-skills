# Plugin を新規作成する

## 目次

- [適用範囲](#適用範囲)
- [最小構成](#最小構成)
- [plugin.json](#pluginjson)
- [component を追加する](#component-を追加する)
- [ローカルで反復開発する](#ローカルで反復開発する)

## 適用範囲

GitHub Copilot CLI を基準に、Copilot cloud agent と VS Code でも使える agent plugin を作るときに読む。Plugin は複数の agent customization を一つの配布単位にまとめるもので、単一の指示だけなら custom instructions、単一の skill だけなら Agent Skill の方が適切な場合がある。

公式: [Creating a plugin for GitHub Copilot CLI](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/plugins-creating)、[About GitHub Copilot plugins](https://docs.github.com/en/copilot/concepts/agents/about-plugins)

## 最小構成

Plugin のルートに `plugin.json` を置く。component は必要なものだけ追加する。

```text
my-plugin/
├── plugin.json
├── agents/                 # 任意: *.agent.md
├── skills/                 # 任意: NAME/SKILL.md
├── commands/               # 任意: command directories
├── hooks.json              # 任意: hook configuration
├── .mcp.json               # 任意: MCP server configuration
└── lsp.json                # 任意: LSP server configuration
```

## plugin.json

必須なのは `name` だけ。`name` は小文字・数字・ハイフンのみ、最大 64 文字の kebab-case にする。説明は最大 1024 文字、`version` は semantic version にする。

```json
{
  "name": "my-dev-tools",
  "description": "Reusable development utilities for the team",
  "version": "1.0.0",
  "author": { "name": "Example Team" },
  "license": "MIT",
  "keywords": ["development"],
  "agents": "agents/",
  "skills": "skills/",
  "hooks": "hooks.json",
  "mcpServers": ".mcp.json",
  "lspServers": "lsp.json"
}
```

component path の項目は省略でき、既定値は `agents/` と `skills/`。複数の skill directory を使う場合は配列にする。`hooks`、`mcpServers`、`lspServers` はファイルパスまたは inline object を指定できる。全フィールドは [CLI plugin reference](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-plugin-reference#pluginjson) で確認する。

manifest を別の場所に置く形式もあるが、最初は Plugin ルートの `plugin.json` を使う。既存リポジトリへ埋め込む場合の `.plugin/plugin.json`、`.github/plugin/plugin.json`、`.claude-plugin/plugin.json` は host の検出順序を確認してから選ぶ。

## component を追加する

1. agent は `agents/NAME.agent.md` を作り、frontmatter の `name`、`description`、必要な tools と本文を定義する。
2. skill は `skills/NAME/SKILL.md` を作り、`name` と具体的な `description` を frontmatter に置く。詳細資料・script は skill directory 内に同梱する。
3. hook、MCP、LSP は [components.md](components.md) の該当節だけを読み、対象 host の設定形式を使う。
4. 各 component の名前・パスが manifest と一致することを確認する。Plugin で配布する skill は、利用時に必要な情報だけを読み込む構成にする。

## ローカルで反復開発する

作成直後にローカル install して検証する。

```powershell
copilot plugin install ./my-plugin
copilot plugin list
```

interactive session では `/plugin list`、`/agent`、`/skills list` を使って読み込みを確認する。ローカル Plugin の内容は cache されるため、ファイルを変更したら同じ install をもう一度実行してから新しい session で確認する。テスト終了後は manifest の `name` を指定して削除する。

```powershell
copilot plugin uninstall my-dev-tools
```

JSON の構文確認、各 component の実動作確認、秘密情報が source に含まれていないことの確認を行ってから marketplace へ登録する。
