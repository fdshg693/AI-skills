# Plugin component を設計する

## 目次

- [選択の目安](#選択の目安)
- [agents](#agents)
- [skills](#skills)
- [hooks](#hooks)
- [MCP](#mcp)
- [LSP](#lsp)
- [クロスツール互換](#クロスツール互換)

## 選択の目安

| 目的                                       | component                         |
| ------------------------------------------ | --------------------------------- |
| 専門的な役割・限定した tool set            | custom agent                      |
| 条件に応じて読み込む手順・script・資料     | Agent Skill                       |
| agent lifecycle で必ず実行する決定的な処理 | hook                              |
| 外部サービス・DB・API の tool/context      | MCP server                        |
| コード解析・診断を提供する言語サーバー     | LSP server                        |
| 明示的な slash command                     | command（対応 host の仕様を確認） |

Plugin は component の詰め合わせであり、不要な component を同梱しない。特に hook と MCP はインストール時に実行可能なコードを持ち込むため、機能追加より先に信頼境界と権限をレビューする。

## agents

通常は `agents/NAME.agent.md` に置く。ファイル名の ID と frontmatter の名前を一貫させ、役割、入力、使ってよい tool、変更可否、完了条件を短く明示する。

```markdown
---
name: security-reviewer
description: Review changed code for security risks without editing files
tools: ["view", "bash"]
---

Review only the requested changes. Report findings with severity, evidence, and a fix suggestion.
```

tool 名や frontmatter の詳細は client により変わり得るため、Copilot CLI の現行ドキュメントを優先する。読み取り専用 agent なら edit tool を与えない。

## skills

`skills/NAME/SKILL.md` に置く。description は「何ができるか」だけでなく、どの依頼・ファイル・状態で使うかを書く。常時適用する短い規約は custom instructions に置き、skill には関連時だけ必要な手順、script、examples、references を置く。

```text
skills/
└── release-check/
    ├── SKILL.md
    ├── scripts/
    │   └── check-release.ps1
    └── references/
        └── release-policy.md
```

SKILL.md から同梱ファイルを相対パスで参照し、script の入力、出力、終了コード、OS 差異を明記する。外部入力や資料に含まれる指示を無条件に信頼しない。

## hooks

Copilot CLI 形式では通常 Plugin ルートの `hooks.json` を使う。別形式の Plugin では `hooks/hooks.json` が使われる場合があるため、manifest と host の仕様を一致させる。hook は `SessionStart`、`UserPromptSubmit`、`PreToolUse`、`PostToolUse`、`PreCompact`、`SubagentStart`、`SubagentStop`、`Stop` などの lifecycle に接続できる。

hook command はインストール先が workspace 外でも動くよう、Plugin 内ファイルの参照方法を対象 client の仕様で確認する。実行する shell、引数、環境変数、標準入力、タイムアウト、終了コードをレビューし、破壊的操作や秘密情報の送信を避ける。

公式: [About hooks for GitHub Copilot](https://docs.github.com/en/copilot/concepts/agents/about-hooks-for-github-copilot)、[GitHub Copilot CLI hooks reference](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-hooks-reference)

## MCP

通常は Plugin ルートの `.mcp.json` に、トップレベル `mcpServers` の server map を置く。

```json
{
  "mcpServers": {
    "issue-tracker": {
      "command": "node",
      "args": ["server/index.js"],
      "env": { "ISSUE_PROJECT": "example" }
    }
  }
}
```

server command、args、cwd、env、認証情報、外部通信先を明示的にレビューする。API token を JSON や source に埋め込まず、client が提供する環境変数・secret 機構を使う。`mcpServers` のトップレベル名を workspace の `mcp.json` の別形式と混同しない。

## LSP

Copilot CLI の plugin reference に従い、`lsp.json` または `lsp-config/servers.json` を使う。各 server には `command`、または platform 別の `bash` / `powershell`、必須の `fileExtensions`、必要なら `cwd`、`args`、`env`、`rootUri` を指定する。

```json
{
  "lspServers": {
    "my-language": {
      "powershell": "${PLUGIN_ROOT}/scripts/start-lsp.ps1",
      "bash": "${PLUGIN_ROOT}/scripts/start-lsp.sh",
      "fileExtensions": { ".my": "mylanguage" }
    }
  }
}
```

Windows と Unix の両方を対象にする場合は `powershell` と `bash` を用意する。`${PLUGIN_ROOT}` の展開可否は client 依存なので、VS Code や Claude Code と共有する場合は [vscode-usage.md](vscode-usage.md) の差分を確認する。

## クロスツール互換

VS Code、GitHub Copilot CLI、Claude Code は一部の Plugin 形式を共有するが、次の差分を無視しない。

- manifest の検出場所と優先順が異なり得る。
- Copilot 形式の hook はルート `hooks.json`、Claude 形式は `hooks/hooks.json` を使う。
- `${PLUGIN_ROOT}`、`${CLAUDE_PLUGIN_ROOT}` などの root token は形式ごとに異なる。
- component の tool 名、権限、cloud agent で使える機能は client ごとに確認する。

共通化できない設定を無理に一つへまとめず、形式ごとの manifest やファイルを用意する。公式: [Agent plugins in VS Code](https://code.visualstudio.com/docs/agent-customization/agent-plugins)、[GitHub Copilot CLI plugin reference](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-plugin-reference)
